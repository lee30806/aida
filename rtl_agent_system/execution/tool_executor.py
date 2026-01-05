"""
EDA Tool Executor - 실제 EDA 툴 실행
"""
from typing import Dict, Any, Optional, List
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
import re
import json

from core.base import ToolExecutor, AnalysisResult


class EDAToolExecutor(ToolExecutor):
    """
    EDA 툴 실행기 - Synopsys, Cadence 등의 툴 실행
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.tool_paths = self.config.get('tool_paths', {})
        self.execution_history: List[Dict[str, Any]] = []
    
    async def execute(self,
                     tool_name: str,
                     script_path: str,
                     args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        EDA 툴 실행
        
        Args:
            tool_name: 툴 이름 (primetime, spyglass, dc_shell 등)
            script_path: 스크립트 파일 경로
            args: 추가 인자
        
        Returns:
            실행 결과 딕셔너리
        """
        args = args or {}
        
        # 툴 명령어 구성
        command = self._build_command(tool_name, script_path, args)
        
        # 실행
        start_time = datetime.now()
        
        try:
            result = await self._run_command(command, args.get('working_dir'))
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            execution_record = {
                'tool': tool_name,
                'script': script_path,
                'command': command,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration': duration,
                'return_code': result['return_code'],
                'success': result['return_code'] == 0
            }
            
            self.execution_history.append(execution_record)
            
            return {
                'success': result['return_code'] == 0,
                'return_code': result['return_code'],
                'stdout': result['stdout'],
                'stderr': result['stderr'],
                'duration': duration,
                'log_file': result.get('log_file')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'return_code': -1
            }
    
    def _build_command(self, 
                      tool_name: str, 
                      script_path: str, 
                      args: Dict[str, Any]) -> List[str]:
        """명령어 구성"""
        
        # 툴별 명령어 템플릿
        tool_commands = {
            'primetime': ['pt_shell', '-f', script_path],
            'spyglass': ['spyglass', '-batch', '-tcl', script_path],
            'dc_shell': ['dc_shell-xg-t', '-f', script_path],
            'fc_shell': ['fc_shell', '-f', script_path],
            'icc2_shell': ['icc2_shell', '-f', script_path],
        }
        
        # 기본 명령어
        base_command = tool_commands.get(tool_name.lower())
        if not base_command:
            # 커스텀 툴인 경우
            tool_path = self.tool_paths.get(tool_name)
            if not tool_path:
                raise ValueError(f"Unknown tool: {tool_name}")
            base_command = [tool_path, script_path]
        
        # 추가 인자
        extra_args = args.get('extra_args', [])
        if isinstance(extra_args, str):
            extra_args = extra_args.split()
        
        return base_command + extra_args
    
    async def _run_command(self, 
                          command: List[str], 
                          working_dir: Optional[str] = None) -> Dict[str, Any]:
        """명령어 실행"""
        
        # 로그 파일 설정
        log_file = None
        if working_dir:
            log_dir = Path(working_dir) / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = str(log_dir / f"execution_{timestamp}.log")
        
        # 프로세스 실행
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir
        )
        
        stdout, stderr = await process.communicate()
        
        stdout_text = stdout.decode('utf-8', errors='ignore')
        stderr_text = stderr.decode('utf-8', errors='ignore')
        
        # 로그 파일에 저장
        if log_file:
            with open(log_file, 'w') as f:
                f.write("=== COMMAND ===\n")
                f.write(" ".join(command) + "\n\n")
                f.write("=== STDOUT ===\n")
                f.write(stdout_text + "\n\n")
                f.write("=== STDERR ===\n")
                f.write(stderr_text + "\n")
        
        return {
            'return_code': process.returncode,
            'stdout': stdout_text,
            'stderr': stderr_text,
            'log_file': log_file
        }
    
    async def validate_output(self, output_path: str) -> AnalysisResult:
        """
        출력 파일 검증
        
        Args:
            output_path: 출력 파일/디렉토리 경로
        
        Returns:
            검증 결과
        """
        path = Path(output_path)
        
        if not path.exists():
            return AnalysisResult(
                success=False,
                summary="Output not found",
                details={'path': output_path},
                errors=[f"Output path does not exist: {output_path}"]
            )
        
        # 파일인 경우
        if path.is_file():
            return self._validate_file(path)
        
        # 디렉토리인 경우
        if path.is_dir():
            return self._validate_directory(path)
        
        return AnalysisResult(
            success=False,
            summary="Invalid output path",
            details={'path': output_path},
            errors=["Path is neither file nor directory"]
        )
    
    def _validate_file(self, file_path: Path) -> AnalysisResult:
        """파일 검증"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 간단한 검증: 에러/경고 카운트
            errors = re.findall(r'\bError\b', content, re.IGNORECASE)
            warnings = re.findall(r'\bWarning\b', content, re.IGNORECASE)
            
            return AnalysisResult(
                success=len(errors) == 0,
                summary=f"File validated: {len(errors)} errors, {len(warnings)} warnings",
                details={
                    'file': str(file_path),
                    'size': file_path.stat().st_size,
                    'error_count': len(errors),
                    'warning_count': len(warnings)
                },
                errors=[f"Found {len(errors)} errors in output"],
                warnings=[f"Found {len(warnings)} warnings in output"]
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                summary="Failed to read output file",
                details={'file': str(file_path)},
                errors=[str(e)]
            )
    
    def _validate_directory(self, dir_path: Path) -> AnalysisResult:
        """디렉토리 검증"""
        files = list(dir_path.rglob('*'))
        
        return AnalysisResult(
            success=True,
            summary=f"Directory contains {len(files)} files",
            details={
                'directory': str(dir_path),
                'file_count': len(files)
            }
        )
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """실행 이력 반환"""
        return self.execution_history
    
    def save_history(self, filepath: str):
        """실행 이력 저장"""
        with open(filepath, 'w') as f:
            json.dump(self.execution_history, f, indent=2)


class DryRunExecutor(ToolExecutor):
    """
    Dry Run 모드 실행기 - 실제 툴을 실행하지 않고 시뮬레이션
    테스트 및 디버깅용
    """
    
    def __init__(self):
        self.executions: List[Dict[str, Any]] = []
    
    async def execute(self,
                     tool_name: str,
                     script_path: str,
                     args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """시뮬레이션 실행"""
        
        execution = {
            'tool': tool_name,
            'script': script_path,
            'args': args or {},
            'timestamp': datetime.now().isoformat(),
            'mode': 'dry_run'
        }
        
        self.executions.append(execution)
        
        # 시뮬레이션 결과 반환
        return {
            'success': True,
            'return_code': 0,
            'stdout': f"[DRY RUN] Would execute {tool_name} with {script_path}",
            'stderr': '',
            'duration': 0.0
        }
    
    async def validate_output(self, output_path: str) -> AnalysisResult:
        """시뮬레이션 검증"""
        return AnalysisResult(
            success=True,
            summary=f"[DRY RUN] Would validate {output_path}",
            details={'path': output_path, 'mode': 'dry_run'}
        )
    
    def get_executions(self) -> List[Dict[str, Any]]:
        """실행 목록 반환"""
        return self.executions


class ParallelExecutor:
    """
    병렬 실행 매니저 - 여러 툴을 동시에 실행
    """
    
    def __init__(self, executor: ToolExecutor, max_concurrent: int = 4):
        self.executor = executor
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def execute_batch(self, 
                           jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        여러 작업을 병렬로 실행
        
        Args:
            jobs: 작업 리스트, 각 작업은 {'tool', 'script', 'args'} 포함
        
        Returns:
            결과 리스트
        """
        tasks = [self._execute_with_semaphore(job) for job in jobs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외 처리
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'error': str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _execute_with_semaphore(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """세마포어를 사용한 실행"""
        async with self.semaphore:
            return await self.executor.execute(
                tool_name=job['tool'],
                script_path=job['script'],
                args=job.get('args')
            )
