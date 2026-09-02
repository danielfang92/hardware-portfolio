# RV32I CPU — Project Context

Last updated: 2026-08-11

> Update: `cpu.sv` is now integrated — single-cycle, R-type, four CPU-level
> tests plus integration mutation testing. The sections below are the
> 2026-08-11 snapshot; the next real step is I-type immediates.

## Who and why

Daniel Fang, 3rd-year Electrical Engineering, Queen's University. Building a
hardware design + verification portfolio targeting Summer 2027 QUIP internships
in RTL design and design verification. Primary target AMD Markham; also
Tenstorrent, NVIDIA, Qualcomm, Intel Toronto, Ciena. Applications open late
August 2026.

## How I want to work

I write all RTL and testbenches myself. Do NOT generate complete modules or
testbenches for me — explain concepts, point at what's wrong, give hints. I
learn by typing and by asking why. Prefer explaining the reasoning behind a
design choice over stating a rule.

Be direct. Tell me if a plan is bad. Don't over-praise.

## Toolchain

- SystemVerilog RTL, cocotb 2.0.1 testbenches in Python
- Icarus Verilog 12.0 (Verilator deferred until sim speed matters)
- WSL2 / Ubuntu, Python venv at ~/cocotb-env (activate before make)
- GTKWave for waveforms
- Vivado WebPACK 2025.2, Basys 3 (Artix-7 XC7A35T) — FPGA work is weeks out
- Repo: github.com/danielfang92/hardware-portfolio

## Conventions

- Parameters UPPERCASE, signals lowercase
- Active-low async reset: always_ff @(posedge clk or negedge rst_n) + if (!rst_n)
- Non-blocking <= in always_ff, blocking = in always_comb and assign
- always_comb: assign every output unconditionally at the top, then override.
  Prevents latch inference.
- typedef enum logic [N:0] for FSM states and op encodings, explicit values
- begin/end on all always and if/else bodies
- default case in every case statement
- _n suffix means active-low
- cocotb: unit="ns" not units= (renamed in cocotb 2.0). start_soon, not fork.
- Sampling: await RisingEdge returns AT the edge, before FFs propagate.
  Add await Timer(1, unit="ns") before reading signals.

## Current state (2026-08-11)

Six modules built, each verified with cocotb and mutation-tested:

| Module | File | Notes |
|---|---|---|
| ALU | projects/alu/rtl/alu.sv | 10 ops, 4-bit selector, reference model + constrained-random + coverage |
| Register file | riscv_cpu/rtl/regfile.sv | 32x32, 2 read 1 write, x0 hardwired, NO reset port |
| Decoder | riscv_cpu/rtl/decoder.sv | R-type field extraction only, combinational |
| Program counter | riscv_cpu/rtl/program_counter.sv | +4 per cycle, async reset to 0 |
| Instruction memory | riscv_cpu/rtl/imem.sv | 64x32 read-only, zero-filled, indexed addr[7:2] |
| Control unit | riscv_cpu/rtl/control.sv | R-type only, outputs alu_op and reg_write |

`riscv_pkg.sv` holds the alu_op_t enum, shared by alu.sv and control.sv.
It MUST come first in VERILOG_SOURCES or Icarus reports "unknown type alu_op_t".

## Next step

cpu.sv — top-level integration. Instantiate all six modules and wire them:

PC → imem → decoder → {control, regfile addresses} → regfile reads → ALU →
writeback to regfile (rd_addr, alu_result, reg_write).

Two things that will bite:
- regfile takes clk but NO rst_n. Only the PC has a reset.
- The first program test will read x1 and x2 before anything writes them, so
  they read X. Seed them through the regfile's write port from the testbench
  before running the program — there is no addi yet to load constants.

## Design decisions and why

- Register file has no reset: software writes every register before reading it,
  so power-up state never matters. Saves a reset net across 1024 flip-flops.
  The PC is the opposite — nothing else can initialize it.
- x0 needs TWO guards: a write-block (rd_addr != 0) and a read-force-zero.
  Without a reset, registers[0] is undefined, so the read guard is what
  actually makes x0 read as zero.
- Decoder and control are separate modules: the decoder does mechanical field
  extraction, control does interpretation. Lets me add I-type without
  rewriting the decoder.
- imem zero-fills at init so untouched slots are defined rather than X.
  Tradeoff: running past the program is silent, since 32'h00000000 isn't a
  legal instruction but nothing traps.
- Building single-cycle first. Pipelining after it works.

## Verification approach

Every module is mutation-tested: deliberately break the RTL, confirm a test
fails, restore, confirm it passes. A green testbench proves nothing until
you've seen it go red.

Lessons that shaped the tests:
- Test values must be chosen against the bug you're hunting. Small values hide
  slice-width bugs (rd=3 and rd=10 both have bit 11 clear, so a [10:7] slice
  returned identical values and only the all-ones test caught it).
- All-ones catches width errors but is blind to swaps (rs1 and rs2 both 31).
  Distinct values catch swaps but miss width errors. Need both.
- Test through the interface, not internals. Peeking at dut.mem[36] passes
  under an index mutation because the array is fine and only the read path
  is broken.
- Verification effort should scale with design complexity. The ALU earned a
  reference model and constrained-random; the decoder needed three directed
  tests.

## Makefile

Per-DUT builds: SIM_BUILD ?= sim_build/$(TOPLEVEL), so switching DUTs doesn't
need sim_build cleared. TOPLEVEL, MODULE, VERILOG_SOURCES are all overridable:

make MODULE=test_control TOPLEVEL=control \
     VERILOG_SOURCES="$(pwd)/../rtl/riscv_pkg.sv $(pwd)/../rtl/control.sv"

## After cpu.sv

I-type immediates (addi), then loads/stores, then branches, then data memory.
Then pipelining, hazard detection, forwarding. Vivado synthesis and Basys 3
deployment last.