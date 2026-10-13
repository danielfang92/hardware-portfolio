"""cocotb testbench for RV32I control unit (R-type only)"""
# Run with: make control   (from projects/riscv_cpu/tb/)
import cocotb
from cocotb.triggers import Timer

# must match riscv_pkg.sv
ALU_ADD, ALU_SUB, ALU_AND, ALU_OR, ALU_XOR = 0, 1, 2, 3, 4
ALU_SLL, ALU_SRL, ALU_SRA, ALU_SLT, ALU_SLTU = 5, 6, 7, 8, 9

R_TYPE = 0b0110011
I_TYPE = 0b0010011

OP_NAMES = {
    ALU_ADD: "ADD", ALU_SUB: "SUB", ALU_AND: "AND", ALU_OR: "OR",
    ALU_XOR: "XOR", ALU_SLL: "SLL", ALU_SRL: "SRL", ALU_SRA: "SRA",
    ALU_SLT: "SLT", ALU_SLTU: "SLTU",
}


async def check(dut, funct3, funct7, expected_op):
    """Drive one R-type instruction's control fields and check the decode."""
    dut.opcode.value = R_TYPE
    dut.funct3.value = funct3
    dut.funct7.value = funct7
    await Timer(1, unit="ns")

    got = int(dut.alu_op.value)
    assert got == expected_op, (
        f"funct3={funct3:03b} funct7={funct7:07b}: "
        f"expected {OP_NAMES[expected_op]}, got {OP_NAMES.get(got, got)}"
    )
    assert dut.reg_write.value == 1, (
        f"funct3={funct3:03b}: reg_write should be 1 for R-type, got "
        f"{int(dut.reg_write.value)}"
    )
    assert dut.alu_src.value == 0, (
        f"funct3={funct3:03b}: alu_src should be 0 for R-type (operand_b=rs2), got "
        f"{int(dut.alu_src.value)}"
    )


async def check_i(dut, funct3, funct7, expected_op):
    """Drive one I-type (OP-IMM) instruction's control fields and check the decode."""
    dut.opcode.value = I_TYPE
    dut.funct3.value = funct3
    dut.funct7.value = funct7
    await Timer(1, unit="ns")

    got = int(dut.alu_op.value)
    assert got == expected_op, (
        f"funct3={funct3:03b} funct7={funct7:07b}: "
        f"expected {OP_NAMES[expected_op]}, got {OP_NAMES.get(got, got)}"
    )
    assert dut.reg_write.value == 1, (
        f"funct3={funct3:03b}: reg_write should be 1 for I-type, got "
        f"{int(dut.reg_write.value)}"
    )
    assert dut.alu_src.value == 1, (
        f"funct3={funct3:03b}: alu_src should be 1 for I-type (operand_b=imm), got "
        f"{int(dut.alu_src.value)}"
    )


@cocotb.test()
async def test_all_r_type_ops(dut):
    """Every R-type funct3/funct7 combination maps to the right ALU op."""
    await check(dut, 0b000, 0b0000000, ALU_ADD)
    await check(dut, 0b000, 0b0100000, ALU_SUB)   # funct7 distinguishes SUB
    await check(dut, 0b001, 0b0000000, ALU_SLL)
    await check(dut, 0b010, 0b0000000, ALU_SLT)
    await check(dut, 0b011, 0b0000000, ALU_SLTU)
    await check(dut, 0b100, 0b0000000, ALU_XOR)
    await check(dut, 0b101, 0b0000000, ALU_SRL)
    await check(dut, 0b101, 0b0100000, ALU_SRA)   # funct7 distinguishes SRA
    await check(dut, 0b110, 0b0000000, ALU_OR)
    await check(dut, 0b111, 0b0000000, ALU_AND)

    dut._log.info("All 10 R-type operations decoded correctly.")


@cocotb.test()
async def test_all_i_type_ops(dut):
    """Every OP-IMM funct3 maps to the right ALU op, with alu_src high."""
    await check_i(dut, 0b000, 0b0000000, ALU_ADD)   # ADDI
    await check_i(dut, 0b000, 0b0100000, ALU_ADD)   # funct7 set, still ADDI (no SUBI)
    await check_i(dut, 0b010, 0b0000000, ALU_SLT)   # SLTI
    await check_i(dut, 0b011, 0b0000000, ALU_SLTU)  # SLTIU
    await check_i(dut, 0b100, 0b0000000, ALU_XOR)   # XORI
    await check_i(dut, 0b110, 0b0000000, ALU_OR)    # ORI
    await check_i(dut, 0b111, 0b0000000, ALU_AND)   # ANDI
    await check_i(dut, 0b001, 0b0000000, ALU_SLL)   # SLLI
    await check_i(dut, 0b101, 0b0000000, ALU_SRL)   # SRLI
    await check_i(dut, 0b101, 0b0100000, ALU_SRA)   # SRAI (funct7 distinguishes)

    dut._log.info("All I-type (OP-IMM) operations decoded correctly.")


@cocotb.test()
async def test_unimplemented_opcode_no_write(dut):
    """An opcode the control unit does not decode must hold reg_write low.

    0b0000000 is the zero-fill word fetched past the end of a program; it is
    not a legal opcode, so nothing should be written. (I-type now legitimately
    writes, so it is no longer a valid 'does-not-write' example.)
    """
    dut.opcode.value = 0b0000000
    dut.funct3.value = 0b000
    dut.funct7.value = 0b0000000
    await Timer(1, unit="ns")
    assert dut.reg_write.value == 0, (
        f"reg_write must be 0 for an unimplemented opcode, got "
        f"{int(dut.reg_write.value)}"
    )