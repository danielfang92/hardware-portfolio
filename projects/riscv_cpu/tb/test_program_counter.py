"""testbenches for RV32I program counter"""
# TO RUN IN MAKEFILE: make MODULE=test_program_counter TOPLEVEL=program_counter VERILOG_SOURCES=../rtl/program_counter.sv
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

async def setup (dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.rst_n.value = 0
    await Timer (1, unit="ns")
    dut.rst_n.value = 1
    await Timer (1, unit="ns")

@cocotb.test()
async def test_pc_resets_to_zero(dut):
#Verify that asserting reset clears pc to 0
    await setup(dut)
    assert dut.pc.value == 0, f"After reset, pc should be 0, got {int(dut.pc.value)}"
    
@cocotb.test()
async def test_pc_increments(dut):
#Verify that pc increments by 4 every clock cycle
    await setup(dut)
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert dut.pc.value == 4, f"After 1 clock cycle, pc should be 4, got {int(dut.pc.value)}"
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    assert dut.pc.value == 8, f"After 2 clock cycles, pc should be 8, got {int(dut.pc.value)}"
    


