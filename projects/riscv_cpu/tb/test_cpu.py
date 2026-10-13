"""cocotb testbench for the single-cycle RISC-V CPU"""
# Run with: make cpu   (from projects/riscv_cpu/tb/)
# remember: test_r_type_program doesn't call load_program, relies on imem from RTL
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer


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

def make_i_type(imm, rs1, funct3, rd, opcode):
#Make an I-type instruction. imm is a 12-bit signed value; mask to 12 bits.
    return ((imm & 0xFFF) << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | (opcode << 0)

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

IMEM_WORDS = 64

async def load_program(dut, instructions):
    """Overwrite imem with a program, zero-filling every slot after it.

    Zero-fill matters: imem.sv's initial block preloads add/sub/and in slots
    0-2. A shorter program would otherwise fall through into those leftovers
    and run them, and a full-trace check would (correctly) see the extra write.
    """
    words = instructions + [0] * (IMEM_WORDS - len(instructions))
    for i, instr in enumerate(words):
        dut.u_imem.mem[i].value = instr
    await Timer(1, unit="ns")
    
@cocotb.test()
async def test_r_type_program(dut):
    #x1=10, x2=3: add->13, sub->7, and->2
    await start_and_reset(dut)
    await seed_register (dut, 1, 10)
    await seed_register (dut, 2, 3)
    trace = await run_cycles(dut, 4)
    expected = [(0, 3, 13), (4, 4, 7), (8, 5, 2)]
    assert trace == expected, f"commit trace wrong: expected {expected}, got {trace}"
    
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
    trace = await run_cycles(dut, 4)
    expected = [(0, 3, 3), (4, 4, 5)]
    assert trace == expected, f"commit trace wrong: expected {expected}, got {trace}"

@cocotb.test()
async def test_x0_stays_zero(dut):
    """x0 is not writable, and reads as zero through the datapath.

        add x0, x1, x2    attempt to write x0
        add x3, x0, x0    read x0 twice; x3 should be 0

    Reading through the program rather than inspecting registers[0]
    directly, because with no reset that slot holds X whether or not
    the write was blocked.

    The x0 write still appears on the commit port (it is a real instruction)
    but must report data 0, not the 7 the ALU computed.
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
    trace = await run_cycles(dut, 4)
    expected = [(0, 0, 0), (4, 3, 0)]
    assert trace == expected, f"commit trace wrong: expected {expected}, got {trace}"
    

@cocotb.test()
async def test_overrun_is_harmless(dut):
    """Running past the end of the program must not corrupt registers.

    imem is zero-filled, so fetching past the program returns 32'h00000000.
    Opcode 0000000 is neither R-type nor OP-IMM, so control should hold
    reg_write low and nothing should be written. Checking the full trace is
    stronger than spot-checking x31: it proves NO register was written after
    the add, not just that one register survived.
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
    trace = await run_cycles(dut, 20)
    expected = [(0, 3, 7)]
    assert trace == expected, f"commit trace wrong: expected {expected}, got {trace}"

@cocotb.test()
async def test_i_type_program(dut):
    """I-type immediates run end to end with NO register seeding.

    addi x1, x0, 5     x1 = 0 + 5    = 5
    addi x2, x1, 3     x2 = 5 + 3    = 8   (reads x1 written the cycle before)
    addi x3, x1, -1    x3 = 5 + (-1) = 4   (negative imm, sign-extended)
    """
    await start_and_reset(dut)
    await load_program(dut, [
        make_i_type(imm=5,  rs1=0, funct3=0b000, rd=1, opcode=0b0010011),
        make_i_type(imm=3,  rs1=1, funct3=0b000, rd=2, opcode=0b0010011),
        make_i_type(imm=-1, rs1=1, funct3=0b000, rd=3, opcode=0b0010011),
    ])
    trace = await run_cycles(dut, 5)
    expected = [(0, 1, 5), (4, 2, 8), (8, 3, 4)]
    assert trace == expected, f"commit trace wrong: expected {expected}, got {trace}"