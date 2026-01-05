#!/usr/bin/env python3
"""
RTL Agent System - Quick Start Script
빠른 시작을 위한 스크립트
"""
import asyncio
import sys
from pathlib import Path


def print_banner():
    """배너 출력"""
    banner = """
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     RTL Agent System - Quick Start                      ║
    ║     Autonomous RTL Analysis & Optimization               ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """
    print(banner)


async def setup_workspace():
    """워크스페이스 설정"""
    print("\n[1/4] Setting up workspace...")
    
    workspace = Path('./workspace')
    workspace.mkdir(exist_ok=True)
    
    dirs = ['knowledge', 'templates', 'scripts', 'reports', 'logs', 'rtl_sample']
    for dir_name in dirs:
        (workspace / dir_name).mkdir(exist_ok=True)
    
    print(f"  ✓ Workspace created at: {workspace.absolute()}")
    return str(workspace)


async def create_sample_rtl():
    """샘플 RTL 코드 생성"""
    print("\n[2/4] Creating sample RTL files...")
    
    sample_rtl = """
// Sample DMA Controller
module dma_controller (
    input wire clk,
    input wire rst_n,
    input wire [31:0] src_addr,
    input wire [31:0] dst_addr,
    input wire [15:0] length,
    input wire start,
    output reg done,
    output reg error
);

    // State machine
    localparam IDLE = 2'b00;
    localparam TRANSFER = 2'b01;
    localparam FINISH = 2'b10;
    
    reg [1:0] state;
    reg [15:0] counter;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            done <= 1'b0;
            error <= 1'b0;
            counter <= 16'h0;
        end else begin
            case (state)
                IDLE: begin
                    if (start) begin
                        state <= TRANSFER;
                        counter <= 16'h0;
                        done <= 1'b0;
                    end
                end
                
                TRANSFER: begin
                    counter <= counter + 1'b1;
                    if (counter >= length) begin
                        state <= FINISH;
                    end
                end
                
                FINISH: begin
                    done <= 1'b1;
                    state <= IDLE;
                end
            endcase
        end
    end
    
    // FIFO instance
    fifo_buffer #(.DEPTH(16)) fifo_inst (
        .clk(clk),
        .rst_n(rst_n),
        .wr_en(state == TRANSFER),
        .rd_en(state == TRANSFER),
        .data_in(src_addr),
        .data_out(),
        .full(),
        .empty()
    );

endmodule

// FIFO Buffer
module fifo_buffer #(
    parameter DEPTH = 16
)(
    input wire clk,
    input wire rst_n,
    input wire wr_en,
    input wire rd_en,
    input wire [31:0] data_in,
    output reg [31:0] data_out,
    output wire full,
    output wire empty
);

    reg [31:0] memory [0:DEPTH-1];
    reg [$clog2(DEPTH):0] wr_ptr;
    reg [$clog2(DEPTH):0] rd_ptr;
    
    assign full = (wr_ptr == {~rd_ptr[$clog2(DEPTH)], rd_ptr[$clog2(DEPTH)-1:0]});
    assign empty = (wr_ptr == rd_ptr);
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= 0;
            rd_ptr <= 0;
        end else begin
            if (wr_en && !full)
                wr_ptr <= wr_ptr + 1'b1;
            if (rd_en && !empty)
                rd_ptr <= rd_ptr + 1'b1;
        end
    end
    
    always @(posedge clk) begin
        if (wr_en && !full)
            memory[wr_ptr[$clog2(DEPTH)-1:0]] <= data_in;
    end
    
    always @(posedge clk) begin
        if (rd_en && !empty)
            data_out <= memory[rd_ptr[$clog2(DEPTH)-1:0]];
    end

endmodule
"""
    
    rtl_file = Path('./workspace/rtl_sample/dma_controller.v')
    rtl_file.write_text(sample_rtl)
    
    print(f"  ✓ Sample RTL created at: {rtl_file}")


async def initialize_system(workspace: str):
    """시스템 초기화"""
    print("\n[3/4] Initializing RTL Agent System...")
    
    try:
        from main import RTLAgentSystem
        
        system = RTLAgentSystem(
            workspace_dir=workspace,
            config={
                'dry_run': True,  # 실제 툴 실행 안함
                'max_concurrent': 2
            }
        )
        
        # RTL 인덱싱
        rtl_dir = str(Path(workspace) / 'rtl_sample')
        await system.initialize(rtl_dirs=[rtl_dir])
        
        print("  ✓ System initialized successfully")
        print(f"  ✓ Knowledge Graph: {len(system.knowledge_graph.graph.nodes)} nodes")
        
        return system
        
    except Exception as e:
        print(f"  ✗ Initialization failed: {e}")
        return None


async def run_demo(system):
    """데모 실행"""
    print("\n[4/4] Running demonstration...")
    
    if not system:
        print("  ✗ System not available")
        return
    
    # 샘플 명령어들
    commands = [
        "DMA 모듈의 구조를 분석해줘",
        "타이밍 최적화 방안을 제안해줘",
        "FIFO 버퍼의 깊이를 검증해줘"
    ]
    
    for i, command in enumerate(commands, 1):
        print(f"\n  Example {i}: {command}")
        try:
            result = await system.execute_command(command)
            print(f"    Status: {'✓ Success' if result.success else '✗ Failed'}")
            print(f"    Summary: {result.summary}")
            
            if result.recommendations:
                print(f"    Recommendations:")
                for rec in result.recommendations[:2]:
                    print(f"      - {rec}")
                    
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    # 통계 출력
    print("\n  System Statistics:")
    stats = system.get_statistics()
    print(f"    - Executions: {stats['execution_count']}")
    print(f"    - Modules indexed: {stats['knowledge_graph']['modules']}")
    print(f"    - Graph nodes: {stats['knowledge_graph']['nodes']}")
    print(f"    - Graph edges: {stats['knowledge_graph']['edges']}")
    
    # 상태 저장
    system.save_state()
    print(f"\n  ✓ System state saved to: {system.workspace}")


async def main():
    """메인 함수"""
    print_banner()
    
    try:
        # 1. 워크스페이스 설정
        workspace = await setup_workspace()
        
        # 2. 샘플 RTL 생성
        await create_sample_rtl()
        
        # 3. 시스템 초기화
        system = await initialize_system(workspace)
        
        # 4. 데모 실행
        await run_demo(system)
        
        print("\n" + "="*60)
        print("Quick start completed successfully!")
        print("="*60)
        print("\nNext steps:")
        print("  1. Check the workspace directory: ./workspace")
        print("  2. Review the generated reports: ./workspace/reports")
        print("  3. Run examples.py for more demonstrations")
        print("  4. Read README.md for detailed documentation")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
