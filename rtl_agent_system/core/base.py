"""
RTL Agent System - Base Classes and Interfaces
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime


class TaskType(Enum):
    """작업 유형 정의"""
    RTL_MODIFICATION = "rtl_modification"
    SCRIPT_TUNING = "script_tuning"
    VERIFICATION = "verification"
    TIMING_ANALYSIS = "timing_analysis"
    POWER_OPTIMIZATION = "power_optimization"
    DEBUG = "debug"


class TaskStatus(Enum):
    """작업 상태"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


@dataclass
class Task:
    """작업 데이터 구조"""
    task_id: str
    task_type: TaskType
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 5
    context: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    sub_tasks: List['Task'] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'task_id': self.task_id,
            'task_type': self.task_type.value,
            'description': self.description,
            'status': self.status.value,
            'priority': self.priority,
            'context': self.context,
            'results': self.results,
            'sub_tasks': [st.to_dict() for st in self.sub_tasks],
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class ExecutionPlan:
    """실행 계획"""
    plan_id: str
    tasks: List[Task]
    dependencies: Dict[str, List[str]]  # task_id -> [dependent_task_ids]
    estimated_duration: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_next_tasks(self, completed_task_ids: set) -> List[Task]:
        """다음 실행 가능한 작업들 반환"""
        next_tasks = []
        for task in self.tasks:
            if task.task_id in completed_task_ids:
                continue
            deps = self.dependencies.get(task.task_id, [])
            if all(dep in completed_task_ids for dep in deps):
                next_tasks.append(task)
        return next_tasks


@dataclass
class AnalysisResult:
    """분석 결과"""
    success: bool
    summary: str
    details: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class Agent(ABC):
    """에이전트 기본 클래스"""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.history: List[Dict[str, Any]] = []
    
    @abstractmethod
    async def process(self, task: Task) -> AnalysisResult:
        """작업 처리"""
        pass
    
    def log_action(self, action: str, details: Dict[str, Any]):
        """액션 로깅"""
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details
        })


class KnowledgeStore(ABC):
    """지식 저장소 인터페이스"""
    
    @abstractmethod
    async def store(self, key: str, value: Any, metadata: Optional[Dict] = None):
        """데이터 저장"""
        pass
    
    @abstractmethod
    async def retrieve(self, key: str) -> Optional[Any]:
        """데이터 검색"""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """유사도 검색"""
        pass
    
    @abstractmethod
    async def delete(self, key: str):
        """데이터 삭제"""
        pass


class ToolExecutor(ABC):
    """툴 실행기 인터페이스"""
    
    @abstractmethod
    async def execute(self, 
                     tool_name: str, 
                     script_path: str, 
                     args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """툴 실행"""
        pass
    
    @abstractmethod
    async def validate_output(self, output_path: str) -> AnalysisResult:
        """출력 검증"""
        pass


@dataclass
class GraphNode:
    """그래프 노드"""
    node_id: str
    node_type: str  # module, signal, instance, etc.
    name: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'node_id': self.node_id,
            'node_type': self.node_type,
            'name': self.name,
            'attributes': self.attributes
        }


@dataclass
class GraphEdge:
    """그래프 엣지"""
    edge_id: str
    source: str  # node_id
    target: str  # node_id
    edge_type: str  # connection, hierarchy, dependency, etc.
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'edge_id': self.edge_id,
            'source': self.source,
            'target': self.target,
            'edge_type': self.edge_type,
            'attributes': self.attributes
        }


class Graph:
    """그래프 데이터 구조"""
    
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        self.adjacency: Dict[str, List[str]] = {}  # node_id -> [connected_node_ids]
    
    def add_node(self, node: GraphNode):
        """노드 추가"""
        self.nodes[node.node_id] = node
        if node.node_id not in self.adjacency:
            self.adjacency[node.node_id] = []
    
    def add_edge(self, edge: GraphEdge):
        """엣지 추가"""
        self.edges[edge.edge_id] = edge
        if edge.source not in self.adjacency:
            self.adjacency[edge.source] = []
        if edge.target not in self.adjacency:
            self.adjacency[edge.target] = []
        self.adjacency[edge.source].append(edge.target)
    
    def get_neighbors(self, node_id: str) -> List[GraphNode]:
        """이웃 노드 반환"""
        neighbor_ids = self.adjacency.get(node_id, [])
        return [self.nodes[nid] for nid in neighbor_ids if nid in self.nodes]
    
    def get_subgraph(self, node_ids: List[str], depth: int = 1) -> 'Graph':
        """서브그래프 추출"""
        subgraph = Graph()
        visited = set()
        
        def traverse(nid: str, current_depth: int):
            if current_depth > depth or nid in visited or nid not in self.nodes:
                return
            visited.add(nid)
            subgraph.add_node(self.nodes[nid])
            
            for neighbor_id in self.adjacency.get(nid, []):
                # 엣지 찾기
                for edge in self.edges.values():
                    if edge.source == nid and edge.target == neighbor_id:
                        subgraph.add_edge(edge)
                traverse(neighbor_id, current_depth + 1)
        
        for node_id in node_ids:
            traverse(node_id, 0)
        
        return subgraph
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'edges': [edge.to_dict() for edge in self.edges.values()]
        }
    
    def save_json(self, filepath: str):
        """JSON으로 저장"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
