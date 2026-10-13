"""cocotb testbench for the single-cycle RISC-V CPU"""
# Run with: make cpu   (from projects/riscv_cpu/tb/)
#
# Programs go in through the imem write port while reset is held, and every
# check reads the write-back (commit) port. The one backdoor left is zeroing
# the register file in start_and_reset, see there for why.
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer


#Helper functions
def make_r_type(funct7, rs2, rs1, funct3, rd, opcode):
#Make an R-type instruction
    return (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | (opcode << 0)

def make_i_type(imm, rs1, funct3, rd, opcode):
#Make an I-type instruction. imm is a 12-bit signed value; mask to 12 bits.
    return ((imm & 0xFFF) << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | (opcode << 0)

def addi(rd, rs1, imm):
    return make_i_type(imm=imm, rs1=rs1, funct3=0b000, rd=rd, opcode=0b0010011)

def add(rd, rs1, rs2):
    return make_r_type(funct7=0b0000000, rs2=rs2, rs1=rs1, funct3=0b000, rd=rd, opcode=0b0110011)

def sub(rd, rs1, rs2):
    return make_r_type(funct7=0b0100000, rs2=rs2, rs1=rs1, funct3=0b000, rd=rd, opcode=0b0110011)

def and_(rd, rs1, rs2):
    return make_r_type(funct7=0b0000000, rs2=rs2, rs1=rs1, funct3=0b111, rd=rd, opcode=0b0110011)

IMEM_WORDS = 64

async def start_and_reset(dut):
    """Start the clock, assert reset, and clear the register file.

    All tests in this file share one simulation, and the regfile has no reset
    (it's distributed RAM), so without the clear a value from one test leaks
    into the next. This is the only backdoor write left in the CPU tests: it
    stands in for software zeroing registers at boot, which this core can't
    do yet without loads.
    """
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst_n.value = 0
    dut.imem_we.value = 0
    dut.imem_waddr.value = 0
    dut.imem_wdata.value = 0
    for i in range(32):
        dut.u_regfile.registers[i].value = 0
    await RisingEdge(dut.clk)

async def load_program(dut, instructions):
    """Write a program through the imem write port, one word per clock.

    Call while reset is held. Every slot after the program is written with 0,
    so nothing left over from imem's power-on contents (or a previous test)
    can run.
    """
    words = instructions + [0] * (IMEM_WORDS - len(instructions))
    for i, instr in enumerate(words):
        dut.imem_we.value = 1
        dut.imem_waddr.value = i
        dut.imem_wdata.value = instr
        await RisingEdge(dut.clk)
    dut.imem_we.value = 0
    await Timer(1, unit="ns")

async def monitor_writeback(dut, trace):
    """Record every register write the CPU reports on its commit port.

    Samples on the FALLING edge: in a single-cycle core the current
    instruction's write-back signals are combinational, so mid-cycle they have
    settled and describe the write that the next rising edge will commit.
    Only the ports are read here, never dut.u_regfile, so this checks what the
    outside world (and synthesis) can actually see.
    """
    while True:
        await FallingEdge(dut.clk)
        if dut.rst_n.value == 1 and dut.wb_en_o.value == 1:
            trace.append((int(dut.pc_o.value),
                          int(dut.wb_rd_o.value),
                          int(dut.wb_data_o.value)))

async def run_cycles(dut, n):
    """Release reset, run n clock cycles, return the commit trace.

    Each trace entry is (pc, rd, data) for one register write, in order.
    """
    trace = []
    cocotb.start_soon(monitor_writeback(dut, trace))
    dut.rst_n.value = 1
    for _ in range(n):
        await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    return trace

async def check_program(dut, program, cycles, expected):
    """Reset, load, run, and compare the full commit trace."""
    await start_and_reset(dut)
    await load_program(dut, program)
    trace = await run_cycles(dut, cycles)
    assert trace == expected, f"commit trace wrong: expected {expected}, got {trace}"


@cocotb.test()
async def test_r_type_program(dut):
    """x1=10, x2=3: add->13, sub->7, and->2"""
    await check_program(dut, [
        addi(1, 0, 10),
        addi(2, 0, 3),
        add(3, 1, 2),
        sub(4, 1, 2),
        and_(5, 1, 2),
    ], cycles=6, expected=[(0, 1, 10), (4, 2, 3), (8, 3, 13), (12, 4, 7), (16, 5, 2)])

@cocotb.test()
async def test_dependent_instructions(dut):
    """A value written by one instruction is readable by the next.

    sub x3, x1, x2   x3 = 5 - 2 = 3
    add x4, x3, x2   x4 = 3 + 2 = 5   (reads x3 written the cycle before)"""
    await check_program(dut, [
        addi(1, 0, 5),
        addi(2, 0, 2),
        sub(3, 1, 2),
        add(4, 3, 2),
    ], cycles=5, expected=[(0, 1, 5), (4, 2, 2), (8, 3, 3), (12, 4, 5)])

@cocotb.test()
async def test_x0_stays_zero(dut):
    """x0 is not writable, and reads as zero through the datapath.

        add x0, x1, x2    attempt to write x0
        add x3, x0, x0    read x0 twice; x3 should be 0

    The x0 write still appears on the commit port (it is a real instruction)
    but must report data 0, not the 7 the ALU computed.
    """
    await check_program(dut, [
        addi(1, 0, 5),
        addi(2, 0, 2),
        add(0, 1, 2),
        add(3, 0, 0),
    ], cycles=5, expected=[(0, 1, 5), (4, 2, 2), (8, 0, 0), (12, 3, 0)])

@cocotb.test()
async def test_overrun_is_harmless(dut):
    """Running past the end of the program must not write any register.

    0x00000FFF and the zero-filled slots after it decode as neither R-type nor
    OP-IMM, so control should hold reg_write low. Checking the full trace
    proves NO register was written after the add, not just that one survived.
    """
    await check_program(dut, [
        addi(1, 0, 5),
        addi(2, 0, 2),
        add(3, 1, 2),
        0x00000FFF,
        0x00000FFF,
    ], cycles=20, expected=[(0, 1, 5), (4, 2, 2), (8, 3, 7)])

@cocotb.test()
async def test_i_type_program(dut):
    """I-type immediates end to end.

    addi x1, x0, 5     x1 = 0 + 5    = 5
    addi x2, x1, 3     x2 = 5 + 3    = 8   (reads x1 written the cycle before)
    addi x3, x1, -1    x3 = 5 + (-1) = 4   (negative imm, sign-extended)
    """
    await check_program(dut, [
        addi(1, 0, 5),
        addi(2, 1, 3),
        addi(3, 1, -1),
    ], cycles=5, expected=[(0, 1, 5), (4, 2, 8), (8, 3, 4)])

@cocotb.test()
async def test_no_writes_during_reset(dut):
    """Instruction 0 must not execute while reset is held.

    During reset the PC sits at 0, so instruction 0 is decoded on every edge,
    including all 64 edges of the program load. If register writes aren't
    blocked, addi x1, x1, 1 counts up once per reset cycle and the first real
    commit reports far more than 1.
    """
    await start_and_reset(dut)
    await load_program(dut, [addi(1, 1, 1)])
    for _ in range(5):                     # hold reset for 5 more edges
        await RisingEdge(dut.clk)
    trace = await run_cycles(dut, 1)
    expected = [(0, 1, 1)]
    assert trace == expected, f"commit trace wrong: expected {expected}, got {trace}"
