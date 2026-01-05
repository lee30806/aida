"""
RTL Agent System - Usage Examples
실제 사용 예제
"""
import asyncio
from pathlib import Path

from main import RTLAgentSystem
from core.base import Task, TaskType


async def example_basic_usage():
    """기본 사용 예제"""
    print("="*60)
    print("Example 1: Basic Usage")
    print("="*60)
    
    # 시스템 초기화
    system = RTLAgentSystem(
        workspace_dir='./workspace',
        config={
            'dry_run': True,  # 실제 툴을 실행하지 않음
            'max_concurrent': 2
        }
    )
    
    # RTL 파일 인덱싱 (실제 RTL 디렉토리 경로 필요)
    # await system.initialize(rtl_dirs=['./rtl_design'])
    await system.initialize()
    
    # 자연어 명령 실행
    result = await system.execute_command("DMA 모듈의 타이밍 위반을 분석해줘")
    
    print(f"\nResult: {result.success}")
    print(f"Summary: {result.summary}")
    if result.errors:
        print(f"Errors: {result.errors}")
    if result.recommendations:
        print(f"Recommendations: {result.recommendations}")
    
    # 통계 출력
    stats = system.get_statistics()
    print(f"\nSystem Statistics:")
    print(f"  - Executions: {stats['execution_count']}")
    print(f"  - KG Nodes: {stats['knowledge_graph']['nodes']}")
    print(f"  - KG Edges: {stats['knowledge_graph']['edges']}")


async def example_timing_analysis():
    """타이밍 분석 예제"""
    print("\n" + "="*60)
    print("Example 2: Timing Analysis")
    print("="*60)
    
    system = RTLAgentSystem(
        workspace_dir='./workspace',
        config={'dry_run': True}
    )
    
    await system.initialize()
    
    # 타이밍 분석
    result = await system.analyze_timing(
        module_name='dma_controller',
        netlist_path='./netlist/dma_controller_synth.v',
        sdc_path='./constraints/dma_controller.sdc'
    )
    
    print(f"\nTiming Analysis Result:")
    print(f"  - Success: {result.success}")
    print(f"  - Summary: {result.summary}")
    
    if 'violations' in result.details:
        violations = result.details['violations']
        print(f"  - Violations: {len(violations)}")
        for v in violations[:3]:  # 상위 3개만
            print(f"    * Slack: {v['slack']:.2f} ns ({v['path_type']})")


async def example_knowledge_graph():
    """Knowledge Graph 사용 예제"""
    print("\n" + "="*60)
    print("Example 3: Knowledge Graph")
    print("="*60)
    
    from knowledge.knowledge_graph import DesignKnowledgeGraph
    
    kg = DesignKnowledgeGraph()
    
    # 샘플 RTL 코드 생성
    sample_rtl = """
module dma_controller (
    input clk,
    input rst_n,
    input [31:0] addr,
    output reg [31:0] data
);

    reg [31:0] buffer;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data <= 32'h0;
        else
            data <= buffer;
    end
    
    fifo_buffer fifo_inst (
        .clk(clk),
        .data_in(addr),
        .data_out(buffer)
    );

endmodule

module fifo_buffer (
    input clk,
    input [31:0] data_in,
    output [31:0] data_out
);
    // FIFO implementation
endmodule
"""
    
    # 임시 파일로 저장
    rtl_path = Path('./workspace/sample.v')
    rtl_path.parent.mkdir(parents=True, exist_ok=True)
    rtl_path.write_text(sample_rtl)
    
    # RTL 파싱
    nodes = await kg.parse_rtl_file(str(rtl_path))
    print(f"\nParsed {len(nodes)} nodes from RTL")
    
    # 모듈 계층 분석
    hierarchy = kg.get_module_hierarchy('dma_controller')
    print(f"\nModule Hierarchy:")
    print_hierarchy(hierarchy, indent=0)
    
    # 의존성 분석
    dependencies = kg.analyze_dependencies()
    print(f"\nModule Dependencies:")
    for module, deps in dependencies.items():
        print(f"  {module} -> {deps}")
    
    # 서브그래프 추출
    subgraph = kg.get_module_context('dma_controller', depth=2)
    print(f"\nContext Subgraph: {len(subgraph.nodes)} nodes, {len(subgraph.edges)} edges")


def print_hierarchy(hierarchy: dict, indent: int = 0):
    """계층 구조 출력"""
    if not hierarchy:
        return
    
    prefix = "  " * indent
    print(f"{prefix}- {hierarchy.get('name', 'unknown')}")
    
    for child in hierarchy.get('children', []):
        print_hierarchy(child, indent + 1)


async def example_rag_engine():
    """RAG Engine 사용 예제"""
    print("\n" + "="*60)
    print("Example 4: RAG Engine")
    print("="*60)
    
    from knowledge.rag_engine import RAGEngine, VectorStore
    
    rag = RAGEngine(VectorStore())
    
    # 샘플 문서 추가
    documents = [
        ("PrimeTime supports both setup and hold timing analysis", 
         {'tool': 'PrimeTime', 'category': 'timing'}),
        ("SpyGlass provides comprehensive lint checking for RTL code",
         {'tool': 'SpyGlass', 'category': 'verification'}),
        ("Clock gating is an effective technique for power reduction",
         {'category': 'power'}),
        ("Pipeline stages can help meet timing constraints",
         {'category': 'optimization'}),
    ]
    
    for content, metadata in documents:
        await rag.vector_store.store(f"doc_{len(rag.vector_store.documents)}", 
                                     content, metadata)
    
    print(f"Indexed {len(documents)} documents")
    
    # 검색 테스트
    queries = [
        "timing analysis tools",
        "power optimization techniques",
        "RTL verification"
    ]
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        results = await rag.search_knowledge(query, limit=2)
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['content']} (score: {result['score']:.3f})")


async def example_template_engine():
    """Template Engine 사용 예제"""
    print("\n" + "="*60)
    print("Example 5: Template Engine")
    print("="*60)
    
    from execution.template_engine import create_default_templates
    
    engine = create_default_templates('./workspace/templates')
    
    # PrimeTime 스크립트 생성
    context = {
        'target_module': 'cpu_core',
        'search_path': './lib ./rtl',
        'link_library': ['slow.db', 'fast.db'],
        'target_library': 'slow.db',
        'netlist_path': './netlist/cpu_core.v',
        'sdc_path': './constraints/cpu_core.sdc',
        'analysis_mode': 'setup',
        'max_paths': 50,
        'nworst': 5,
        'output_dir': './reports'
    }
    
    script = engine.render('primetime_sta', context)
    
    print("\nGenerated PrimeTime Script:")
    print("-" * 60)
    print(script[:500] + "...")  # 처음 500자만 출력
    
    # Makefile 생성
    makefile_context = {
        'project_name': 'CPU_Design',
        'top_module': 'cpu_core',
        'rtl_dir': './rtl',
        'output_dir': './build',
        'tool_name': 'dc_shell',
        'rtl_files': ['./rtl/core.v', './rtl/alu.v', './rtl/regfile.v'],
        'tool_command': 'dc_shell-xg-t -f',
        'lint_script': './scripts/lint.tcl',
        'synthesis_script': './scripts/synthesis.tcl',
        'timing_script': './scripts/timing.tcl'
    }
    
    makefile = engine.render('makefile', makefile_context)
    
    print("\nGenerated Makefile:")
    print("-" * 60)
    print(makefile[:500] + "...")


async def example_feedback_loop():
    """피드백 루프 예제"""
    print("\n" + "="*60)
    print("Example 6: Feedback Loop with Self-Correction")
    print("="*60)
    
    system = RTLAgentSystem(
        workspace_dir='./workspace',
        config={'dry_run': True}
    )
    
    await system.initialize()
    
    # 문제가 있는 작업 생성
    task = Task(
        task_id='test_task',
        task_type=TaskType.TIMING_ANALYSIS,
        description='Analyze timing violations',
        context={
            'module': 'test_module',
            'log_path': './workspace/logs/test.log'
        }
    )
    
    # 피드백 루프 실행
    result = await system.run_with_feedback(task, max_iterations=3)
    
    print(f"\nFeedback Loop Result:")
    print(f"  - Success: {result.success}")
    print(f"  - Summary: {result.summary}")
    print(f"  - Iterations: Check ./workspace/reports/ for history")


async def main():
    """모든 예제 실행"""
    try:
        await example_basic_usage()
        await example_timing_analysis()
        await example_knowledge_graph()
        await example_rag_engine()
        await example_template_engine()
        await example_feedback_loop()
        
        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
