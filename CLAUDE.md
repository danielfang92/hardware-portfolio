# CLAUDE.md — Hardware Portfolio Context

## Who I am and what this is

I'm Daniel Fang, a 3rd-year Electrical Engineering student at Queen's University. This repo is a hardware design + verification portfolio I'm building due to interest in computer architecture and RTL. Looking to target **Summer 2027 QUIP internships** (Queen's Undergraduate Internship Program, a 12-16 month placement). Applications open August-October 2026.

**Target roles:** RTL design and design verification (DV) internships.
**Strongly Interested in:** AMD Markham, Tenstorrent Toronto, NVIDIA, Qualcomm, Intel Toronto, Ciena, Qualcomm, Marvell, Nokia, Amazon (Annapurna Labs) Toronto, Synopsys, Alphawave Semi, Rambus, The Six Semiconductor, Celestica, IBM Canada, DragonWave, SanDisk, Ericson, Huawei Canada, Thales Canada, L3Harris, Taalas, Untether AI

I want to work in Ontario (Toronto area) preferably, open to Vancouver and Alberta. I'm in Trail, BC for the summer, back at Queen's in September.

GitHub: danielfang92/hardware-portfolio

## What I'm optimizing for

**Depth over breadth.** The goal is a portfolio-grade RISC-V CPU with industry-standard verification (self-checking testbenches, coverage, formal proofs, FPGA deployment). This differentiates me from typical QUIP applicants who have coursework projects but no real verification methodology.

**AMD DV interview prep** is a north star. From real interview data, AMD Markham DV interviews test: writing Verilog live (e.g. a counter with synchronous reset), digital logic fundamentals, one LeetCode Easy, Python basics (sets/dicts), and computer architecture (caches, pipelining). My projects ARE my interview prep.

## How I want you to work with me

**I'm learning, not just shipping.** Do NOT just write code for me to paste, except incertain autonomous circumstances (bypassable) I need to understand every line. When we write something:
- Explain concepts from scratch, intuitively, assuming I'm newer to hardware.
- Have me type code myself (I learn by typing, not pasting).
- After writing something, sometimes have me rewrite it from scratch to lock it in.
- Prefer hint-mode over full solutions when I'm debugging.
- Ask me to explain code back to verify I actually understand it.

**I ask "why" a lot.** WHY explanations land better than rules for me. Explain the reasoning behind design choices.

**Style:** direct, practical, low fluff. Real engineering judgment. Honest assessments — tell me if a plan is bad. Don't over-praise. Minimal emojis.

**Sustainability matters:** I work a 5 AM-1:30 PM groundskeeper shift, so I have ~15-20 hrs/week. Weekend mornings are for heavy design work; tired weekday afternoons are for lighter scaffolding/review. One rest day per week. Don't let me grind into burnout.

## Toolchain (already set up)

- **HDL:** SystemVerilog
- **Simulation:** cocotb (Python) + Icarus Verilog 12.0 (Verilator was too old in apt; using Icarus)
- **Waveforms:** GTKWave
- **Synthesis:** Vivado WebPACK 2025.2 (AMD toolchain, intentional alignment with target employers)
- **Environment:** WSL/Ubuntu, Python 3.13 venv at ~/cocotb-env (activate before running make)
- **Board:** Basys 3 (Xilinx Artix-7 XC7A35T), 100 MHz clock — ordering/ordered via DigiKey, ships to Trail
- **Version control:** Git/GitHub

Pending installs before CPU project: riscv-gnu-toolchain, Spike, SymbiYosys, riscv-formal, riscv-dv.

## Project sequence (master plan v3)

1. ✅ **Counter** — DONE. Parameterized 4-bit counter, active-low async reset + enable, 4/4 cocotb tests, GTKWave waveform, pushed.
2. ✅ **UART transmitter** — DONE. `uart_tx.sv`: 8N1 framing, parameterizable baud, 4-state FSM (IDLE/START/DATA/STOP), 2/2 cocotb tests passing, pushed.
3. ⏳ **UART receiver** (`uart_rx.sv`) + loopback test — NOT STARTED (optional extension of UART project)
4. ⏳ **ALU** — NEXT. 32-bit RV32I ALU (ADD, SUB, AND, OR, XOR, SLL, SRL, SRA, SLT, SLTU). Constrained-random testing with reference model + coverage. Mostly combinational.
5. ⏳ **Pipelined RV32I CPU** — THE HEADLINE. 5-stage pipeline, hazard detection, forwarding, Spike co-sim, riscv-dv, riscv-formal proofs, C programs, FPGA deployment.
6. ⏳ **QUIP applications** (Aug-Oct)
7. ⏳ **Systolic array** (8x8 INT8 GEMM)
8. ⏳ **SoC integration** (CPU + GEMM + UART, memory-mapped)
9. ⏳ **Open-source contribution** (cocotb / CV32E40P / Ibex / riscv-formal PRs)

Timeline is ~10 days shifted from original (as of July 8) but within the 20% buffer. ALU now ~Jul 8-20, CPU ~Jul 21 onward.

## Project structure convention

Each project follows:
```
projects/<name>/
  rtl/          <- SystemVerilog design files (.sv)
  tb/           <- cocotb testbench (.py) + Makefile
  docs/         <- notes, waveform screenshots
  .gitignore    <- sim_build/, results.xml, __pycache__/, *.vcd, *.save
```

Makefile uses `SIM ?= icarus`. The venv must be active (`source ~/cocotb-env/bin/activate`) before `make`.

## SystemVerilog conventions I follow

- Parameters UPPERCASE (`BAUD_RATE`), variables/signals lowercase (`baud_counter`).
- `localparam` for internal derived constants, `parameter` for caller-configurable ones.
- Active-low async reset: `always_ff @(posedge clk or negedge rst_n)` + `if (!rst_n)`. This is the industry default.
- `<=` (non-blocking) in `always_ff`; `=` (blocking) in `always_comb` and `assign`.
- `typedef enum logic [N:0] {...} state_t;` for FSM states, with explicit encodings.
- Always use `begin`/`end` on all always/if/else bodies (prevents dangling-else bugs).
- Always include a `default` case in FSM case statements.
- `_n` suffix means active-low.

## cocotb patterns I use

- `cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())` to start the clock.
- Sampling quirk: `await RisingEdge(dut.clk)` returns AT the edge, before FFs propagate. Add `await Timer(1, units="ns")` before reading signals.
- Scoreboard assertions: `assert sig.value == expected, f"context: expected X, got {int(sig.value)}"` (f-string only evaluates on failure).
- Override params in Makefile for fast sim (e.g. small BAUD_DIVIDER) via `COMPILE_ARGS += -P module.PARAM=value`.

## Concepts I've internalized (don't need re-explaining from zero, but I still like "why")

FSM design (states/transitions/outputs, Moore vs Mealy, 1-block vs 3-block), sync vs async reset and why reset is held multiple cycles, combinational vs sequential, why latches get inferred, `always_ff` as clock-paced flip-flops (not a software loop), UART 8N1 protocol (idle HIGH, start bit LOW, LSB first, baud divider math, bit centers/oversampling), parameterization, bit manipulation (`data[bit_index]`, `>>`, `& 1`), git three-stage workflow.

## What I'm still building fluency in

Writing Python and SystemVerilog from scratch (not just recognizing it) — this is critical for the live-coding AMD interview. Push me to write code myself. Also building: constrained-random verification, coverage, formal methods, computer architecture depth.
