"""
Supervisor & Planning Layer
최상위 의사결정 및 작업 계획 수립
"""
from typing import Dict, List, Optional, Any
import asyncio
import uuid
from datetime import datetime
import re

from core.base import (
    Agent, Task, TaskType, TaskStatus, ExecutionPlan, AnalysisResult
)


class SupervisorAgent(Agent):
    """
    Supervisor Agent - 전체 시스템을 조율하는 최상위 에이전트
    자연어 명령을 해석하고 실행 계획을 수립
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("Supervisor", config)
        self.task_patterns = self._initialize_patterns()
        self.router = DynamicRouter(config)
    
    def _initialize_patterns(self) -> Dict[str, TaskType]:
        """작업 유형 판단을 위한 패턴 정의"""
        return {
            r'타이밍|timing|slack|setup|hold': TaskType.TIMING_ANALYSIS,
            r'전력|power|leakage|dynamic': TaskType.POWER_OPTIMIZATION,
            r'수정|fix|modify|change|edit': TaskType.RTL_MODIFICATION,
            r'스크립트|script|tcl|makefile': TaskType.SCRIPT_TUNING,
            r'검증|verify|lint|check': TaskType.VERIFICATION,
            r'디버그|debug|error|warning': TaskType.DEBUG,
        }
    
    async def parse_user_command(self, command: str) -> Task:
        """
        자연어 명령을 Task로 변환
        
        Args:
            command: 사용자 입력 ("DMA 모듈의 타이밍 위반 해결해줘")
        
        Returns:
            Task 객체
        """
        # 작업 유형 판단
        task_type = TaskType.VERIFICATION  # 기본값
        for pattern, ttype in self.task_patterns.items():
            if re.search(pattern, command, re.IGNORECASE):
                task_type = ttype
                break
        
        # 모듈/파일명 추출
        module_names = self._extract_module_names(command)
        
        # Task 생성
        task = Task(
            task_id=f"task_{uuid.uuid4().hex[:8]}",
            task_type=task_type,
            description=command,
            context={
                'raw_command': command,
                'target_modules': module_names,
                'language': 'ko' if self._is_korean(command) else 'en'
            }
        )
        
        self.log_action('parse_command', {
            'command': command,
            'task_type': task_type.value,
            'task_id': task.task_id
        })
        
        return task
    
    def _extract_module_names(self, text: str) -> List[str]:
        """텍스트에서 모듈명 추출"""
        # 대문자로 시작하는 단어나 snake_case 패턴 추출
        patterns = [
            r'\b[A-Z][a-zA-Z0-9_]*\b',  # CamelCase
            r'\b[a-z_][a-z0-9_]+_[a-z0-9_]+\b'  # snake_case
        ]
        modules = []
        for pattern in patterns:
            modules.extend(re.findall(pattern, text))
        return list(set(modules))
    
    def _is_korean(self, text: str) -> bool:
        """한글 포함 여부 확인"""
        return bool(re.search(r'[ㄱ-ㅎㅏ-ㅣ가-힣]', text))
    
    async def create_execution_plan(self, task: Task) -> ExecutionPlan:
        """
        Task를 세부 실행 계획으로 분해
        
        Args:
            task: 상위 수준 Task
        
        Returns:
            ExecutionPlan with sub-tasks and dependencies
        """
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        sub_tasks = []
        dependencies = {}
        
        # Task 타입별 계획 수립
        if task.task_type == TaskType.TIMING_ANALYSIS:
            sub_tasks, dependencies = await self._plan_timing_analysis(task)
        elif task.task_type == TaskType.RTL_MODIFICATION:
            sub_tasks, dependencies = await self._plan_rtl_modification(task)
        elif task.task_type == TaskType.SCRIPT_TUNING:
            sub_tasks, dependencies = await self._plan_script_tuning(task)
        elif task.task_type == TaskType.VERIFICATION:
            sub_tasks, dependencies = await self._plan_verification(task)
        elif task.task_type == TaskType.POWER_OPTIMIZATION:
            sub_tasks, dependencies = await self._plan_power_optimization(task)
        else:  # DEBUG
            sub_tasks, dependencies = await self._plan_debug(task)
        
        plan = ExecutionPlan(
            plan_id=plan_id,
            tasks=sub_tasks,
            dependencies=dependencies,
            metadata={
                'parent_task_id': task.task_id,
                'created_at': datetime.now().isoformat()
            }
        )
        
        self.log_action('create_plan', {
            'plan_id': plan_id,
            'num_tasks': len(sub_tasks),
            'task_type': task.task_type.value
        })
        
        return plan
    
    async def _plan_timing_analysis(self, task: Task) -> tuple:
        """타이밍 분석 계획 수립"""
        sub_tasks = []
        dependencies = {}
        
        # 1. KG에서 타겟 모듈의 컨텍스트 로드
        t1 = Task(
            task_id=f"{task.task_id}_kg_load",
            task_type=TaskType.VERIFICATION,
            description="Load module context from Knowledge Graph",
            context={'target_modules': task.context.get('target_modules', [])}
        )
        sub_tasks.append(t1)
        dependencies[t1.task_id] = []
        
        # 2. PrimeTime 스크립트 생성
        t2 = Task(
            task_id=f"{task.task_id}_gen_script",
            task_type=TaskType.SCRIPT_TUNING,
            description="Generate PrimeTime timing analysis script",
            context={'tool': 'PrimeTime'}
        )
        sub_tasks.append(t2)
        dependencies[t2.task_id] = [t1.task_id]
        
        # 3. 타이밍 분석 실행
        t3 = Task(
            task_id=f"{task.task_id}_run_sta",
            task_type=TaskType.TIMING_ANALYSIS,
            description="Run static timing analysis",
            context={'tool': 'PrimeTime'}
        )
        sub_tasks.append(t3)
        dependencies[t3.task_id] = [t2.task_id]
        
        # 4. 로그 분석 및 해결책 제안
        t4 = Task(
            task_id=f"{task.task_id}_analyze",
            task_type=TaskType.DEBUG,
            description="Analyze timing violations and suggest fixes",
            context={}
        )
        sub_tasks.append(t4)
        dependencies[t4.task_id] = [t3.task_id]
        
        return sub_tasks, dependencies
    
    async def _plan_rtl_modification(self, task: Task) -> tuple:
        """RTL 수정 계획 수립"""
        sub_tasks = []
        dependencies = {}
        
        # 1. RTL 코드 분석
        t1 = Task(
            task_id=f"{task.task_id}_analyze_rtl",
            task_type=TaskType.VERIFICATION,
            description="Analyze RTL code structure",
            context=task.context
        )
        sub_tasks.append(t1)
        dependencies[t1.task_id] = []
        
        # 2. 수정 사항 생성
        t2 = Task(
            task_id=f"{task.task_id}_gen_fix",
            task_type=TaskType.RTL_MODIFICATION,
            description="Generate RTL modifications",
            context=task.context
        )
        sub_tasks.append(t2)
        dependencies[t2.task_id] = [t1.task_id]
        
        # 3. Lint 검증
        t3 = Task(
            task_id=f"{task.task_id}_lint",
            task_type=TaskType.VERIFICATION,
            description="Run lint check on modified RTL",
            context={'tool': 'SpyGlass'}
        )
        sub_tasks.append(t3)
        dependencies[t3.task_id] = [t2.task_id]
        
        return sub_tasks, dependencies
    
    async def _plan_script_tuning(self, task: Task) -> tuple:
        """스크립트 튜닝 계획"""
        sub_tasks = []
        dependencies = {}
        
        t1 = Task(
            task_id=f"{task.task_id}_load_template",
            task_type=TaskType.VERIFICATION,
            description="Load script template",
            context=task.context
        )
        sub_tasks.append(t1)
        dependencies[t1.task_id] = []
        
        t2 = Task(
            task_id=f"{task.task_id}_optimize",
            task_type=TaskType.SCRIPT_TUNING,
            description="Optimize script parameters",
            context=task.context
        )
        sub_tasks.append(t2)
        dependencies[t2.task_id] = [t1.task_id]
        
        return sub_tasks, dependencies
    
    async def _plan_verification(self, task: Task) -> tuple:
        """검증 계획"""
        sub_tasks = []
        dependencies = {}
        
        t1 = Task(
            task_id=f"{task.task_id}_verify",
            task_type=TaskType.VERIFICATION,
            description="Run verification checks",
            context=task.context
        )
        sub_tasks.append(t1)
        dependencies[t1.task_id] = []
        
        return sub_tasks, dependencies
    
    async def _plan_power_optimization(self, task: Task) -> tuple:
        """전력 최적화 계획"""
        sub_tasks = []
        dependencies = {}
        
        # Similar structure to timing analysis
        t1 = Task(
            task_id=f"{task.task_id}_power_analysis",
            task_type=TaskType.POWER_OPTIMIZATION,
            description="Analyze power consumption",
            context=task.context
        )
        sub_tasks.append(t1)
        dependencies[t1.task_id] = []
        
        return sub_tasks, dependencies
    
    async def _plan_debug(self, task: Task) -> tuple:
        """디버그 계획"""
        sub_tasks = []
        dependencies = {}
        
        t1 = Task(
            task_id=f"{task.task_id}_identify_issue",
            task_type=TaskType.DEBUG,
            description="Identify root cause",
            context=task.context
        )
        sub_tasks.append(t1)
        dependencies[t1.task_id] = []
        
        t2 = Task(
            task_id=f"{task.task_id}_suggest_fix",
            task_type=TaskType.DEBUG,
            description="Suggest fixes",
            context=task.context
        )
        sub_tasks.append(t2)
        dependencies[t2.task_id] = [t1.task_id]
        
        return sub_tasks, dependencies
    
    async def process(self, task: Task) -> AnalysisResult:
        """Task 처리 - Supervisor는 직접 처리하지 않고 하위 에이전트에 위임"""
        plan = await self.create_execution_plan(task)
        
        # 라우터를 통해 하위 에이전트에 분배
        results = await self.router.execute_plan(plan)
        
        # 결과 종합
        success = all(r.success for r in results)
        summary = f"Completed {len(results)} sub-tasks"
        
        return AnalysisResult(
            success=success,
            summary=summary,
            details={
                'plan_id': plan.plan_id,
                'results': [r.__dict__ for r in results]
            }
        )


class DynamicRouter:
    """
    동적 라우터 - 작업 성격에 따라 적절한 에이전트로 라우팅
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.agent_registry: Dict[TaskType, Agent] = {}
    
    def register_agent(self, task_type: TaskType, agent: Agent):
        """에이전트 등록"""
        self.agent_registry[task_type] = agent
    
    async def route(self, task: Task) -> Agent:
        """Task를 적절한 에이전트로 라우팅"""
        agent = self.agent_registry.get(task.task_type)
        if not agent:
            raise ValueError(f"No agent registered for task type: {task.task_type}")
        return agent
    
    async def execute_plan(self, plan: ExecutionPlan) -> List[AnalysisResult]:
        """실행 계획을 순차적으로 실행"""
        completed = set()
        results = []
        
        while len(completed) < len(plan.tasks):
            # 실행 가능한 작업 찾기
            next_tasks = plan.get_next_tasks(completed)
            
            if not next_tasks:
                # 순환 의존성 또는 문제 발생
                break
            
            # 병렬 실행
            task_results = await asyncio.gather(
                *[self._execute_task(task) for task in next_tasks],
                return_exceptions=True
            )
            
            for task, result in zip(next_tasks, task_results):
                if isinstance(result, Exception):
                    result = AnalysisResult(
                        success=False,
                        summary=f"Task failed: {str(result)}",
                        details={'error': str(result)},
                        errors=[str(result)]
                    )
                
                results.append(result)
                completed.add(task.task_id)
                task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
        
        return results
    
    async def _execute_task(self, task: Task) -> AnalysisResult:
        """개별 작업 실행"""
        try:
            agent = await self.route(task)
            result = await agent.process(task)
            return result
        except Exception as e:
            return AnalysisResult(
                success=False,
                summary=f"Execution failed: {str(e)}",
                details={'exception': str(e)},
                errors=[str(e)]
            )
