# RTL Agent System - 시스템 개요

## 📋 생성된 파일 목록

```
rtl_agent_system/
├── README.md                    # 전체 시스템 문서
├── requirements.txt             # 의존성 목록
├── quick_start.py              # 빠른 시작 스크립트
├── examples.py                 # 사용 예제
├── main.py                     # 메인 시스템 클래스
│
├── core/                       # 핵심 기본 클래스
│   ├── __init__.py
│   └── base.py                 # Agent, Task, Graph 등 기본 클래스
│
├── agents/                     # 에이전트 계층
│   ├── __init__.py
│   └── supervisor.py           # Supervisor & Router
│
├── knowledge/                  # 지식 관리 계층
│   ├── __init__.py
│   ├── knowledge_graph.py      # RTL Knowledge Graph
│   └── rag_engine.py          # RAG Engine
│
├── execution/                  # 실행 계층
│   ├── __init__.py
│   ├── template_engine.py     # Jinja2 템플릿 엔진
│   └── tool_executor.py       # EDA 툴 실행기
│
└── analysis/                   # 분석 계층
    ├── __init__.py
    └── log_analyzer.py        # 로그 분석 & 피드백
```

## 🚀 빠른 시작

### 1단계: 설치

```bash
# 필요한 패키지 설치
pip install numpy jinja2

# 또는 requirements.txt 사용
pip install -r requirements.txt
```

### 2단계: 빠른 시작 실행

```bash
python quick_start.py
```

이 스크립트는 다음을 수행합니다:
- 워크스페이스 자동 생성
- 샘플 RTL 파일 생성
- Knowledge Graph 구축
- 데모 명령어 실행
- 결과 리포트 생성

### 3단계: 예제 실행

```bash
python examples.py
```

6가지 예제가 실행됩니다:
1. 기본 사용법
2. 타이밍 분석
3. Knowledge Graph 활용
4. RAG Engine 검색
5. Template Engine 사용
6. 피드백 루프

## 📚 주요 컴포넌트 설명

### 1. Core Layer (core/base.py)

**기본 데이터 구조:**
- `Task`: 작업 정의
- `TaskType`: 작업 유형 (TIMING_ANALYSIS, RTL_MODIFICATION 등)
- `ExecutionPlan`: 실행 계획
- `AnalysisResult`: 분석 결과

**인터페이스:**
- `Agent`: 모든 에이전트의 기본 클래스
- `KnowledgeStore`: 지식 저장소 인터페이스
- `ToolExecutor`: 툴 실행기 인터페이스

**그래프 구조:**
- `Graph`: 일반 그래프
- `GraphNode`: 노드 (모듈, 신호, 인스턴스)
- `GraphEdge`: 엣지 (연결, 계층, 의존성)

### 2. Supervisor Layer (agents/supervisor.py)

**SupervisorAgent:**
- 자연어 명령 파싱
- 작업 계획 수립
- 작업 유형 판단

**DynamicRouter:**
- 작업별 에이전트 라우팅
- 병렬/순차 실행 관리
- 의존성 해결

### 3. Knowledge Layer

**DesignKnowledgeGraph (knowledge/knowledge_graph.py):**
- RTL 파일 파싱 (Verilog/SystemVerilog)
- 모듈 계층 구조 생성
- 신호 연결 관계 파악
- 의존성 분석
- 서브그래프 추출

주요 메서드:
```python
# RTL 파싱
await kg.parse_rtl_file('./rtl/top.v')

# 모듈 컨텍스트 추출
context = kg.get_module_context('dma_controller', depth=2)

# 계층 구조 조회
hierarchy = kg.get_module_hierarchy('top')

# 의존성 분석
deps = kg.analyze_dependencies()
```

**RAGEngine (knowledge/rag_engine.py):**
- 벡터 기반 문서 검색
- EDA 매뉴얼 인덱싱
- 과거 해결 사례 검색
- 컨텍스트 생성

주요 메서드:
```python
# 문서 인덱싱
await rag.index_directory('./docs')

# 지식 검색
results = await rag.search_knowledge('timing optimization')

# 에러 해결책 검색
solutions = await rag.search_error_solutions(error_msg)
```

### 4. Execution Layer

**TemplateEngine (execution/template_engine.py):**
- Jinja2 기반 스크립트 생성
- 다중 EDA 툴 지원
- 커스텀 템플릿 등록

기본 템플릿:
- `primetime_sta`: PrimeTime 타이밍 분석
- `spyglass_lint`: SpyGlass 린트 체크
- `fusion_compiler`: Fusion Compiler 합성
- `makefile`: Makefile 생성

사용 예:
```python
engine = create_default_templates('./templates')

context = {
    'target_module': 'cpu_core',
    'netlist_path': './netlist/cpu_core.v',
    # ...
}

script = engine.render('primetime_sta', context, 'output.tcl')
```

**ToolExecutor (execution/tool_executor.py):**
- EDA 툴 실행 관리
- 로그 수집
- 결과 검증
- 병렬 실행 지원

실행 모드:
- `EDAToolExecutor`: 실제 툴 실행
- `DryRunExecutor`: 시뮬레이션 모드
- `ParallelExecutor`: 병렬 실행 래퍼

### 5. Analysis Layer (analysis/log_analyzer.py)

**LogReducer:**
- 대용량 로그 요약
- 에러/경고 추출
- 타이밍 위반 파싱
- 린트 리포트 분석

**AnalysisAgent:**
- 로그 분석
- 근본 원인 파악
- 해결책 제안

**FeedbackLoop:**
- 자동 에러 수정
- 반복 최적화
- 이력 관리

## 💡 실전 사용 시나리오

### 시나리오 1: 타이밍 위반 자동 분석

```python
from main import RTLAgentSystem

system = RTLAgentSystem('./workspace')
await system.initialize(rtl_dirs=['./rtl'])

result = await system.execute_command(
    "CPU 코어의 setup 타이밍 위반을 분석하고 해결 방안을 제시해줘"
)

if not result.success:
    print("Violations found:")
    for rec in result.recommendations:
        print(f"  - {rec}")
```

### 시나리오 2: RTL 린트 체크

```python
result = await system.execute_command(
    "DMA 컨트롤러의 RTL 코드를 SpyGlass로 린트 체크해줘"
)
```

### 시나리오 3: 자동 최적화

```python
task = Task(
    task_id='optimize',
    task_type=TaskType.POWER_OPTIMIZATION,
    description='Optimize power consumption',
    context={'module': 'soc_top'}
)

# 자동으로 최적화 시도 (최대 3회 반복)
result = await system.run_with_feedback(task, max_iterations=3)
```

## 🔧 커스터마이징

### 1. 커스텀 에이전트 추가

```python
from core.base import Agent

class CustomTimingAgent(Agent):
    async def process(self, task: Task) -> AnalysisResult:
        # 커스텀 타이밍 분석 로직
        return AnalysisResult(...)

# 등록
system.router.register_agent(TaskType.TIMING_ANALYSIS, CustomTimingAgent())
```

### 2. 커스텀 템플릿 추가

```python
MY_TEMPLATE = """
# Custom EDA Script
set design {{ design_name }}
read_verilog {{ rtl_files | format_list }}
"""

system.template_engine.register_template('my_tool', MY_TEMPLATE)
```

### 3. 커스텀 파서 추가

```python
# Knowledge Graph에 커스텀 파서 추가
class MyParser:
    async def parse_custom_file(self, filepath):
        # 파싱 로직
        return nodes, edges

kg.register_parser('custom', MyParser())
```

## 📊 성능 특징

### 메모리 효율성
- Knowledge Graph 서브그래프 추출로 메모리 절약
- 로그 스트리밍 처리
- 청크 단위 문서 처리

### 병렬 처리
- 비동기 I/O (asyncio)
- 멀티 툴 병렬 실행
- 세마포어 기반 동시성 제어

### 확장성
- 모듈화된 아키텍처
- 플러그인 방식 에이전트
- 템플릿 기반 스크립트 생성

## 🐛 디버깅 팁

### 1. Dry-run 모드 활성화

```python
config = {'dry_run': True}
system = RTLAgentSystem('./workspace', config)
```

### 2. 로그 레벨 조정

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 3. 중간 결과 저장

```python
# Knowledge Graph 저장
system.knowledge_graph.save('./debug/kg.json')

# 실행 이력 저장
system.tool_executor.save_history('./debug/exec_history.json')
```

## 🔒 보안 고려사항

1. **입력 검증**: 사용자 명령어 sanitization
2. **파일 접근 제한**: 워크스페이스 내로 제한
3. **툴 경로 검증**: 허가된 툴만 실행
4. **로그 민감정보**: 자동 마스킹

## 📈 향후 개선 방향

1. **LLM 통합**: OpenAI/Anthropic API 연동
2. **웹 인터페이스**: FastAPI + Streamlit
3. **분산 실행**: Celery/Ray 기반 분산 처리
4. **고급 RAG**: ChromaDB, Pinecone 통합
5. **모델 학습**: Fine-tuning for EDA domain

## 📞 지원

- **버그 리포트**: GitHub Issues
- **기능 요청**: Pull Requests
- **질문**: Discussions

## 📄 라이센스

[라이센스 정보]

---

**개발자**: Seungjoon Lee  
**버전**: 1.0.0  
**마지막 업데이트**: 2026-01-05
