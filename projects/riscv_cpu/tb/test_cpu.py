""""cocotb testbench for single-cyckle RISC-V CPU"""
#make MODULE=test_cpu TOPLEVEL=cpu VERILOG_SOURCES="$(pwd)/../rtl/riscv_pkg.sv $(pwd)/../rtl/program_counter.sv $(pwd)/../rtl/imem.sv $(pwd)/../rtl/decoder.sv $(pwd)/../rtl/control.sv $(pwd)/../rtl/regfile.sv $(pwd)/../../alu/rtl/alu.sv $(pwd)/../rtl/cpu.sv"
#remmber test_r_type_program doesn't call load_program, relies on imem from RTL
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
    
async def load_program(dut, instructions):
    """Overwrite imem with a program, one word per slot."""
    for i, instr in enumerate(instructions):
        dut.u_imem.mem[i].value = instr
    await Timer(1, unit="ns")
    
@cocotb.test()
async def test_r_type_program(dut):
    #x1=10, x2=3: add->13, sub->7, and->2
    await start_and_reset(dut)
    await seed_register (dut, 1, 10)
    await seed_register (dut, 2, 3)
    await run_cycles (dut, 4)
    assert dut.u_regfile.registers[3].value == 13, f"add result wrong: {(dut.u_regfile.registers[3].value)}"
    assert dut.u_regfile.registers[4].value == 7, f"sub result wrong: {(dut.u_regfile.registers[4].value)}"
    assert dut.u_regfile.registers[5].value == 2, f"and result wrong: {(dut.u_regfile.registers[5].value)}"
    
@cocotb.test()
async def test_dependent_instructions(dut):   
    """A value written by one instruction is readable by the next.

    sub x3, x1, x2   x3 = 5 - 2 = 3
    add x4, x3, x2   x4 = 3 + 2 = 5   (reads x3 written the cycle before)"""
    
    await start_and_reset(dut)
    await load_program(dut, [
    make_r_type(funct7=0b0100000, rs2=2, rs1=1, funct3=0b000, rd=3, opcode=0b0110011),
    make_r_type(funct7=0b0000000, rs2=2, rs1=3, funct3=0b000, rd=4, opcode=0b0110011),
    ])
    await seed_register (dut, 1, 5)
    await seed_register (dut, 2, 2)
    await run_cycles (dut, 4)
    assert dut.u_regfile.registers[3].value == 3, f"sub result wrong: {(dut.u_regfile.registers[3].value)}"
    assert dut.u_regfile.registers[4].value == 5, f"add result wrong: {(dut.u_regfile.registers[4].value)}"

@cocotb.test()
async def test_x0_stays_zero(dut):
    """x0 is not writable, and reads as zero through the datapath.

        add x0, x1, x2    attempt to write x0
        add x3, x0, x0    read x0 twice; x3 should be 0

    Reading through the program rather than inspecting registers[0]
    directly, because with no reset that slot holds X whether or not
    the write was blocked.
    """
    await start_and_reset(dut)
    await load_program(dut, [
        # add x0, x1, x2   — rd=0, rs1=1, rs2=2
        make_r_type(funct7=0b0000000, rs2=2, rs1=1, funct3=0b000, rd=0, opcode=0b0110011),
        # add x3, x0, x0   — rd=3, rs1=0, rs2=0
        make_r_type(funct7=0b0000000, rs2=0, rs1=0, funct3=0b000, rd=3, opcode=0b0110011),
    ])
    await seed_register(dut, 1, 5)
    await seed_register(dut, 2, 2)
    await run_cycles(dut, 4)
    assert dut.u_regfile.registers[3].value == 0, \
        f"x0 did not read as zero: x3 = {dut.u_regfile.registers[3].value}"
    

@cocotb.test()
async def test_overrun_is_harmless(dut):
    """Running past the end of the program must not corrupt registers.

    imem is zero-filled, so fetching past the program returns 32'h00000000.
    Opcode 0000000 is not R-type, so control should hold reg_write low and
    nothing should be written.
    """
    await start_and_reset(dut)
    await load_program(dut, [
        # add x3, x1, x2, then nothing
        make_r_type(funct7=0b0000000, rs2=2, rs1=1, funct3=0b000, rd=3, opcode=0b0110011),
        0x00000FFF,
        0x00000FFF,
    ])
    await seed_register(dut, 1, 5)
    await seed_register(dut, 2, 2)
    await seed_register(dut, 31, 0xABCD)     # nothing should ever overwrite x31
    await run_cycles(dut, 20)
    assert dut.u_regfile.registers[3].value == 7, \
        f"add result wrong: {dut.u_regfile.registers[3].value}"
    assert dut.u_regfile.registers[31].value == 0xABCD, \
        f"x31 corrupted by overrun: {dut.u_regfile.registers[31].value}"                       