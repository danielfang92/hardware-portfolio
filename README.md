# Hardware Portfolio

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
co-simulation, formal verification, and FPGA deployment of the core. The only hardware bring-up so far
is a blink bitstream and an out-of-context synthesis run of the register file.

## Verification approach

- **Self-checking testbenches** in cocotb (Python), no eyeballing waveforms.
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
failure. It is currently **32/32 passing** from a clean clone. Individual
projects:

```bash
make counter    # 4-bit parameterized counter
make uart       # UART transmitter (8N1)
make alu        # 32-bit RV32I ALU: reference model, constrained-random, coverage gate
make cpu        # single-cycle R/I-type core: regfile, imem, decoder, pc, control, cpu
make clean      # remove build artifacts
```

Waveforms are dumped to each project's `tb/sim_build/` and open with GTKWave.

## Synthesis

The register file was run through Vivado out-of-context for the Artix-7
(`xc7a35tcpg236-1`): 109 LUTs, 0.52% of the device, with the tool inferring
distributed RAM for the 32x32 array rather than discrete flip-flops. The
utilization report is committed alongside the build scripts.

## Documentation

- [Setup notes](docs/setup.md) — toolchain and environment
- [Learning log](docs/learning-log.md) — technical notes, bugs, and post-mortems
