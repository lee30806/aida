"""
RAG Engine - Retrieval Augmented Generation
EDA 툴 매뉴얼, 과거 프로젝트 지식 검색
"""
from typing import List, Dict, Optional, Any, Tuple
import numpy as np
from pathlib import Path
import json
import pickle
from dataclasses import dataclass
from datetime import datetime
import hashlib

from core.base import KnowledgeStore


@dataclass
class Document:
    """문서 데이터 구조"""
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'doc_id': self.doc_id,
            'content': self.content,
            'metadata': self.metadata,
            'embedding': self.embedding.tolist() if self.embedding is not None else None
        }


class VectorStore(KnowledgeStore):
    """
    벡터 저장소 - 임베딩 기반 검색
    실제 환경에서는 Chroma, Pinecone, Weaviate 등 사용 가능
    """
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.documents: Dict[str, Document] = {}
        self.embeddings: Optional[np.ndarray] = None
        self.doc_ids: List[str] = []
    
    async def store(self, key: str, value: Any, metadata: Optional[Dict] = None):
        """문서 저장"""
        if isinstance(value, str):
            # 텍스트를 Document로 변환
            doc = Document(
                doc_id=key,
                content=value,
                metadata=metadata or {},
                embedding=self._compute_embedding(value)
            )
        elif isinstance(value, Document):
            doc = value
            if doc.embedding is None:
                doc.embedding = self._compute_embedding(doc.content)
        else:
            raise ValueError("Value must be string or Document")
        
        self.documents[key] = doc
        self._rebuild_index()
    
    async def retrieve(self, key: str) -> Optional[Document]:
        """문서 검색"""
        return self.documents.get(key)
    
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """유사도 기반 검색"""
        if not self.documents:
            return []
        
        query_embedding = self._compute_embedding(query)
        similarities = self._compute_similarities(query_embedding)
        
        # Top-K 인덱스
        top_indices = np.argsort(similarities)[::-1][:limit]
        
        results = []
        for idx in top_indices:
            if idx >= len(self.doc_ids):
                continue
            doc_id = self.doc_ids[idx]
            doc = self.documents[doc_id]
            results.append({
                'doc_id': doc_id,
                'content': doc.content,
                'metadata': doc.metadata,
                'score': float(similarities[idx])
            })
        
        return results
    
    async def delete(self, key: str):
        """문서 삭제"""
        if key in self.documents:
            del self.documents[key]
            self._rebuild_index()
    
    def _compute_embedding(self, text: str) -> np.ndarray:
        """
        텍스트 임베딩 생성 (간단한 구현)
        실제로는 sentence-transformers, OpenAI embeddings 등 사용
        """
        # 간단한 TF-IDF 스타일 임베딩 (데모용)
        # 실제 환경에서는 SentenceTransformer 또는 다른 모델 사용
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        np.random.seed(hash_val % (2**32))
        embedding = np.random.randn(self.dimension)
        # 정규화
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        return embedding
    
    def _rebuild_index(self):
        """인덱스 재구축"""
        if not self.documents:
            self.embeddings = None
            self.doc_ids = []
            return
        
        self.doc_ids = list(self.documents.keys())
        embeddings_list = []
        
        for doc_id in self.doc_ids:
            doc = self.documents[doc_id]
            if doc.embedding is None:
                doc.embedding = self._compute_embedding(doc.content)
            embeddings_list.append(doc.embedding)
        
        self.embeddings = np.vstack(embeddings_list)
    
    def _compute_similarities(self, query_embedding: np.ndarray) -> np.ndarray:
        """코사인 유사도 계산"""
        if self.embeddings is None:
            return np.array([])
        
        # 코사인 유사도
        similarities = np.dot(self.embeddings, query_embedding)
        return similarities
    
    def save(self, filepath: str):
        """저장소 저장"""
        data = {
            'dimension': self.dimension,
            'documents': {k: v.to_dict() for k, v in self.documents.items()},
            'doc_ids': self.doc_ids
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
    
    def load(self, filepath: str):
        """저장소 로드"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        self.dimension = data['dimension']
        self.doc_ids = data['doc_ids']
        
        # Document 복원
        for doc_id, doc_data in data['documents'].items():
            embedding = np.array(doc_data['embedding']) if doc_data['embedding'] else None
            doc = Document(
                doc_id=doc_data['doc_id'],
                content=doc_data['content'],
                metadata=doc_data['metadata'],
                embedding=embedding
            )
            self.documents[doc_id] = doc
        
        self._rebuild_index()


class RAGEngine:
    """
    RAG Engine - 지식 검색 및 컨텍스트 생성
    """
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        self.vector_store = vector_store or VectorStore()
        self.doc_cache: Dict[str, Document] = {}
    
    async def index_directory(self, directory: str, file_patterns: List[str] = None):
        """
        디렉토리의 문서들을 인덱싱
        
        Args:
            directory: 대상 디렉토리
            file_patterns: 파일 패턴 리스트 (예: ['*.md', '*.txt'])
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            raise ValueError(f"Directory not found: {directory}")
        
        patterns = file_patterns or ['*.md', '*.txt', '*.rst']
        
        for pattern in patterns:
            for file_path in dir_path.rglob(pattern):
                await self.index_file(str(file_path))
    
    async def index_file(self, filepath: str):
        """
        파일을 청크로 나누어 인덱싱
        """
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 청크로 분할
        chunks = self._chunk_text(content)
        
        for i, chunk in enumerate(chunks):
            doc_id = f"{filepath}:chunk_{i}"
            metadata = {
                'source_file': filepath,
                'chunk_index': i,
                'total_chunks': len(chunks),
                'indexed_at': datetime.now().isoformat()
            }
            
            await self.vector_store.store(doc_id, chunk, metadata)
    
    def _chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        """
        텍스트를 청크로 분할
        
        Args:
            text: 원본 텍스트
            chunk_size: 청크 크기 (문자 수)
            overlap: 청크 간 중첩 크기
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        
        return chunks
    
    async def search_knowledge(self, 
                               query: str, 
                               limit: int = 5,
                               filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        지식 검색
        
        Args:
            query: 검색 쿼리
            limit: 결과 개수
            filters: 메타데이터 필터
        
        Returns:
            검색 결과 리스트
        """
        results = await self.vector_store.search(query, limit=limit * 2)  # 필터링 고려
        
        # 필터 적용
        if filters:
            filtered_results = []
            for result in results:
                metadata = result['metadata']
                match = all(
                    metadata.get(k) == v for k, v in filters.items()
                )
                if match:
                    filtered_results.append(result)
            results = filtered_results[:limit]
        else:
            results = results[:limit]
        
        return results
    
    async def get_context_for_query(self, query: str, max_tokens: int = 2000) -> str:
        """
        쿼리에 대한 컨텍스트 생성
        
        Args:
            query: 사용자 쿼리
            max_tokens: 최대 토큰 수 (대략 문자 수 / 4)
        
        Returns:
            컨텍스트 텍스트
        """
        results = await self.search_knowledge(query, limit=10)
        
        context_parts = []
        current_length = 0
        max_chars = max_tokens * 4  # 대략적인 변환
        
        for result in results:
            content = result['content']
            source = result['metadata'].get('source_file', 'unknown')
            
            part = f"[Source: {source}]\n{content}\n"
            part_length = len(part)
            
            if current_length + part_length > max_chars:
                break
            
            context_parts.append(part)
            current_length += part_length
        
        return "\n---\n".join(context_parts)
    
    async def index_eda_manual(self, tool_name: str, manual_path: str):
        """
        EDA 툴 매뉴얼 인덱싱
        
        Args:
            tool_name: 툴 이름 (PrimeTime, SpyGlass 등)
            manual_path: 매뉴얼 파일 경로
        """
        with open(manual_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 섹션별로 분할 (예: 챕터, 옵션 설명 등)
        sections = self._split_manual_sections(content)
        
        for i, section in enumerate(sections):
            doc_id = f"{tool_name}:manual:section_{i}"
            metadata = {
                'tool': tool_name,
                'document_type': 'manual',
                'section_index': i,
                'indexed_at': datetime.now().isoformat()
            }
            
            await self.vector_store.store(doc_id, section, metadata)
    
    def _split_manual_sections(self, content: str) -> List[str]:
        """매뉴얼을 섹션으로 분할"""
        # 간단한 구현: 빈 줄 기준으로 분할
        sections = content.split('\n\n')
        # 너무 작은 섹션은 병합
        merged = []
        current = ""
        
        for section in sections:
            if len(current) + len(section) < 1000:
                current += section + "\n\n"
            else:
                if current:
                    merged.append(current.strip())
                current = section + "\n\n"
        
        if current:
            merged.append(current.strip())
        
        return merged
    
    async def search_error_solutions(self, error_message: str) -> List[Dict[str, Any]]:
        """
        에러 메시지에 대한 해결책 검색
        
        Args:
            error_message: 에러 메시지
        
        Returns:
            과거 해결 사례 리스트
        """
        # 에러 메시지에서 핵심 키워드 추출
        keywords = self._extract_error_keywords(error_message)
        query = " ".join(keywords)
        
        results = await self.search_knowledge(
            query,
            limit=5,
            filters={'document_type': 'lesson_learned'}
        )
        
        return results
    
    def _extract_error_keywords(self, error_message: str) -> List[str]:
        """에러 메시지에서 키워드 추출"""
        # 간단한 구현
        # 실제로는 NLP 기법 사용
        keywords = []
        
        # Error/Warning 코드 추출
        import re
        codes = re.findall(r'[A-Z]+-\d+', error_message)
        keywords.extend(codes)
        
        # 중요 단어 추출 (대문자 시작 단어)
        words = re.findall(r'\b[A-Z][a-z]+\b', error_message)
        keywords.extend(words[:5])
        
        return keywords
    
    async def add_lesson_learned(self, 
                                 problem: str, 
                                 solution: str, 
                                 metadata: Optional[Dict] = None):
        """
        과거 해결 사례 추가
        
        Args:
            problem: 문제 설명
            solution: 해결 방법
            metadata: 추가 메타데이터
        """
        doc_id = f"lesson_{datetime.now().timestamp()}"
        content = f"Problem: {problem}\n\nSolution: {solution}"
        
        meta = metadata or {}
        meta.update({
            'document_type': 'lesson_learned',
            'added_at': datetime.now().isoformat()
        })
        
        await self.vector_store.store(doc_id, content, meta)
    
    def save(self, filepath: str):
        """RAG Engine 저장"""
        self.vector_store.save(filepath)
    
    def load(self, filepath: str):
        """RAG Engine 로드"""
        self.vector_store.load(filepath)
