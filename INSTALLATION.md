# RTL Agent System - 설치 및 실행 가이드

## 📦 파일 다운로드 및 압축 해제

### 1. 압축 파일 다운로드
`rtl_agent_system.tar.gz` 파일을 다운로드하세요.

### 2. 압축 해제

**Linux/Mac:**
```bash
tar -xzf rtl_agent_system.tar.gz
cd rtl_agent_system
```

**Windows (Git Bash 또는 WSL):**
```bash
tar -xzf rtl_agent_system.tar.gz
cd rtl_agent_system
```

**Windows (7-Zip 사용):**
1. 7-Zip으로 `rtl_agent_system.tar.gz` 우클릭 → "압축 풀기"
2. 생성된 `rtl_agent_system.tar` 파일도 한번 더 압축 해제
3. `rtl_agent_system` 폴더로 이동

## 🔧 환경 설정

### Python 버전 확인
```bash
python --version  # Python 3.7 이상 필요
```

### 가상환경 생성 (권장)

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 의존성 설치

**필수 패키지:**
```bash
pip install numpy jinja2
```

**또는 requirements.txt 사용:**
```bash
pip install -r requirements.txt
```

## 🚀 빠른 시작

### 1단계: 디렉토리 구조 확인
```bash
ls -la
# README.md, main.py, quick_start.py 등이 보여야 함

ls -la core/
# base.py, __init__.py가 보여야 함
```

### 2단계: 빠른 시작 스크립트 실행
```bash
python quick_start.py
```

**실행 내용:**
- 워크스페이스 자동 생성 (`./workspace`)
- 샘플 RTL 파일 생성
- Knowledge Graph 구축
- 3가지 예제 명령 실행
- 결과 리포트 생성

**예상 출력:**
```
╔══════════════════════════════════════════════════════════╗
║     RTL Agent System - Quick Start                      ║
╚══════════════════════════════════════════════════════════╝

[1/4] Setting up workspace...
  ✓ Workspace created at: /path/to/workspace

[2/4] Creating sample RTL files...
  ✓ Sample RTL created

[3/4] Initializing RTL Agent System...
  ✓ System initialized successfully
  ✓ Knowledge Graph: 15 nodes

[4/4] Running demonstration...
  Example 1: DMA 모듈의 구조를 분석해줘
    Status: ✓ Success
    ...

Quick start completed successfully!
```

### 3단계: 예제 실행
```bash
python examples.py
```

**포함된 예제:**
1. 기본 사용법
2. 타이밍 분석
3. Knowledge Graph 활용
4. RAG Engine 검색
5. Template Engine 사용
6. 피드백 루프

## 📖 실제 사용 예제

### Python 스크립트로 사용

**test_system.py 생성:**
```python
import asyncio
from main import RTLAgentSystem

async def main():
    # 시스템 초기화
    system = RTLAgentSystem(
        workspace_dir='./my_workspace',
        config={
            'dry_run': False,  # 실제 툴 실행
            'tool_paths': {
                'primetime': '/tools/synopsys/pt/bin/pt_shell',
                'spyglass': '/tools/atrenta/spyglass/bin/spyglass'
            }
        }
    )
    
    # RTL 디렉토리 인덱싱
    await system.initialize(rtl_dirs=['./rtl_design'])
    
    # 명령 실행
    result = await system.execute_command(
        "DMA 모듈의 setup 타이밍을 분석해줘"
    )
    
    # 결과 출력
    print(f"성공: {result.success}")
    print(f"요약: {result.summary}")
    
    if result.errors:
        print("에러:", result.errors)
    
    if result.recommendations:
        print("추천사항:")
        for rec in result.recommendations:
            print(f"  - {rec}")
    
    # 상태 저장
    system.save_state()

if __name__ == '__main__':
    asyncio.run(main())
```

**실행:**
```bash
python test_system.py
```

### Interactive Python으로 사용

```bash
python
```

```python
>>> import asyncio
>>> from main import RTLAgentSystem
>>> 
>>> async def test():
...     system = RTLAgentSystem('./workspace', {'dry_run': True})
...     await system.initialize()
...     result = await system.execute_command("타이밍 분석")
...     print(result.summary)
... 
>>> asyncio.run(test())
```

## 🔍 생성된 파일 확인

### 워크스페이스 구조
```bash
tree workspace/
```

```
workspace/
├── knowledge/
│   ├── design_kg.json      # Knowledge Graph
│   └── rag_store.pkl       # RAG Vector Store
├── templates/
│   ├── primetime_sta.j2
│   ├── spyglass_lint.j2
│   └── ...
├── scripts/
│   └── (생성된 TCL/Makefile 스크립트)
├── reports/
│   └── (분석 결과 리포트)
└── logs/
    └── (실행 로그)
```

### 결과 확인
```bash
# Knowledge Graph 확인
cat workspace/knowledge/design_kg.json

# 실행 리포트 확인
ls -la workspace/reports/

# 생성된 스크립트 확인
ls -la workspace/scripts/
```

## 🐛 문제 해결

### 문제 1: 모듈을 찾을 수 없음
```
ModuleNotFoundError: No module named 'core'
```

**해결:**
```bash
# 현재 디렉토리 확인
pwd
# rtl_agent_system 디렉토리에 있어야 함

# Python path 확인
python -c "import sys; print(sys.path)"

# PYTHONPATH 설정 (필요시)
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 문제 2: numpy/jinja2 없음
```
ModuleNotFoundError: No module named 'numpy'
```

**해결:**
```bash
pip install numpy jinja2
```

### 문제 3: 권한 오류
```
PermissionError: [Errno 13] Permission denied: './workspace'
```

**해결:**
```bash
# 디렉토리 권한 확인
ls -la

# 워크스페이스 수동 생성
mkdir -p workspace
chmod 755 workspace
```

### 문제 4: asyncio 관련 에러 (Windows)
```
RuntimeError: Event loop is closed
```

**해결 (Windows):**
```python
# Windows에서는 ProactorEventLoop 사용
import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# 이후 정상 실행
asyncio.run(main())
```

## ✅ 설치 확인

### 체크리스트

```bash
# 1. 파일 구조 확인
ls -la core/base.py
ls -la agents/supervisor.py
ls -la main.py

# 2. Python 임포트 테스트
python -c "from core.base import Agent; print('✓ core.base OK')"
python -c "from main import RTLAgentSystem; print('✓ main OK')"

# 3. 간단한 실행 테스트
python -c "
import asyncio
from main import RTLAgentSystem

async def test():
    system = RTLAgentSystem('./test_ws', {'dry_run': True})
    await system.initialize()
    print('✓ System initialization OK')

asyncio.run(test())
"

# 4. 워크스페이스 확인
ls -la workspace/ 2>/dev/null && echo "✓ Workspace created" || echo "⚠ Run quick_start.py first"
```

모든 항목이 ✓이면 정상 설치된 것입니다!

## 📚 다음 단계

1. **README.md** 읽기 - 전체 기능 이해
2. **OVERVIEW.md** 읽기 - 상세 기술 문서
3. **PROJECT_STRUCTURE.md** 읽기 - 코드 구조 파악
4. **examples.py** 실행 - 다양한 사용 예제 확인
5. 실제 RTL 프로젝트에 적용

## 💡 팁

### Dry-run 모드로 테스트
```python
config = {'dry_run': True}  # 실제 툴 실행 안함
system = RTLAgentSystem('./workspace', config)
```

### 로깅 활성화
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 병렬 실행 수 조정
```python
config = {'max_concurrent': 8}  # 동시 실행 작업 수
```

## 📞 지원

- 문제 발생 시: GitHub Issues
- 기능 요청: Pull Requests
- 질문: Discussions

---

설치 완료! 🎉
```
