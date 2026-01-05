"""
Log Analysis & Feedback System
EDA 툴 출력 로그 분석 및 피드백 생성
"""
from typing import Dict, List, Optional, Any, Tuple
import re
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import json

from core.base import Agent, Task, AnalysisResult, TaskStatus


@dataclass
class LogEntry:
    """로그 엔트리"""
    severity: str  # ERROR, WARNING, INFO
    message: str
    line_number: Optional[int] = None
    file: Optional[str] = None
    code: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'severity': self.severity,
            'message': self.message,
            'line_number': self.line_number,
            'file': self.file,
            'code': self.code,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


@dataclass
class TimingViolation:
    """타이밍 위반 정보"""
    path_type: str  # setup, hold
    slack: float
    required_time: float
    arrival_time: float
    start_point: str
    end_point: str
    path_group: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'path_type': self.path_type,
            'slack': self.slack,
            'required_time': self.required_time,
            'arrival_time': self.arrival_time,
            'start_point': self.start_point,
            'end_point': self.end_point,
            'path_group': self.path_group
        }


class LogReducer:
    """
    로그 리듀서 - 대용량 로그에서 핵심 정보만 추출
    """
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[str, re.Pattern]:
        """로그 패턴 초기화"""
        return {
            'error': re.compile(r'Error[:\s]+(.+)', re.IGNORECASE),
            'warning': re.compile(r'Warning[:\s]+(.+)', re.IGNORECASE),
            'info': re.compile(r'Info[:\s]+(.+)', re.IGNORECASE),
            'error_code': re.compile(r'([A-Z]+-\d+)'),
            'file_line': re.compile(r'File:\s*(.+?)\s+Line:\s*(\d+)', re.IGNORECASE),
            'timing_slack': re.compile(r'slack\s*(?:\(.*?\))?\s*:\s*([-+]?\d+\.?\d*)', re.IGNORECASE),
        }
    
    async def reduce_log(self, log_path: str, max_entries: int = 1000) -> Dict[str, Any]:
        """
        로그 파일을 요약
        
        Args:
            log_path: 로그 파일 경로
            max_entries: 최대 엔트리 수
        
        Returns:
            요약된 로그 정보
        """
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        entries = []
        error_count = 0
        warning_count = 0
        info_count = 0
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # 에러 매칭
            if match := self.patterns['error'].search(line):
                entry = self._create_log_entry('ERROR', match.group(1), i, line)
                entries.append(entry)
                error_count += 1
            
            # 경고 매칭
            elif match := self.patterns['warning'].search(line):
                entry = self._create_log_entry('WARNING', match.group(1), i, line)
                entries.append(entry)
                warning_count += 1
            
            # 정보 매칭
            elif match := self.patterns['info'].search(line):
                entry = self._create_log_entry('INFO', match.group(1), i, line)
                entries.append(entry)
                info_count += 1
            
            # 최대 엔트리 수 제한
            if len(entries) >= max_entries:
                break
        
        return {
            'log_file': log_path,
            'total_lines': len(lines),
            'error_count': error_count,
            'warning_count': warning_count,
            'info_count': info_count,
            'entries': [e.to_dict() for e in entries],
            'timestamp': datetime.now().isoformat()
        }
    
    def _create_log_entry(self, 
                         severity: str, 
                         message: str, 
                         line_num: int,
                         full_line: str) -> LogEntry:
        """로그 엔트리 생성"""
        
        # 에러 코드 추출
        code = None
        if match := self.patterns['error_code'].search(full_line):
            code = match.group(1)
        
        # 파일 및 라인 번호 추출
        file = None
        file_line = None
        if match := self.patterns['file_line'].search(full_line):
            file = match.group(1)
            file_line = int(match.group(2))
        
        return LogEntry(
            severity=severity,
            message=message,
            line_number=line_num,
            file=file,
            code=code
        )
    
    async def parse_timing_report(self, report_path: str) -> List[TimingViolation]:
        """
        타이밍 리포트 파싱
        
        Args:
            report_path: 타이밍 리포트 파일 경로
        
        Returns:
            타이밍 위반 리스트
        """
        with open(report_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        violations = []
        
        # 타이밍 경로 블록 찾기
        # 간단한 파싱 (실제로는 툴별로 다른 포맷 처리 필요)
        path_blocks = re.split(r'\n\s*\n', content)
        
        for block in path_blocks:
            if 'slack' not in block.lower():
                continue
            
            # Slack 추출
            slack_match = self.patterns['timing_slack'].search(block)
            if not slack_match:
                continue
            
            slack = float(slack_match.group(1))
            
            # 위반이 아니면 스킵 (slack >= 0)
            if slack >= 0:
                continue
            
            # 경로 타입 판단
            path_type = 'setup' if 'max' in block.lower() else 'hold'
            
            # 시작/끝 포인트 추출 (간단한 휴리스틱)
            points = re.findall(r'([a-zA-Z_][\w/\[\]\.]*(?:/[a-zA-Z_][\w]*)?)', block)
            start_point = points[0] if points else "unknown"
            end_point = points[-1] if len(points) > 1 else "unknown"
            
            violation = TimingViolation(
                path_type=path_type,
                slack=slack,
                required_time=0.0,  # 실제로는 파싱 필요
                arrival_time=0.0,
                start_point=start_point,
                end_point=end_point
            )
            
            violations.append(violation)
        
        return violations
    
    async def parse_lint_report(self, report_path: str) -> Dict[str, Any]:
        """
        린트 리포트 파싱
        
        Args:
            report_path: 린트 리포트 파일 경로
        
        Returns:
            린트 분석 결과
        """
        reduced_log = await self.reduce_log(report_path)
        
        # 룰별 위반 카운트
        rule_violations = {}
        for entry in reduced_log['entries']:
            if entry['severity'] in ['ERROR', 'WARNING']:
                code = entry.get('code', 'UNKNOWN')
                rule_violations[code] = rule_violations.get(code, 0) + 1
        
        return {
            'total_violations': reduced_log['error_count'] + reduced_log['warning_count'],
            'error_count': reduced_log['error_count'],
            'warning_count': reduced_log['warning_count'],
            'rule_violations': rule_violations,
            'entries': reduced_log['entries'][:100]  # 상위 100개만
        }


class AnalysisAgent(Agent):
    """
    분석 에이전트 - 로그를 분석하고 근본 원인 파악 및 해결책 제안
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("AnalysisAgent", config)
        self.log_reducer = LogReducer()
    
    async def process(self, task: Task) -> AnalysisResult:
        """
        작업 처리 - 로그 분석 및 피드백 생성
        """
        log_path = task.context.get('log_path')
        if not log_path:
            return AnalysisResult(
                success=False,
                summary="No log path provided",
                details={},
                errors=["log_path not found in task context"]
            )
        
        # 로그 리듀스
        reduced = await self.log_reducer.reduce_log(log_path)
        
        # 분석 수행
        analysis = await self._analyze_logs(reduced, task.context)
        
        # 해결책 제안
        recommendations = await self._generate_recommendations(analysis)
        
        return AnalysisResult(
            success=analysis['success'],
            summary=analysis['summary'],
            details=analysis,
            errors=analysis.get('errors', []),
            warnings=analysis.get('warnings', []),
            recommendations=recommendations
        )
    
    async def _analyze_logs(self, 
                           reduced_log: Dict[str, Any],
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """로그 분석"""
        
        error_count = reduced_log['error_count']
        warning_count = reduced_log['warning_count']
        
        # 치명적 에러 찾기
        critical_errors = [
            entry for entry in reduced_log['entries']
            if entry['severity'] == 'ERROR'
        ]
        
        # 에러 패턴 분석
        error_patterns = self._categorize_errors(critical_errors)
        
        # 성공 여부 판단
        success = error_count == 0
        
        summary = f"Analysis: {error_count} errors, {warning_count} warnings"
        
        return {
            'success': success,
            'summary': summary,
            'error_count': error_count,
            'warning_count': warning_count,
            'critical_errors': critical_errors[:10],  # 상위 10개
            'error_patterns': error_patterns,
            'errors': [e['message'] for e in critical_errors[:5]],
            'warnings': [e['message'] for e in reduced_log['entries'] 
                        if e['severity'] == 'WARNING'][:5]
        }
    
    def _categorize_errors(self, errors: List[Dict[str, Any]]) -> Dict[str, int]:
        """에러 카테고리화"""
        categories = {
            'syntax': 0,
            'timing': 0,
            'constraint': 0,
            'netlist': 0,
            'library': 0,
            'other': 0
        }
        
        for error in errors:
            message = error['message'].lower()
            
            if any(kw in message for kw in ['syntax', 'parse', 'expected']):
                categories['syntax'] += 1
            elif any(kw in message for kw in ['timing', 'slack', 'delay']):
                categories['timing'] += 1
            elif any(kw in message for kw in ['constraint', 'sdc']):
                categories['constraint'] += 1
            elif any(kw in message for kw in ['netlist', 'port', 'instance']):
                categories['netlist'] += 1
            elif any(kw in message for kw in ['library', 'cell', 'lib']):
                categories['library'] += 1
            else:
                categories['other'] += 1
        
        return categories
    
    async def _generate_recommendations(self, 
                                       analysis: Dict[str, Any]) -> List[str]:
        """해결책 생성"""
        recommendations = []
        
        error_patterns = analysis.get('error_patterns', {})
        
        # 카테고리별 추천
        if error_patterns.get('syntax', 0) > 0:
            recommendations.append(
                "Syntax errors detected. Check RTL code for parsing issues."
            )
        
        if error_patterns.get('timing', 0) > 0:
            recommendations.append(
                "Timing violations found. Consider: "
                "1) Adjusting clock constraints, "
                "2) Adding pipeline stages, "
                "3) Optimizing critical paths"
            )
        
        if error_patterns.get('constraint', 0) > 0:
            recommendations.append(
                "Constraint errors detected. Review SDC file for correctness."
            )
        
        if error_patterns.get('netlist', 0) > 0:
            recommendations.append(
                "Netlist issues found. Check module instantiations and port connections."
            )
        
        if error_patterns.get('library', 0) > 0:
            recommendations.append(
                "Library errors detected. Verify library paths and cell availability."
            )
        
        # 일반적인 추천
        if analysis['error_count'] > 10:
            recommendations.append(
                "Multiple errors detected. Fix critical errors first and re-run."
            )
        
        return recommendations


class FeedbackLoop:
    """
    피드백 루프 - 분석 결과를 바탕으로 자동 수정 시도
    """
    
    def __init__(self, max_iterations: int = 3):
        self.max_iterations = max_iterations
        self.iteration_history: List[Dict[str, Any]] = []
    
    async def run(self,
                 initial_task: Task,
                 analysis_agent: AnalysisAgent,
                 fix_callback) -> AnalysisResult:
        """
        피드백 루프 실행
        
        Args:
            initial_task: 초기 작업
            analysis_agent: 분석 에이전트
            fix_callback: 수정 콜백 함수 (recommendations -> new_task)
        
        Returns:
            최종 분석 결과
        """
        current_task = initial_task
        
        for iteration in range(self.max_iterations):
            # 분석 실행
            result = await analysis_agent.process(current_task)
            
            # 이력 저장
            self.iteration_history.append({
                'iteration': iteration,
                'task_id': current_task.task_id,
                'result': result.__dict__,
                'timestamp': datetime.now().isoformat()
            })
            
            # 성공하면 종료
            if result.success:
                return result
            
            # 추천사항이 없으면 종료
            if not result.recommendations:
                return result
            
            # 수정 시도
            try:
                current_task = await fix_callback(result.recommendations)
            except Exception as e:
                result.errors.append(f"Fix callback failed: {str(e)}")
                return result
        
        # 최대 반복 횟수 도달
        result.errors.append(f"Max iterations ({self.max_iterations}) reached")
        return result
    
    def get_history(self) -> List[Dict[str, Any]]:
        """이력 반환"""
        return self.iteration_history
