"""
Template Engine - EDA 스크립트 생성
Jinja2 기반 템플릿 렌더링
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
from jinja2 import Environment, FileSystemLoader, Template
from datetime import datetime


class TemplateEngine:
    """
    템플릿 엔진 - LLM의 구조화된 출력을 실행 가능한 스크립트로 변환
    """
    
    def __init__(self, template_dir: str):
        """
        Args:
            template_dir: 템플릿 파일들이 있는 디렉토리
        """
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 커스텀 필터 등록
        self.env.filters['format_list'] = self._format_list
        self.env.filters['format_path'] = self._format_path
        
        # 템플릿 레지스트리
        self.templates: Dict[str, Template] = {}
    
    def register_template(self, name: str, template_content: str):
        """
        템플릿 등록
        
        Args:
            name: 템플릿 이름
            template_content: 템플릿 내용
        """
        # 파일로 저장
        template_path = self.template_dir / f"{name}.j2"
        with open(template_path, 'w') as f:
            f.write(template_content)
        
        # 캐시에 로드
        self.templates[name] = self.env.get_template(f"{name}.j2")
    
    def render(self, 
               template_name: str, 
               context: Dict[str, Any],
               output_path: Optional[str] = None) -> str:
        """
        템플릿 렌더링
        
        Args:
            template_name: 템플릿 이름
            context: 렌더링 컨텍스트 (JSON 데이터)
            output_path: 출력 파일 경로 (None이면 문자열 반환)
        
        Returns:
            렌더링된 스크립트
        """
        template = self._get_template(template_name)
        
        # 기본 컨텍스트 추가
        full_context = {
            'timestamp': datetime.now().isoformat(),
            'template_name': template_name,
            **context
        }
        
        rendered = template.render(**full_context)
        
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(rendered)
        
        return rendered
    
    def _get_template(self, name: str) -> Template:
        """템플릿 가져오기"""
        if name in self.templates:
            return self.templates[name]
        
        # 파일에서 로드 시도
        try:
            template = self.env.get_template(f"{name}.j2")
            self.templates[name] = template
            return template
        except Exception as e:
            raise ValueError(f"Template '{name}' not found: {e}")
    
    @staticmethod
    def _format_list(items: List[Any], separator: str = " ") -> str:
        """리스트를 문자열로 포맷팅"""
        return separator.join(str(item) for item in items)
    
    @staticmethod
    def _format_path(path: str) -> str:
        """경로 포맷팅 (백슬래시 -> 슬래시)"""
        return path.replace("\\", "/")


# 기본 템플릿 정의

PRIMETIME_STA_TEMPLATE = """
# PrimeTime Static Timing Analysis Script
# Generated: {{ timestamp }}
# Target: {{ target_module }}

# Read design
set search_path "{{ search_path | format_path }}"
set link_library "{{ link_library | format_list }}"
set target_library "{{ target_library }}"

# Read netlist
read_verilog {{ netlist_path | format_path }}
current_design {{ target_module }}
link

# Read SDC constraints
read_sdc {{ sdc_path | format_path }}

# Timing analysis
{% if analysis_mode == "setup" %}
report_timing -delay max -max_paths {{ max_paths }} -nworst {{ nworst }}
{% elif analysis_mode == "hold" %}
report_timing -delay min -max_paths {{ max_paths }} -nworst {{ nworst }}
{% else %}
report_timing -max_paths {{ max_paths }} -nworst {{ nworst }}
{% endif %}

# Report violations
report_constraint -all_violators

# Generate reports
report_timing -delay max > {{ output_dir }}/timing_setup.rpt
report_timing -delay min > {{ output_dir }}/timing_hold.rpt
report_constraint > {{ output_dir }}/constraints.rpt

# Exit
quit
"""

SPYGLASS_LINT_TEMPLATE = """
# SpyGlass Lint Analysis Script
# Generated: {{ timestamp }}
# Project: {{ project_name }}

# Set working directory
set_option top {{ top_module }}
set_option enableSV09 yes
set_option language_mode {{ language_mode }}

# Read design files
{% for file in design_files %}
read_file -type verilog {{ file | format_path }}
{% endfor %}

# Read lint rules
{% for goal in lint_goals %}
current_goal {{ goal }} -top {{ top_module }}
{% endfor %}

# Run lint
run_goal

# Generate reports
{% for goal in lint_goals %}
save_result {{ output_dir }}/{{ goal }}.rpt -goal {{ goal }}
{% endfor %}

# Save design data
save_design {{ output_dir }}/design_data.db

# Exit
exit
"""

MAKEFILE_TEMPLATE = """
# Makefile for {{ project_name }}
# Generated: {{ timestamp }}

# Variables
TOP_MODULE = {{ top_module }}
RTL_DIR = {{ rtl_dir | format_path }}
OUTPUT_DIR = {{ output_dir | format_path }}
TOOL = {{ tool_name }}

# File lists
RTL_FILES = {% for file in rtl_files %}\\
    {{ file | format_path }}{% if not loop.last %} \\{% endif %}
{% endfor %}

# Targets
.PHONY: all clean lint synthesis timing

all: lint synthesis timing

lint:
\t@echo "Running lint check..."
\t{{ tool_command }} {{ lint_script }}

synthesis:
\t@echo "Running synthesis..."
\t{{ tool_command }} {{ synthesis_script }}

timing:
\t@echo "Running timing analysis..."
\t{{ tool_command }} {{ timing_script }}

clean:
\t@echo "Cleaning output directory..."
\trm -rf $(OUTPUT_DIR)/*

# Report targets
report:
\t@echo "Generating summary report..."
\t@cat $(OUTPUT_DIR)/*.rpt > $(OUTPUT_DIR)/summary.txt
"""

FUSION_COMPILER_TEMPLATE = """
# Fusion Compiler Synthesis Script
# Generated: {{ timestamp }}

# Setup
set_app_var target_library "{{ target_library }}"
set_app_var link_library "* {{ link_library | format_list }}"

# Read RTL
{% for file in rtl_files %}
read_verilog -rtl {{ file | format_path }}
{% endfor %}

# Elaborate design
elaborate {{ top_module }}
link

# Read constraints
read_sdc {{ sdc_file | format_path }}

# Set optimization goals
{% if optimize_power %}
set_app_var power_keep_license_after_run true
{% endif %}

{% if optimize_area %}
set_max_area {{ max_area }}
{% endif %}

# Compile
compile_ultra {% if optimize_power %}-gate_clock{% endif %}

# Reports
report_timing > {{ output_dir }}/timing.rpt
report_area > {{ output_dir }}/area.rpt
report_power > {{ output_dir }}/power.rpt
report_qor > {{ output_dir }}/qor.rpt

# Write outputs
write_verilog {{ output_dir }}/{{ top_module }}_synth.v
write_sdc {{ output_dir }}/{{ top_module }}_synth.sdc

# Save database
write -format ddc -output {{ output_dir }}/{{ top_module }}.ddc

# Exit
exit
"""


def create_default_templates(template_dir: str) -> TemplateEngine:
    """
    기본 템플릿이 등록된 TemplateEngine 생성
    
    Args:
        template_dir: 템플릿 디렉토리
    
    Returns:
        TemplateEngine 인스턴스
    """
    engine = TemplateEngine(template_dir)
    
    # 기본 템플릿 등록
    engine.register_template("primetime_sta", PRIMETIME_STA_TEMPLATE)
    engine.register_template("spyglass_lint", SPYGLASS_LINT_TEMPLATE)
    engine.register_template("makefile", MAKEFILE_TEMPLATE)
    engine.register_template("fusion_compiler", FUSION_COMPILER_TEMPLATE)
    
    return engine


# 예제 컨텍스트 (LLM이 생성할 JSON 형식)

EXAMPLE_PRIMETIME_CONTEXT = {
    "target_module": "dma_controller",
    "search_path": "./lib ./rtl",
    "link_library": ["* slow.db", "fast.db"],
    "target_library": "slow.db",
    "netlist_path": "./output/dma_controller_synth.v",
    "sdc_path": "./constraints/dma_controller.sdc",
    "analysis_mode": "setup",
    "max_paths": 100,
    "nworst": 10,
    "output_dir": "./reports/timing"
}

EXAMPLE_SPYGLASS_CONTEXT = {
    "project_name": "my_soc",
    "top_module": "top",
    "language_mode": "verilog",
    "design_files": [
        "./rtl/top.v",
        "./rtl/dma_controller.v",
        "./rtl/fifo.v"
    ],
    "lint_goals": ["lint/lint_rtl", "cdc/cdc_setup_check"],
    "output_dir": "./reports/lint"
}

EXAMPLE_MAKEFILE_CONTEXT = {
    "project_name": "SoC_Design",
    "top_module": "soc_top",
    "rtl_dir": "./rtl",
    "output_dir": "./build",
    "tool_name": "dc_shell",
    "rtl_files": ["./rtl/top.v", "./rtl/cpu.v", "./rtl/mem.v"],
    "tool_command": "dc_shell-xg-t -f",
    "lint_script": "./scripts/lint.tcl",
    "synthesis_script": "./scripts/synthesis.tcl",
    "timing_script": "./scripts/timing.tcl"
}
