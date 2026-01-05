# RTL Agent System - 프로젝트 구조

## 📁 전체 디렉토리 구조

```
rtl_agent_system/
│
├── README.md                          # 메인 문서
├── OVERVIEW.md                        # 상세 기술 문서
├── requirements.txt                   # Python 의존성
├── quick_start.py                     # 빠른 시작 스크립트
├── examples.py                        # 사용 예제 모음
├── main.py                           # 메인 시스템 통합 클래스
│
├── core/                             # 핵심 기본 클래스
│   ├── __init__.py
│   └── base.py                       # Agent, Task, Graph 등 기본 클래스
│
├── agents/                           # 에이전트 계층
│   ├── __init__.py
│   └── supervisor.py                 # SupervisorAgent & DynamicRouter
│
├── knowledge/                        # 지식 관리 계층
│   ├── __init__.py
│   ├── knowledge_graph.py           # RTL Knowledge Graph
│   └── rag_engine.py                # RAG Engine & Vector Store
│
├── execution/                        # 실행 계층
│   ├── __init__.py
│   ├── template_engine.py           # Jinja2 템플릿 엔진
│   └── tool_executor.py             # EDA 툴 실행기
│
└── analysis/                         # 분석 계층
    ├── __init__.py
    └── log_analyzer.py              # 로그 분석 & 피드백 루프
```

## 📋 파일별 설명

### 루트 디렉토리

#### README.md
- 시스템 전체 개요
- 설치 방법
- 빠른 시작 가이드
- 지원 EDA 툴 목록
- 고급 기능 설명
- 트러블슈팅

#### OVERVIEW.md
- 생성된 파일 목록
- 각 컴포넌트 상세 설명
- 실전 사용 시나리오
- 커스터마이징 방법
- 성능 최적화 팁
- 디버깅 가이드

#### requirements.txt
- numpy: 벡터 연산
- jinja2: 템플릿 엔진
- (선택) 고급 기능용 라이브러리

#### main.py
- **RTLAgentSystem**: 메인 통합 클래스
- 모든 컴포넌트 초기화
- 워크스페이스 관리
- 명령어 실행 인터페이스
- 상태 저장/로드

#### quick_start.py
- 자동 워크스페이스 생성
- 샘플 RTL 생성
- 시스템 초기화
- 데모 실행
- 결과 출력

#### examples.py
- 6가지 실전 예제:
  1. 기본 사용법
  2. 타이밍 분석
  3. Knowledge Graph 활용
  4. RAG Engine 검색
  5. Template Engine 사용
  6. 피드백 루프

### core/ - 핵심 기본 클래스

#### base.py (2,900 lines)
**데이터 구조:**
- `Task`: 작업 정의
- `TaskType`: 작업 유형 Enum
- `TaskStatus`: 작업 상태
- `ExecutionPlan`: 실행 계획
- `AnalysisResult`: 분석 결과

**추상 클래스:**
- `Agent`: 모든 에이전트의 베이스
- `KnowledgeStore`: 지식 저장소 인터페이스
- `ToolExecutor`: 툴 실행기 인터페이스

**그래프 구조:**
- `GraphNode`: 노드 (모듈, 신호, 인스턴스)
- `GraphEdge`: 엣지 (연결, 계층, 의존성)
- `Graph`: 그래프 컨테이너

### agents/ - 에이전트 계층

#### supervisor.py (3,500 lines)
**SupervisorAgent:**
- 자연어 명령 파싱
- 정규표현식 기반 작업 유형 판단
- 모듈명 추출
- 실행 계획 수립
- 6가지 작업 유형별 플랜 생성:
  - 타이밍 분석
  - RTL 수정
  - 스크립트 튜닝
  - 검증
  - 전력 최적화
  - 디버그

**DynamicRouter:**
- 작업별 에이전트 라우팅
- 병렬/순차 실행 관리
- 의존성 해결
- 실행 계획 실행

### knowledge/ - 지식 관리 계층

#### knowledge_graph.py (3,300 lines)
**DesignKnowledgeGraph:**
- RTL 파싱 (Verilog/SystemVerilog)
- 모듈 추출 (module...endmodule)
- 포트 파싱 (input/output/inout)
- 인스턴스 추출
- 신호 선언 추출 (wire/reg/logic)
- TCL 스크립트 파싱
- 모듈 컨텍스트 추출 (서브그래프)
- 패턴 기반 모듈 검색
- 계층 구조 분석
- 의존성 분석
- 저장/로드 (JSON)

#### rag_engine.py (3,900 lines)
**Document & VectorStore:**
- 문서 데이터 구조
- 벡터 저장소 (간단한 구현)
- 임베딩 생성 (데모용 해시 기반)
- 코사인 유사도 검색
- 저장/로드 (Pickle)

**RAGEngine:**
- 디렉토리 인덱싱
- 파일 청크 분할
- 지식 검색 (Top-K)
- 컨텍스트 생성
- EDA 매뉴얼 인덱싱
- 에러 해결책 검색
- Lesson Learned 관리

### execution/ - 실행 계층

#### template_engine.py (2,400 lines)
**TemplateEngine:**
- Jinja2 기반 렌더링
- 템플릿 등록/캐싱
- 커스텀 필터 (format_list, format_path)
- 다중 파일 지원

**기본 템플릿:**
- `PRIMETIME_STA_TEMPLATE`: PrimeTime 타이밍 분석
- `SPYGLASS_LINT_TEMPLATE`: SpyGlass 린트
- `MAKEFILE_TEMPLATE`: Makefile 생성
- `FUSION_COMPILER_TEMPLATE`: Fusion Compiler 합성

**예제 컨텍스트:**
- PrimeTime 설정 예제
- SpyGlass 설정 예제
- Makefile 설정 예제

#### tool_executor.py (2,900 lines)
**EDAToolExecutor:**
- 명령어 구성 (툴별 템플릿)
- 비동기 프로세스 실행
- 로그 수집 (stdout/stderr)
- 출력 검증
- 실행 이력 관리

**DryRunExecutor:**
- 시뮬레이션 모드
- 테스트용

**ParallelExecutor:**
- 세마포어 기반 병렬 실행
- 배치 실행

### analysis/ - 분석 계층

#### log_analyzer.py (4,200 lines)
**LogEntry & TimingViolation:**
- 로그 엔트리 데이터 구조
- 타이밍 위반 데이터 구조

**LogReducer:**
- 정규표현식 기반 로그 파싱
- Error/Warning/Info 추출
- 타이밍 리포트 파싱
- 린트 리포트 파싱
- 로그 요약 (JSON)

**AnalysisAgent:**
- 로그 분석
- 에러 카테고리화 (syntax, timing, constraint 등)
- 근본 원인 추론
- 해결책 생성

**FeedbackLoop:**
- 자동 수정 반복
- 최대 반복 횟수 제어
- 이력 관리

## 🔄 의존성 관계

```
main.py
  ├─> agents/supervisor.py
  │     └─> core/base.py
  ├─> knowledge/knowledge_graph.py
  │     └─> core/base.py
  ├─> knowledge/rag_engine.py
  │     └─> core/base.py
  ├─> execution/template_engine.py
  ├─> execution/tool_executor.py
  │     └─> core/base.py
  └─> analysis/log_analyzer.py
        └─> core/base.py
```

## 📊 코드 통계

| 모듈 | 파일 | 라인 수 | 주요 클래스/함수 |
|------|------|---------|-----------------|
| core | base.py | ~200 | 10개 클래스 |
| agents | supervisor.py | ~350 | 2개 클래스 |
| knowledge | knowledge_graph.py | ~330 | 1개 클래스 |
| knowledge | rag_engine.py | ~390 | 3개 클래스 |
| execution | template_engine.py | ~240 | 1개 클래스 + 4개 템플릿 |
| execution | tool_executor.py | ~290 | 3개 클래스 |
| analysis | log_analyzer.py | ~420 | 4개 클래스 |
| main | main.py | ~410 | 1개 메인 클래스 |
| examples | examples.py | ~260 | 6개 예제 함수 |
| quick_start | quick_start.py | ~230 | 5개 함수 |
| **Total** | **11 files** | **~3,120** | **32개 클래스** |

## 🚀 실행 순서

### 1. 설치
```bash
pip install -r requirements.txt
```

### 2. 빠른 시작
```bash
python quick_start.py
```

### 3. 예제 실행
```bash
python examples.py
```

### 4. 실제 사용
```python
from main import RTLAgentSystem

system = RTLAgentSystem('./workspace')
await system.initialize(rtl_dirs=['./rtl'])
result = await system.execute_command("명령어")
```

## 🎯 주요 진입점

1. **quick_start.py** - 처음 시작하는 경우
2. **examples.py** - 기능별 예제 확인
3. **main.py** - 실제 프로젝트에 통합

## 📝 확장 포인트

- `core/base.py`: 새로운 베이스 클래스 추가
- `agents/`: 커스텀 에이전트 추가
- `execution/template_engine.py`: 새 EDA 툴 템플릿 추가
- `knowledge/`: 새로운 파서 추가

## 🔧 설정 파일

실행 시 자동 생성되는 워크스페이스 구조:
```
workspace/
├── knowledge/       # KG, RAG 저장소
├── templates/       # Jinja2 템플릿
├── scripts/         # 생성된 스크립트
├── reports/         # 분석 결과
└── logs/           # 실행 로그
```
