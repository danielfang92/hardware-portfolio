"""Cocotb testbench for the 32-bit RV32I ALU.

Four layers, cheap to expensive:
  1. Reference model    - a pure-Python "golden" ALU we trust as the source of truth.
  2. Directed tests     - hand-picked edge cases (overflow, sign boundaries, shifts).
  3. Constrained-random - thousands of random (a, b, op) vectors: DUT vs model.
  4. Coverage           - prove we actually hit every op and every interesting corner.

Timing note: the ALU is purely combinational. No clock, no reset. We set the
inputs, wait a tiny Timer for the logic to settle, then read the outputs.
"""

import cocotb
from cocotb.triggers import Timer
import random


# Op encodings: must match the enum in alu.sv exactly.
ALU_ADD  = 0
ALU_SUB  = 1
ALU_AND  = 2
ALU_OR   = 3
ALU_XOR  = 4
ALU_SLL  = 5
ALU_SRL  = 6
ALU_SRA  = 7
ALU_SLT  = 8
ALU_SLTU = 9

ALL_OPS = {
    "ADD": ALU_ADD, "SUB": ALU_SUB, "AND": ALU_AND, "OR": ALU_OR,
    "XOR": ALU_XOR, "SLL": ALU_SLL, "SRL": ALU_SRL, "SRA": ALU_SRA,
    "SLT": ALU_SLT, "SLTU": ALU_SLTU,
}
OP_NAME = {code: name for name, code in ALL_OPS.items()}  # reverse lookup for messages

MASK32 = 0xFFFFFFFF  # force Python's arbitrary-width ints back down to 32 bits


def to_signed(val):
    """Reinterpret a 32-bit unsigned value as two's-complement signed."""
    if val >= 2**31:
        return val - 2**32
    else:
        return val


def alu_model(a, b, op):
    """Golden model: the result the hardware SHOULD produce for (a, b, op)."""
    shamt = b & 0x1F  # low 5 bits, same as operand_b[4:0] in the RTL

    if   op == ALU_ADD:  return (a + b) & MASK32
    elif op == ALU_SUB:  return (a - b) & MASK32
    elif op == ALU_AND:  return a & b
    elif op == ALU_OR:   return a | b
    elif op == ALU_XOR:  return a ^ b
    elif op == ALU_SLL:  return (a << shamt) & MASK32
    elif op == ALU_SRL:  return a >> shamt  # a is unsigned, so >> is logical
    elif op == ALU_SRA:  return (to_signed(a) >> shamt) & MASK32  # Python >> on a negative int sign-extends
    elif op == ALU_SLT:  return 1 if to_signed(a) < to_signed(b) else 0
    elif op == ALU_SLTU: return 1 if a < b else 0
    else:                return 0  # matches the RTL default case


async def apply_and_check(dut, a, b, op):
    """Drive one vector, let the combinational logic settle, compare to model."""
    dut.operand_a.value = a
    dut.operand_b.value = b
    dut.op.value = op
    await Timer(1, unit="ns")

    expected = alu_model(a, b, op)
    got = int(dut.result.value)
    assert got == expected, (
        f"{OP_NAME[op]}: a=0x{a:08X} b=0x{b:08X} "
        f"expected 0x{expected:08X}, got 0x{got:08X}"
    )

    expected_zero = 1 if expected == 0 else 0
    assert dut.zero.value == expected_zero, (
        f"{OP_NAME[op]}: a=0x{a:08X} b=0x{b:08X} result=0x{expected:08X} "
        f"expected zero={expected_zero}, got {int(dut.zero.value)}"
    )


@cocotb.test()
async def test_directed_edges(dut):
    """Hand-picked corner cases that random testing might take ages to hit."""
    vectors = [
        # (a, b, op)
        (0xFFFFFFFF, 0x00000001, ALU_ADD),   # overflow wraps to 0, exercises zero flag
        (0x00000000, 0x00000001, ALU_SUB),   # underflow wraps to 0xFFFFFFFF
        (0x80000000, 0x00000001, ALU_SLT),   # most-negative < 1 (signed) -> 1
        (0x80000000, 0x00000001, ALU_SLTU),  # huge unsigned > 1 -> 0
        (0x80000000, 0x00000004, ALU_SRA),   # sign bit replicates -> 0xF8000000
        (0x80000000, 0x00000004, ALU_SRL),   # zero-fill -> 0x08000000
        (0x00000001, 0x0000001F, ALU_SLL),   # walk the bit up to the MSB
        (0xDEADBEEF, 0x00000000, ALU_SLL),   # shift by 0 leaves value unchanged
        (0xDEADBEEF, 0x0000001F, ALU_SRL),   # max shift amount
        (0xFFFFFFFF, 0x0000001F, ALU_SRA),   # -1 >>> 31 stays -1
        (0x7FFFFFFF, 0x00000001, ALU_ADD),   # signed overflow: max positive + 1
        (0x12345678, 0x12345678, ALU_XOR),   # a ^ a = 0, exercises zero flag
        (0x12345678, 0x12345678, ALU_SUB),   # a - a = 0, exercises zero flag
        (0xFFFFFFFF, 0x00000000, ALU_AND),   # anything AND 0 = 0
        (0x00000000, 0xFFFFFFFF, ALU_OR),    # 0 OR all-ones = all-ones
        (0x00000005, 0x00000005, ALU_SLT),   # equal values -> not less-than
        (0x00000005, 0x00000005, ALU_SLTU),
        (0xFFFFFFFF, 0x00000000, ALU_SLT),   # -1 < 0 signed -> 1
        (0xFFFFFFFF, 0x00000000, ALU_SLTU),  # max unsigned < 0 -> 0
    ]

    for a, b, op in vectors:
        await apply_and_check(dut, a, b, op)

    dut._log.info(f"{len(vectors)} directed edge tests passed.")


def random_operand(corners):
    """Random 32-bit value, but 20% of the time pick a known-nasty corner value."""
    if random.random() < 0.2:
        return random.choice(corners)
    return random.getrandbits(32)


@cocotb.test()
async def test_constrained_random(dut):
    """Throw N random vectors at every op; DUT must match the model every time."""
    N = 2000
    corners = [0, 1, 0xFFFFFFFF, 0x80000000, 0x7FFFFFFF]
    op_codes = list(ALL_OPS.values())

    for _ in range(N):
        a = random_operand(corners)
        b = random_operand(corners)
        op = random.choice(op_codes)
        await apply_and_check(dut, a, b, op)

    dut._log.info(f"{N} constrained-random vectors passed.")


@cocotb.test()
async def test_coverage(dut):
    """Drive random vectors while recording which bins we hit, then assert
    every required bin was covered. Passing tests with a coverage hole are a
    false sense of security - this closes the loop."""
    N = 3000
    corners = [0, 1, 0xFFFFFFFF, 0x80000000, 0x7FFFFFFF]
    op_codes = list(ALL_OPS.values())
    shift_ops = (ALU_SLL, ALU_SRL, ALU_SRA)

    ops_seen = set()
    corner_bins = set()

    for _ in range(N):
        a = random_operand(corners)
        b = random_operand(corners)
        op = random.choice(op_codes)
        await apply_and_check(dut, a, b, op)

        ops_seen.add(op)
        expected = alu_model(a, b, op)
        if expected == 0:
            corner_bins.add("result_zero")
        if op in shift_ops and (b & 0x1F) == 0:
            corner_bins.add("shift_by_0")
        if op in shift_ops and (b & 0x1F) == 31:
            corner_bins.add("shift_by_31")
        if op in (ALU_SLT, ALU_SLTU) and (a >> 31) != (b >> 31):
            corner_bins.add("compare_mixed_signs")
        if a == 0x80000000 or b == 0x80000000:
            corner_bins.add("operand_most_negative")
        if a == 0xFFFFFFFF or b == 0xFFFFFFFF:
            corner_bins.add("operand_all_ones")

    assert ops_seen == set(op_codes), (
        f"ops never exercised: {[OP_NAME[o] for o in set(op_codes) - ops_seen]}"
    )
    required = {
        "result_zero", "shift_by_0", "shift_by_31",
        "compare_mixed_signs", "operand_most_negative", "operand_all_ones",
    }
    assert required.issubset(corner_bins), (
        f"corner bins missed: {required - corner_bins}"
    )

    dut._log.info(f"Coverage closed: all {len(ops_seen)} ops, bins hit: {sorted(corner_bins)}")
