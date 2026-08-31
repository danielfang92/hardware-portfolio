""""cocotb testbench for single-cyckle RISC-V CPU"""
#make MODULE=test_cpu TOPLEVEL=cpu VERILOG_SOURCES="$(pwd)/../rtl/riscv_pkg.sv $(pwd)/../rtl/program_counter.sv $(pwd)/../rtl/imem.sv $(pwd)/../rtl/decoder.sv $(pwd)/../rtl/control.sv $(pwd)/../rtl/regfile.sv $(pwd)/../../alu/rtl/alu.sv $(pwd)/../rtl/cpu.sv"
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


'''@cocotb.test()
async def test_compile(dut):
#Test that the CPU compiles and runs without errors
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await Timer (1, unit="ns")
    dut._log.info("CPU elaborated and clocked.")'''

#Helper functions
def make_r_type(funct7, rs2, rs1, funct3, rd, opcode):
#Make an R-type instruction
    return (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | (opcode << 0)

async def start_and_reset(dut):
#Start the clock and assert reset
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    

async def seed_register(dut, addr, value):
    """Write a register directly into the regfile's array.
    Bypasses the write port: rd_addr, rd_data and we are already driven by
    the decoder, ALU and control inside cpu.sv, so driving them from the
    testbench too would put X in those nets.
    Remove once addi exists"""
    dut.u_regfile.registers[addr].value = value
    await Timer (1, unit="ns")

async def run_cycles(dut, n):
    """Release reset and run n clock cycles."""
    dut.rst_n.value = 1
    for _ in range(n):
        await RisingEdge(dut.clk)
    await Timer(1, unit="ns")    
    
@cocotb.test()
async def test_r_type_program(dut):
    #x1=10, x2=3: add->13, sub->7, and->2
    await start_and_reset(dut)
    await seed_register (dut, 1, 10)
    await seed_register (dut, 2, 3)
    await run_cycles (dut, 4)
    assert dut.u_regfile.registers[3].value == 13, f"add result wrong: {int(dut.u_regfile.registers[3].value)}"
    assert dut.u_regfile.registers[4].value == 7, f"sub result wrong: {int(dut.u_regfile.registers[4].value)}"
    assert dut.u_regfile.registers[5].value == 2, f"and result wrong: {int(dut.u_regfile.registers[5].value)}"
    
    



                            