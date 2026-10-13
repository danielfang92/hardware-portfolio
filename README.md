# Hardware Portfolio

[![regression](https://github.com/danielfang92/hardware-portfolio/actions/workflows/regression.yml/badge.svg)](https://github.com/danielfang92/hardware-portfolio/actions/workflows/regression.yml)

Electrical Engineering student at Queen's University, working on RTL design,
design verification, and hardware validation.

Every design here is verified with a self-checking cocotb testbench, and every
testbench is checked by deliberately breaking the RTL and confirming the tests
go red. A green run that has never been seen to fail is not evidence.

## Scope, and what this is not

The RV32I core is **single-cycle and implements the integer register-register
(R-type) and register-immediate (OP-IMM: ADDI, SLTI, SLTIU, XORI, ORI, ANDI,
SLLI, SRLI, SRAI) instructions only**. The control unit decodes two opcodes.
There are no loads, stores, branches or jumps, so **it cannot run a loop**. It
executes those instructions end to end from fetch through writeback, and that
is the whole claim.

Not done yet: loads/stores, branches and jumps, LUI/AUIPC, pipelining, Spike
co-simulation, formal verification, and FPGA deployment of the core. The core
has been synthesized and routed out of context (numbers below) but not run on
the board. The only bitstream so far is a blink test.

## Verification approach

- **Self-checking testbenches** in cocotb (Python), no eyeballing waveforms.
- **Checked at the ports** — CPU programs are loaded through the instruction
  memory's write port, and every check compares the full sequence of register
  writes reported on the core's write-back port, rather than reading internal
  registers. The one exception is clearing the register file between tests,
  since it has no reset and all tests share a simulation.
- **Reference modelling** — the ALU is checked against a Python model written
  from the RISC-V ISA specification rather than from the RTL, so the test cannot
  simply agree with the design.
- **Functional coverage as a gate** — the ALU run fails if any of the 10
  operations or 6 named corner-case bins went unhit across 3,000
  constrained-random vectors. Pass criteria are fixed in source, not derived
  from what the run happened to hit.
- **Mutation testing** on every module and on the integrated datapath: inject a
  known fault, confirm the suite goes red, restore, confirm it goes green.
- **Clean-clone regression** — the suite is rebuilt from a fresh clone of this
  repo in a pinned environment, as a stranger would, because a green run is
  evidence about the environment as much as about the design.

Notes on specific bugs, including the ones the tests initially failed to catch,
are in the [learning log](docs/learning-log.md).

## Tech Stack

- **HDL:** SystemVerilog
- **Simulation:** Icarus Verilog 12.0 + cocotb 2.0.1 (Python)
- **Synthesis:** AMD Vivado 2025.2 (Artix-7 / Basys 3)
- **Automation:** Make (multi-DUT regression), Tcl (Vivado batch builds), Git
- **Languages:** SystemVerilog, Python, C/C++, Tcl

## Running the tests

Requires [Icarus Verilog](https://steveicarus.github.io/iverilog/) 12.0 and
Python 3.9-3.13. cocotb 2.0.x refuses to build on Python 3.14, so name the
interpreter explicitly rather than relying on the system default:

```bash
python3.13 -m venv env
source env/bin/activate
pip install -r requirements.txt
make
```

`make` runs the full regression across every project and stops on the first
failure. It is currently **34/34 passing** from a clean clone.

The same 34-test regression runs in GitHub Actions on every push
([`.github/workflows/regression.yml`](.github/workflows/regression.yml)), on a
pinned Ubuntu 24.04 runner with Python 3.12. CI is simulation only: Vivado is
licensed and installed on Windows, so synthesis is still run locally with
`make synth`.

Individual projects:

```bash
make counter    # 4-bit parameterized counter
make uart       # UART transmitter (8N1)
make alu        # 32-bit RV32I ALU: reference model, constrained-random, coverage gate
make cpu        # single-cycle R/I-type core: regfile, imem, decoder, pc, control, cpu
make clean      # remove build artifacts
make synth      # Vivado out-of-context build of the CPU + one-line area/timing summary
```

Waveforms are dumped to each project's `tb/sim_build/` and open with GTKWave.

## Synthesis

Vivado 2025.2, out of context, Artix-7 (`xc7a35tcpg236-1`), 100 MHz target.

| Block | LUTs | of which distributed RAM | FFs | Timing |
|---|---|---|---|---|
| Single-cycle core | 608 (2.9%) | 88 | 30 | met, WNS +0.505 ns |
| Register file alone | 109 (0.5%) | 44 | 0 | no reg-to-reg paths |

Both the 32x32 register file and the 64-word instruction memory come out as
distributed RAM rather than flip-flops. The 30 flip-flops are the PC: its low
two bits are always zero, so Vivado replaces them with constants. The
critical path runs PC → instruction memory → register file read → ALU carry
chain → register file write, about 9.25 ns across 10 logic levels, most of it
routing.

The timing is against an ideal clock. Out of context, Vivado doesn't know
where the clock buffer will sit, so there is no insertion delay or skew in the
number, and the margin would shrink in a full design.

An earlier build reported 217 LUTs. That figure was wrong as a size for the
core: the instruction memory was a fixed ROM, so Vivado knew only three
instructions could ever run and removed the logic for everything else. Adding
a write port to the instruction memory makes its contents unknown at
synthesis time, which is what produces the number above. Reports are in
`vivado_cpu/` and `vivado_regfile/`; `make synth-report` reprints the summary.

## Documentation

- [Setup notes](docs/setup.md) — toolchain and environment
- [Learning log](docs/learning-log.md) — technical notes, bugs, and post-mortems
