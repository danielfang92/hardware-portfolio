"""Cocotb testbench for the 32-bit RV32I ALU.

VERIFICATION STRATEGY (this is the real point of the ALU project — the RTL was
the easy part). Four layers, cheap to expensive:

  1. Reference model     - a pure-Python "golden" ALU we trust as the source of truth.
  2. Directed tests      - hand-picked edge cases (overflow, sign boundaries, shift by 0/31).
  3. Constrained-random  - thousands of random (a, b, op) vectors: DUT vs model.
  4. Coverage            - prove we actually exercised every op and every interesting corner,
                           so "10,000 passing random tests" isn't secretly 10,000 ADDs.

NOTE ON TIMING: the ALU is purely combinational. There is NO clock and NO reset.
We don't await RisingEdge — we set the inputs, wait a tiny Timer for the logic to
settle, then read the outputs. That's the big structural difference from uart_tx.
"""

import cocotb
from cocotb.triggers import Timer
import random


# ---------------------------------------------------------------------------
# OP ENCODINGS  — must match the enum in alu.sv exactly.
# ---------------------------------------------------------------------------
# TODO: define one constant per op code, matching alu.sv:
#   ALU_ADD = 0, ALU_SUB = 1, ALU_AND = 2, ALU_OR = 3, ALU_XOR = 4,
#   ALU_SLL = 5, ALU_SRL = 6, ALU_SRA = 7, ALU_SLT = 8, ALU_SLTU = 9
#
# HINT: also build a dict  ALL_OPS = {"ADD": ALU_ADD, "SUB": ALU_SUB, ...}
#       so the random loop and coverage can iterate over every op by name.

MASK32 = 0xFFFFFFFF  # force Python's arbitrary-width ints back down to 32 bits


# ===========================================================================
# 1. REFERENCE MODEL
# ===========================================================================

def to_signed(val):
    """Reinterpret a 32-bit unsigned value as two's-complement signed.

    WHY THIS EXISTS: Python ints are infinite precision. To Python, 0xFFFFFFFF
    is ~4.29 billion. To the hardware it's -1. SLT and SRA need the *signed*
    view of the bits, so we convert first.

    PSEUDOCODE:
        if bit 31 of val is set:      # i.e. val >= 2**31
            return val - 2**32        # wrap into the negative range
        else:
            return val
    """
    # TODO: implement
    pass


def alu_model(a, b, op):
    """Golden model. Given 32-bit unsigned a, b and an op code, return the
    32-bit result the hardware SHOULD produce. Must match alu.sv exactly —
    if model and DUT ever disagree, exactly one of them has the bug.

    PSEUDOCODE:
        shamt = b & 0x1F                      # low 5 bits == operand_b[4:0]

        if   op == ALU_ADD:  return (a + b) & MASK32
        elif op == ALU_SUB:  return (a - b) & MASK32
        elif op == ALU_AND:  return a & b
        elif op == ALU_OR:   return a | b
        elif op == ALU_XOR:  return a ^ b
        elif op == ALU_SLL:  return (a << shamt) & MASK32
        elif op == ALU_SRL:  return a >> shamt            # a already unsigned -> logical
        elif op == ALU_SRA:  return (to_signed(a) >> shamt) & MASK32
                                                          # Python's >> on a negative
                                                          # int IS arithmetic (sign-extends)
        elif op == ALU_SLT:  return 1 if to_signed(a) < to_signed(b) else 0
        elif op == ALU_SLTU: return 1 if a < b else 0     # both already unsigned
        else:                return 0                     # matches your RTL default
    """
    # TODO: implement
    pass


# ===========================================================================
# DRIVE + CHECK HELPER  (the scoreboard)
# ===========================================================================

async def apply_and_check(dut, a, b, op):
    """Drive one vector, let the combinational logic settle, compare to model.

    PSEUDOCODE:
        drive dut.operand_a = a
        drive dut.operand_b = b
        drive dut.op        = op
        await Timer(1, units="ns")            # let comb logic propagate; NO clock edge

        expected = alu_model(a, b, op)

        assert dut.result.value == expected, (
            rich f-string showing op, a, b, expected, and int(dut.result.value)
            — remember: f-string only formats on failure, so it's free on pass)

        # zero flag is result == 0; check it too so the flag path gets verified
        expected_zero = 1 if expected == 0 else 0
        assert dut.zero.value == expected_zero, (similar rich message)
    """
    # TODO: implement
    pass


# ===========================================================================
# 2. DIRECTED TESTS — hand-picked corners that random might take ages to hit
# ===========================================================================

@cocotb.test()
async def test_directed_edges(dut):
    """Walk a table of (a, b, op) cases that stress known boundaries.

    PSEUDOCODE:
        build a list of interesting vectors, e.g.:
          - ADD:  0xFFFFFFFF + 1        -> overflow wraps to 0  (also tests zero flag)
          - SUB:  0 - 1                 -> underflow wraps to 0xFFFFFFFF
          - SLT:  0x80000000 vs 0x1     -> most-negative < positive  (signed!)  -> 1
          - SLTU: 0x80000000 vs 0x1     -> huge unsigned > 1                     -> 0
          - SRA:  0x80000000 >> 4       -> sign bit should replicate (0xF8000000)
          - SRL:  0x80000000 >> 4       -> zero-fill                (0x08000000)
          - SLL:  0x1 << 31             -> walks the bit to the MSB
          - shift by 0 and by 31        -> boundary shift amounts

        for (a, b, op) in that list:
            await apply_and_check(dut, a, b, op)

        dut._log.info("Directed edge tests passed.")
    """
    # TODO: implement
    pass


# ===========================================================================
# 3. CONSTRAINED-RANDOM  — the volume test
# ===========================================================================

@cocotb.test()
async def test_constrained_random(dut):
    """Throw N random vectors at every op; DUT must match the model every time.

    "Constrained" = we don't pick fully arbitrary bits blindly; we bias toward
    values that expose bugs (all-zeros, all-ones, the sign boundary, small
    shift amounts) MIXED with pure-random 32-bit values.

    PSEUDOCODE:
        N = 2000
        # a pool of "interesting" operands to sample from sometimes
        corners = [0, 1, 0xFFFFFFFF, 0x80000000, 0x7FFFFFFF]

        for _ in range(N):
            a  = random 32-bit  (occasionally pick from corners instead)
            b  = random 32-bit  (occasionally pick from corners instead)
            op = random.choice(list of the 10 valid op codes)
            await apply_and_check(dut, a, b, op)

        dut._log.info(f"{N} constrained-random vectors passed.")

    HINT: random.getrandbits(32) gives a random 32-bit int.
          random.random() < 0.2  to sometimes pull from `corners`.
    """
    # TODO: implement
    pass


# ===========================================================================
# 4. COVERAGE  — did we actually test what we think we tested?
# ===========================================================================

@cocotb.test()
async def test_coverage(dut):
    """Drive vectors while recording which "bins" we hit, then ASSERT every
    required bin was covered. A passing random test with a coverage hole is a
    false sense of security — this closes the loop.

    Cocotb has no built-in SystemVerilog-style covergroups, so we roll our own
    with plain Python sets/dicts. That's fine and it teaches what coverage IS.

    PSEUDOCODE:
        ops_seen = set()
        corner_bins = set()     # e.g. "result_zero", "shift_by_31", "sll_msb_set"

        run a loop (reuse the random generator, say 3000 vectors):
            pick a, b, op
            await apply_and_check(dut, a, b, op)
            ops_seen.add(op)
            expected = alu_model(a, b, op)
            if expected == 0:          corner_bins.add("result_zero")
            if op in (SLL,SRL,SRA) and (b & 0x1F) == 31: corner_bins.add("shift_by_31")
            ... add whatever bins you care about

        # Now PROVE coverage — these asserts fail the test if a bin was missed:
        assert ops_seen == set(all 10 op codes), f"ops missed: {...}"
        required = {"result_zero", "shift_by_31", ...}
        assert required.issubset(corner_bins), f"corner bins missed: {required - corner_bins}"

        dut._log.info(f"Coverage closed: {len(ops_seen)} ops, bins={corner_bins}")

    STRETCH (later, not now): replace this hand-rolled version with the
    `cocotb-coverage` library's CoverPoint/CoverCross decorators.
    """
    # TODO: implement
    pass
