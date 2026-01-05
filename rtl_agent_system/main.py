"""
RTL Agent System - Main Integration
모든 컴포넌트를 통합하는 메인 시스템
"""
from typing import Dict, Optional, Any, List
from pathlib import Path
import asyncio
import json
from datetime import datetime

from core.base import Task, TaskType, ExecutionPlan, AnalysisResult
from agents.supervisor import SupervisorAgent, DynamicRouter
from knowledge.knowledge_graph import DesignKnowledgeGraph
from knowledge.rag_engine import RAGEngine, VectorStore
from execution.template_engine import TemplateEngine, create_default_templates
from execution.tool_executor import EDAToolExecutor, DryRunExecutor, ParallelExecutor
from analysis.log_analyzer import AnalysisAgent, FeedbackLoop, LogReducer


class RTLAgentSystem:
    """
    RTL Agent System - 통합 시스템
    """
    
    def __init__(self, 
                 workspace_dir: str,
                 config: Optional[Dict[str, Any]] = None):
        """
        Args:
            workspace_dir: 작업 디렉토리
            config: 시스템 설정
        """
        self.workspace = Path(workspace_dir)
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        self.config = config or {}
        
        # 디렉토리 구조 생성
        self.dirs = {
            'knowledge': self.workspace / 'knowledge',
            'templates': self.workspace / 'templates',
            'scripts': self.workspace / 'scripts',
            'reports': self.workspace / 'reports',
            'logs': self.workspace / 'logs'
        }
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 컴포넌트 초기화
        self._initialize_components()
        
        # 상태
        self.is_initialized = False
        self.execution_count = 0
    
    def _initialize_components(self):
        """컴포넌트 초기화"""
        
        # Knowledge Layer
        self.knowledge_graph = DesignKnowledgeGraph()
        self.rag_engine = RAGEngine(VectorStore())
        
        # Execution Layer
        self.template_engine = create_default_templates(str(self.dirs['templates']))
        
        # DryRun 모드 여부에 따라 실행기 선택
        if self.config.get('dry_run', False):
            self.tool_executor = DryRunExecutor()
        else:
            self.tool_executor = EDAToolExecutor(self.config.get('tool_config'))
        
        self.parallel_executor = ParallelExecutor(
            self.tool_executor,
            max_concurrent=self.config.get('max_concurrent', 4)
        )
        
        # Analysis Layer
        self.log_reducer = LogReducer()
        self.analysis_agent = AnalysisAgent({'workspace': str(self.workspace)})
        
        # Planning Layer
        self.supervisor = SupervisorAgent(self.config)
        self.router = DynamicRouter(self.config)
        
        # 에이전트 등록
        self._register_agents()
    
    def _register_agents(self):
        """에이전트 등록"""
        # 각 TaskType에 대한 기본 에이전트 등록
        # 실제로는 각 TaskType별로 전문화된 에이전트 필요
        for task_type in TaskType:
            self.router.register_agent(task_type, self.analysis_agent)
    
    async def initialize(self, rtl_dirs: List[str] = None):
        """
        시스템 초기화 - RTL 파일 인덱싱 등
        
        Args:
            rtl_dirs: RTL 디렉토리 리스트
        """
        print("Initializing RTL Agent System...")
        
        # RTL 파일 파싱 및 KG 구축
        if rtl_dirs:
            for rtl_dir in rtl_dirs:
                await self._index_rtl_directory(rtl_dir)
        
        # Knowledge Graph 저장
        kg_path = self.dirs['knowledge'] / 'design_kg.json'
        self.knowledge_graph.save(str(kg_path))
        print(f"Knowledge Graph saved to {kg_path}")
        
        self.is_initialized = True
        print("System initialized successfully!")
    
    async def _index_rtl_directory(self, directory: str):
        """RTL 디렉토리 인덱싱"""
        dir_path = Path(directory)
        if not dir_path.exists():
            print(f"Warning: Directory not found: {directory}")
            return
        
        # Verilog/SystemVerilog 파일 찾기
        rtl_files = list(dir_path.rglob('*.v')) + \
                   list(dir_path.rglob('*.sv')) + \
                   list(dir_path.rglob('*.vh'))
        
        print(f"Indexing {len(rtl_files)} RTL files from {directory}...")
        
        for rtl_file in rtl_files:
            try:
                await self.knowledge_graph.parse_rtl_file(str(rtl_file))
            except Exception as e:
                print(f"Error parsing {rtl_file}: {e}")
    
    async def execute_command(self, command: str) -> AnalysisResult:
        """
        자연어 명령 실행
        
        Args:
            command: 사용자 명령 (예: "DMA 모듈의 타이밍 위반 해결해줘")
        
        Returns:
            실행 결과
        """
        if not self.is_initialized:
            print("System not initialized. Call initialize() first.")
            return AnalysisResult(
                success=False,
                summary="System not initialized",
                details={},
                errors=["Call initialize() before executing commands"]
            )
        
        print(f"\n{'='*60}")
        print(f"Executing command: {command}")
        print(f"{'='*60}\n")
        
        # 1. 명령 파싱
        task = await self.supervisor.parse_user_command(command)
        print(f"Task created: {task.task_id} ({task.task_type.value})")
        
        # 2. 실행 계획 수립
        plan = await self.supervisor.create_execution_plan(task)
        print(f"Execution plan created: {len(plan.tasks)} sub-tasks")
        
        # 3. 계획 실행
        results = await self.router.execute_plan(plan)
        
        # 4. 결과 종합
        success = all(r.success for r in results)
        
        final_result = AnalysisResult(
            success=success,
            summary=f"Executed {len(results)} tasks",
            details={
                'task_id': task.task_id,
                'plan_id': plan.plan_id,
                'results': [r.__dict__ for r in results]
            },
            errors=[e for r in results for e in r.errors],
            warnings=[w for r in results for w in r.warnings],
            recommendations=[rec for r in results for rec in r.recommendations]
        )
        
        self.execution_count += 1
        
        # 결과 저장
        await self._save_execution_result(task.task_id, final_result)
        
        return final_result
    
    async def _save_execution_result(self, task_id: str, result: AnalysisResult):
        """실행 결과 저장"""
        result_path = self.dirs['reports'] / f"{task_id}_result.json"
        
        with open(result_path, 'w') as f:
            json.dump({
                'task_id': task_id,
                'timestamp': datetime.now().isoformat(),
                'result': result.__dict__
            }, f, indent=2)
    
    async def analyze_timing(self, 
                            module_name: str,
                            netlist_path: str,
                            sdc_path: str) -> AnalysisResult:
        """
        타이밍 분석 실행
        
        Args:
            module_name: 대상 모듈명
            netlist_path: 넷리스트 경로
            sdc_path: SDC 제약 조건 경로
        
        Returns:
            분석 결과
        """
        print(f"Analyzing timing for module: {module_name}")
        
        # 1. Knowledge Graph에서 모듈 컨텍스트 추출
        context_graph = self.knowledge_graph.get_module_context(module_name)
        print(f"Loaded context: {len(context_graph.nodes)} nodes")
        
        # 2. PrimeTime 스크립트 생성
        script_context = {
            'target_module': module_name,
            'search_path': str(Path(netlist_path).parent),
            'link_library': ['* slow.db'],
            'target_library': 'slow.db',
            'netlist_path': netlist_path,
            'sdc_path': sdc_path,
            'analysis_mode': 'setup',
            'max_paths': 100,
            'nworst': 10,
            'output_dir': str(self.dirs['reports'])
        }
        
        script_path = self.dirs['scripts'] / f'{module_name}_timing.tcl'
        self.template_engine.render(
            'primetime_sta',
            script_context,
            str(script_path)
        )
        print(f"Generated script: {script_path}")
        
        # 3. 실행
        exec_result = await self.tool_executor.execute(
            'primetime',
            str(script_path),
            {'working_dir': str(self.workspace)}
        )
        
        if not exec_result['success']:
            return AnalysisResult(
                success=False,
                summary="Timing analysis failed",
                details=exec_result,
                errors=[exec_result.get('error', 'Unknown error')]
            )
        
        # 4. 결과 분석
        timing_report = self.dirs['reports'] / 'timing_setup.rpt'
        if timing_report.exists():
            violations = await self.log_reducer.parse_timing_report(str(timing_report))
            
            return AnalysisResult(
                success=len(violations) == 0,
                summary=f"Found {len(violations)} timing violations",
                details={
                    'violations': [v.to_dict() for v in violations],
                    'report_path': str(timing_report)
                }
            )
        
        return AnalysisResult(
            success=True,
            summary="Timing analysis completed (no violations)",
            details={'report_path': str(timing_report)}
        )
    
    async def run_with_feedback(self, 
                               task: Task,
                               max_iterations: int = 3) -> AnalysisResult:
        """
        피드백 루프를 사용한 자동 수정
        
        Args:
            task: 작업
            max_iterations: 최대 반복 횟수
        
        Returns:
            최종 결과
        """
        feedback_loop = FeedbackLoop(max_iterations)
        
        async def fix_callback(recommendations: List[str]) -> Task:
            """수정 콜백"""
            # 추천사항을 바탕으로 새로운 작업 생성
            # 실제로는 LLM을 사용하여 RTL 코드 수정 등 수행
            print(f"Applying fixes based on recommendations:")
            for rec in recommendations:
                print(f"  - {rec}")
            
            # 수정된 작업 반환 (간단한 구현)
            new_task = Task(
                task_id=f"{task.task_id}_fixed",
                task_type=task.task_type,
                description=f"Fixed: {task.description}",
                context=task.context
            )
            return new_task
        
        result = await feedback_loop.run(task, self.analysis_agent, fix_callback)
        
        # 이력 저장
        history_path = self.dirs['reports'] / f'{task.task_id}_feedback_history.json'
        with open(history_path, 'w') as f:
            json.dump(feedback_loop.get_history(), f, indent=2)
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """시스템 통계 반환"""
        return {
            'workspace': str(self.workspace),
            'initialized': self.is_initialized,
            'execution_count': self.execution_count,
            'knowledge_graph': {
                'nodes': len(self.knowledge_graph.graph.nodes),
                'edges': len(self.knowledge_graph.graph.edges),
                'modules': len(self.knowledge_graph.module_registry)
            },
            'rag_engine': {
                'documents': len(self.rag_engine.vector_store.documents)
            }
        }
    
    def save_state(self):
        """시스템 상태 저장"""
        # Knowledge Graph
        kg_path = self.dirs['knowledge'] / 'design_kg.json'
        self.knowledge_graph.save(str(kg_path))
        
        # RAG Engine
        rag_path = self.dirs['knowledge'] / 'rag_store.pkl'
        self.rag_engine.save(str(rag_path))
        
        # 통계
        stats_path = self.workspace / 'system_stats.json'
        with open(stats_path, 'w') as f:
            json.dump(self.get_statistics(), f, indent=2)
        
        print(f"System state saved to {self.workspace}")
    
    def load_state(self):
        """시스템 상태 로드"""
        # Knowledge Graph
        kg_path = self.dirs['knowledge'] / 'design_kg.json'
        if kg_path.exists():
            self.knowledge_graph.load(str(kg_path))
        
        # RAG Engine
        rag_path = self.dirs['knowledge'] / 'rag_store.pkl'
        if rag_path.exists():
            self.rag_engine.load(str(rag_path))
        
        self.is_initialized = True
        print(f"System state loaded from {self.workspace}")
