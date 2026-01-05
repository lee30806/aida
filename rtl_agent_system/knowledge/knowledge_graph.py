"""
Knowledge Graph - RTL 설계 지식 관리
모듈 계층, 신호 연결, 의존성을 그래프로 관리
"""
from typing import Dict, List, Optional, Any, Set
import re
import json
from pathlib import Path
from dataclasses import dataclass

from core.base import Graph, GraphNode, GraphEdge


class DesignKnowledgeGraph:
    """
    Design Knowledge Graph - RTL 및 스크립트의 구조적 지식 관리
    """
    
    def __init__(self):
        self.graph = Graph()
        self.file_registry: Dict[str, str] = {}  # file_path -> node_id
        self.module_registry: Dict[str, str] = {}  # module_name -> node_id
    
    async def parse_rtl_file(self, file_path: str) -> List[GraphNode]:
        """
        RTL 파일을 파싱하여 Knowledge Graph에 추가
        
        Args:
            file_path: RTL 파일 경로 (Verilog/SystemVerilog)
        
        Returns:
            생성된 노드 리스트
        """
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        nodes = []
        
        # 모듈 추출
        modules = self._extract_modules(content)
        for module_info in modules:
            node = self._create_module_node(module_info, file_path)
            self.graph.add_node(node)
            nodes.append(node)
            self.module_registry[module_info['name']] = node.node_id
        
        # 모듈 인스턴스 추출 및 계층 관계 생성
        for module_info in modules:
            instances = self._extract_instances(module_info['body'])
            for inst in instances:
                # 인스턴스 노드 생성
                inst_node = self._create_instance_node(inst, module_info['name'])
                self.graph.add_node(inst_node)
                nodes.append(inst_node)
                
                # 계층 관계 엣지 생성
                parent_id = self.module_registry.get(module_info['name'])
                if parent_id:
                    edge = GraphEdge(
                        edge_id=f"hier_{parent_id}_{inst_node.node_id}",
                        source=parent_id,
                        target=inst_node.node_id,
                        edge_type="hierarchy",
                        attributes={'instance_name': inst['instance_name']}
                    )
                    self.graph.add_edge(edge)
        
        # 신호 및 포트 추출
        for module_info in modules:
            signals = self._extract_signals(module_info['body'])
            for signal in signals:
                sig_node = self._create_signal_node(signal, module_info['name'])
                self.graph.add_node(sig_node)
                nodes.append(sig_node)
                
                # 모듈-신호 연결
                module_id = self.module_registry.get(module_info['name'])
                if module_id:
                    edge = GraphEdge(
                        edge_id=f"sig_{module_id}_{sig_node.node_id}",
                        source=module_id,
                        target=sig_node.node_id,
                        edge_type="contains_signal",
                        attributes={}
                    )
                    self.graph.add_edge(edge)
        
        self.file_registry[file_path] = modules[0]['name'] if modules else ""
        
        return nodes
    
    def _extract_modules(self, content: str) -> List[Dict[str, Any]]:
        """모듈 정의 추출"""
        # module name (...); ... endmodule
        pattern = r'module\s+(\w+)\s*(?:#\s*\([^)]*\))?\s*\(([^;]*)\);(.*?)endmodule'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        modules = []
        for match in matches:
            module_name = match.group(1)
            ports = match.group(2)
            body = match.group(3)
            
            modules.append({
                'name': module_name,
                'ports': self._parse_ports(ports),
                'body': body
            })
        
        return modules
    
    def _parse_ports(self, ports_str: str) -> List[Dict[str, str]]:
        """포트 파싱"""
        ports = []
        # 간단한 포트 파싱 (input/output/inout signal_name)
        lines = ports_str.split(',')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # input/output/inout 찾기
            match = re.search(r'(input|output|inout)\s+(?:\[[\d:]+\])?\s*(\w+)', line)
            if match:
                direction = match.group(1)
                name = match.group(2)
                ports.append({'direction': direction, 'name': name})
        
        return ports
    
    def _extract_instances(self, body: str) -> List[Dict[str, str]]:
        """모듈 인스턴스 추출"""
        # module_type instance_name (...);
        pattern = r'(\w+)\s+(?:#\s*\([^)]*\))?\s*(\w+)\s*\('
        matches = re.finditer(pattern, body)
        
        instances = []
        for match in matches:
            module_type = match.group(1)
            instance_name = match.group(2)
            
            # 키워드 필터링
            if module_type in ['wire', 'reg', 'logic', 'input', 'output', 'inout', 
                              'assign', 'always', 'initial', 'generate']:
                continue
            
            instances.append({
                'module_type': module_type,
                'instance_name': instance_name
            })
        
        return instances
    
    def _extract_signals(self, body: str) -> List[Dict[str, str]]:
        """신호 선언 추출"""
        signals = []
        
        # wire, reg, logic 선언
        patterns = [
            r'(wire|reg|logic)\s+(?:\[[\d:]+\])?\s*(\w+)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, body)
            for match in matches:
                sig_type = match.group(1)
                sig_name = match.group(2)
                signals.append({
                    'type': sig_type,
                    'name': sig_name
                })
        
        return signals
    
    def _create_module_node(self, module_info: Dict, file_path: str) -> GraphNode:
        """모듈 노드 생성"""
        node_id = f"mod_{module_info['name']}"
        return GraphNode(
            node_id=node_id,
            node_type="module",
            name=module_info['name'],
            attributes={
                'file_path': file_path,
                'ports': module_info['ports']
            }
        )
    
    def _create_instance_node(self, inst_info: Dict, parent_module: str) -> GraphNode:
        """인스턴스 노드 생성"""
        node_id = f"inst_{parent_module}_{inst_info['instance_name']}"
        return GraphNode(
            node_id=node_id,
            node_type="instance",
            name=inst_info['instance_name'],
            attributes={
                'module_type': inst_info['module_type'],
                'parent_module': parent_module
            }
        )
    
    def _create_signal_node(self, signal_info: Dict, module_name: str) -> GraphNode:
        """신호 노드 생성"""
        node_id = f"sig_{module_name}_{signal_info['name']}"
        return GraphNode(
            node_id=node_id,
            node_type="signal",
            name=signal_info['name'],
            attributes={
                'signal_type': signal_info['type'],
                'module': module_name
            }
        )
    
    async def parse_tcl_script(self, file_path: str) -> List[GraphNode]:
        """
        TCL 스크립트를 파싱하여 설정 정보를 KG에 추가
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        nodes = []
        
        # 변수 추출
        var_pattern = r'set\s+(\w+)\s+(.+)'
        matches = re.finditer(var_pattern, content)
        
        for match in matches:
            var_name = match.group(1)
            var_value = match.group(2).strip()
            
            node = GraphNode(
                node_id=f"var_{var_name}",
                node_type="tcl_variable",
                name=var_name,
                attributes={
                    'value': var_value,
                    'file_path': file_path
                }
            )
            self.graph.add_node(node)
            nodes.append(node)
        
        return nodes
    
    def get_module_context(self, module_name: str, depth: int = 2) -> Graph:
        """
        특정 모듈의 컨텍스트 서브그래프 추출
        
        Args:
            module_name: 대상 모듈명
            depth: 탐색 깊이
        
        Returns:
            서브그래프
        """
        node_id = self.module_registry.get(module_name)
        if not node_id:
            return Graph()
        
        return self.graph.get_subgraph([node_id], depth)
    
    def find_modules_by_pattern(self, pattern: str) -> List[GraphNode]:
        """패턴으로 모듈 검색"""
        regex = re.compile(pattern, re.IGNORECASE)
        matching_modules = []
        
        for node in self.graph.nodes.values():
            if node.node_type == "module" and regex.search(node.name):
                matching_modules.append(node)
        
        return matching_modules
    
    def get_module_hierarchy(self, module_name: str) -> Dict[str, Any]:
        """모듈의 계층 구조 반환"""
        node_id = self.module_registry.get(module_name)
        if not node_id:
            return {}
        
        def build_hierarchy(nid: str) -> Dict[str, Any]:
            node = self.graph.nodes.get(nid)
            if not node:
                return {}
            
            children = []
            for edge in self.graph.edges.values():
                if edge.source == nid and edge.edge_type == "hierarchy":
                    child_node = self.graph.nodes.get(edge.target)
                    if child_node:
                        children.append({
                            'name': child_node.name,
                            'type': child_node.attributes.get('module_type', ''),
                            'children': build_hierarchy(edge.target)
                        })
            
            return {
                'name': node.name,
                'type': node.node_type,
                'children': children
            }
        
        return build_hierarchy(node_id)
    
    def analyze_dependencies(self) -> Dict[str, List[str]]:
        """모듈 간 의존성 분석"""
        dependencies = {}
        
        for node in self.graph.nodes.values():
            if node.node_type == "module":
                deps = set()
                
                # 인스턴스를 통한 의존성
                for edge in self.graph.edges.values():
                    if edge.source == node.node_id and edge.edge_type == "hierarchy":
                        inst_node = self.graph.nodes.get(edge.target)
                        if inst_node:
                            module_type = inst_node.attributes.get('module_type')
                            if module_type:
                                deps.add(module_type)
                
                dependencies[node.name] = list(deps)
        
        return dependencies
    
    def save(self, filepath: str):
        """KG를 파일로 저장"""
        data = {
            'graph': self.graph.to_dict(),
            'file_registry': self.file_registry,
            'module_registry': self.module_registry
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, filepath: str):
        """KG를 파일에서 로드"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # 그래프 복원
        graph_data = data['graph']
        for node_data in graph_data['nodes']:
            node = GraphNode(**node_data)
            self.graph.add_node(node)
        
        for edge_data in graph_data['edges']:
            edge = GraphEdge(**edge_data)
            self.graph.add_edge(edge)
        
        self.file_registry = data['file_registry']
        self.module_registry = data['module_registry']
