# 자율형 RTL 분석 및 최적화 에이전트 시스템

## 개요

대규모 반도체 설계(SoC/IP) 프로젝트의 RTL 코드, EDA 스크립트, 대용량 로그 데이터를 통합 분석하고 제어하는 Neuro-symbolic Agent 시스템입니다.

### 핵심 기능

- **Deep Context Understanding**: Knowledge Graph 기반 RTL 코드 구조 및 의존성 파악
- **Tool Orchestration**: Synopsys, Cadence 등 상용 EDA 툴의 정교한 제어
- **Self-Correction**: 로그 분석을 통한 자동 에러 수정 및 최적화 반복 수행

## 아키텍처

시스템은 4개의 계층으로 구성됩니다:

### 1. Supervisor & Planning Layer (두뇌 계층)
- **SupervisorAgent**: 자연어 명령 해석 및 작업 계획 수립
- **DynamicRouter**: 작업 성격에 따른 동적 에이전트 라우팅

### 2. Knowledge & Context Layer (기억 계층)
- **Design Knowledge Graph**: RTL/스크립트의 AST 분석 및 그래프 저장
- **RAG Engine**: EDA 매뉴얼, 과거 해결 사례 검색

### 3. Execution & Infrastructure Layer (실행 계층)
- **Template Engine**: Jinja2 기반 EDA 스크립트 생성
- **Tool Executor**: 실제 EDA 툴 실행 관리

### 4. Analysis & Feedback Layer (분석 계층)
- **Log Reducer**: 대용량 로그 요약 및 핵심 정보 추출
- **Analysis Agent**: 근본 원인 분석 및 해결책 제안

## 설치

```bash
# 저장소 클론
git clone <repository-url>
cd rtl_agent_system

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

## 디렉토리 구조

```
rtl_agent_system/
├── core/
│   └── base.py              # 기본 클래스 및 인터페이스
├── agents/
│   └── supervisor.py        # Supervisor 및 Router
├── knowledge/
│   ├── knowledge_graph.py   # Knowledge Graph 시스템
│   └── rag_engine.py        # RAG Engine
├── execution/
│   ├── template_engine.py   # 템플릿 엔진
│   └── tool_executor.py     # 툴 실행기
├── analysis/
│   └── log_analyzer.py      # 로그 분석
├── main.py                  # 메인 시스템 클래스
├── examples.py              # 사용 예제
├── requirements.txt         # 의존성
└── README.md               # 문서
```

## 빠른 시작

### 1. 기본 사용법

```python
import asyncio
from main import RTLAgentSystem

async def main():
    # 시스템 초기화
    system = RTLAgentSystem(
        workspace_dir='./workspace',
        config={
            'dry_run': True,  # 테스트 모드
            'max_concurrent': 4
        }
    )
    
    # RTL 파일 인덱싱
    await system.initialize(rtl_dirs=['./rtl_design'])
    
    # 자연어 명령 실행
    result = await system.execute_command(
        "DMA 모듈의 타이밍 위반을 분석해줘"
    )
    
    print(f"Result: {result.success}")
    print(f"Summary: {result.summary}")

if __name__ == '__main__':
    asyncio.run(main())
```

### 2. 타이밍 분석

```python
result = await system.analyze_timing(
    module_name='dma_controller',
    netlist_path='./netlist/dma_controller_synth.v',
    sdc_path='./constraints/dma_controller.sdc'
)

if not result.success:
    print(f"Violations found: {len(result.details['violations'])}")
```

### 3. Knowledge Graph 사용

```python
from knowledge.knowledge_graph import DesignKnowledgeGraph

kg = DesignKnowledgeGraph()

# RTL 파일 파싱
await kg.parse_rtl_file('./rtl/top.v')

# 모듈 계층 구조 확인
hierarchy = kg.get_module_hierarchy('top')

# 의존성 분석
dependencies = kg.analyze_dependencies()
```

## 예제 실행

```bash
# 모든 예제 실행
python examples.py

# 또는 개별 예제 실행
python -c "import asyncio; from examples import example_basic_usage; asyncio.run(example_basic_usage())"
```

## 지원하는 EDA 툴

- **Synopsys**: PrimeTime, Design Compiler, Fusion Compiler
- **Cadence**: Genus, Innovus, Tempus
- **Siemens**: Questa, ModelSim
- **기타**: SpyGlass, Formality 등

## 설정

### Tool Configuration

`config` 딕셔너리로 툴 경로 설정:

```python
config = {
    'tool_paths': {
        'primetime': '/tools/synopsys/pt/bin/pt_shell',
        'spyglass': '/tools/atrenta/spyglass/bin/spyglass',
        'dc_shell': '/tools/synopsys/dc/bin/dc_shell'
    },
    'max_concurrent': 4,
    'dry_run': False
}

system = RTLAgentSystem('./workspace', config)
```

### Template Customization

커스텀 템플릿 추가:

```python
from execution.template_engine import TemplateEngine

engine = TemplateEngine('./templates')

custom_template = """
# Custom Script
set top {{ top_module }}
# ...
"""

engine.register_template('custom_script', custom_template)
```

## 고급 기능

### 피드백 루프를 통한 자동 수정

```python
from core.base import Task, TaskType

task = Task(
    task_id='fix_timing',
    task_type=TaskType.TIMING_ANALYSIS,
    description='Fix timing violations',
    context={'module': 'cpu_core'}
)

# 자동으로 에러 수정 시도 (최대 3회)
result = await system.run_with_feedback(task, max_iterations=3)
```

### 병렬 실행

```python
from execution.tool_executor import ParallelExecutor

parallel = ParallelExecutor(system.tool_executor, max_concurrent=8)

jobs = [
    {'tool': 'primetime', 'script': 'timing1.tcl'},
    {'tool': 'spyglass', 'script': 'lint1.tcl'},
    # ...
]

results = await parallel.execute_batch(jobs)
```

### RAG를 활용한 지식 검색

```python
# EDA 매뉴얼 인덱싱
await system.rag_engine.index_eda_manual(
    'PrimeTime',
    './manuals/primetime_user_guide.pdf'
)

# 에러 해결책 검색
solutions = await system.rag_engine.search_error_solutions(
    "Error: UITE-416: Cannot resolve reference"
)
```

## 성능 최적화

### Knowledge Graph 최적화

- 대규모 설계의 경우 서브그래프 추출 사용
- 깊이(depth) 파라미터로 컨텍스트 크기 조절

```python
# 필요한 부분만 추출
subgraph = kg.get_module_context('target_module', depth=1)
```

### 로그 처리 최적화

- `max_entries` 파라미터로 메모리 사용량 제어
- 대용량 로그는 스트리밍 방식으로 처리

```python
from analysis.log_analyzer import LogReducer

reducer = LogReducer()
summary = await reducer.reduce_log('huge.log', max_entries=500)
```

## 트러블슈팅

### 일반적인 문제

1. **툴 실행 실패**
   - 툴 경로 확인: `config['tool_paths']`
   - 라이센스 확인
   - Dry-run 모드로 테스트: `config['dry_run'] = True`

2. **메모리 부족**
   - Knowledge Graph 서브그래프 사용
   - 병렬 실행 수 감소: `max_concurrent` 조정
   - 로그 엔트리 제한

3. **파싱 오류**
   - RTL 문법 확인
   - 인코딩 문제: UTF-8 사용

## 확장 가능성

### 커스텀 에이전트 추가

```python
from core.base import Agent, Task, AnalysisResult

class CustomAgent(Agent):
    async def process(self, task: Task) -> AnalysisResult:
        # 커스텀 로직 구현
        return AnalysisResult(
            success=True,
            summary="Custom processing completed",
            details={}
        )

# 등록
system.router.register_agent(TaskType.CUSTOM, CustomAgent())
```

### 새로운 템플릿 추가

```python
CUSTOM_TEMPLATE = """
# Your custom EDA script template
set design {{ design_name }}
# ...
"""

system.template_engine.register_template('custom', CUSTOM_TEMPLATE)
```

## 기여 방법

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 라이센스

[라이센스 정보 추가]

## 문의

- 이슈: GitHub Issues
- 이메일: [이메일 주소]

## 참고 자료

- [Synopsys Documentation](https://www.synopsys.com/support.html)
- [Cadence Documentation](https://www.cadence.com/en_US/home/support.html)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
