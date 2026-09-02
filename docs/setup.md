# Development Environment Setup

This document describes the toolchain **actually in use** in this portfolio.
Tools I plan to adopt but am not yet using are listed under "Planned," so this
file reflects the repo as it stands rather than the eventual goal.

## Operating System
- **Host:** Windows 11
- **Development environment:** Ubuntu 24.04 LTS via WSL2

## Hardware
- **FPGA Board:** Digilent Basys 3 (AMD Artix-7 XC7A35T-1CPG236C)

## Toolchain (in use)

### Simulation
- **Icarus Verilog** 12.0 — the simulator used for every testbench in this repo
- **cocotb** 2.0.1 — Python testbench framework (drives Icarus)
- **GTKWave** — waveform viewer

### Verification
- **cocotb** testbenches in Python
- **Python reference models** checked against the DUT (ALU)
- **Constrained-random stimulus** and **functional coverage** (ALU)
- **Mutation testing** — every module and the integrated datapath: deliberately
  break the RTL, confirm a test fails, restore, confirm it passes

### Synthesis
- **AMD Vivado 2025.2** — synthesis, place-and-route, and bitstream generation
  targeting the Basys 3 (Artix-7). Done so far: a bring-up blink bitstream
  (timing-closed at 100 MHz) and an out-of-context register-file
  characterization (109 LUTs; report in `vivado_regfile/utilization.rpt`).

### Languages
- **SystemVerilog** — RTL design and testbench top levels
- **Python** 3.13 — cocotb testbenches and reference models
- **Tcl** — Vivado batch build scripts (`build_*.tcl`)

### Version Control
- Git + GitHub, SSH key authentication

## Planned (not yet in the repo)

On the roadmap but **not** yet present here — listed so nothing above overstates
what exists:
- **Verilator** — faster simulation, to adopt when sim speed matters (the apt
  version was too old for cocotb 2.0 at setup time, so Icarus is used instead)
- **SystemVerilog Assertions (SVA)** — property-based checks
- **SymbiYosys / Yosys formal** and **riscv-formal** — bounded model checking
  and formal proofs
- **Spike** co-simulation and **riscv-dv** for the CPU

## Installation Notes

### WSL2 Setup
    wsl --install -d Ubuntu

### Toolchain Install (Ubuntu)
    sudo apt install -y iverilog gtkwave make git build-essential python3 python3-venv
    python3 -m venv ~/cocotb-env
    source ~/cocotb-env/bin/activate
    pip install cocotb cocotb-test pytest

## Project Structure
    hardware-portfolio/
    ├── docs/                  # Documentation, learning log, setup notes
    ├── projects/
    │   ├── counter/           # 4-bit counter (warmup)
    │   ├── uart/              # UART transmitter (uart_tx; receiver planned)
    │   ├── alu/               # 32-bit RV32I ALU — reference model + constrained-random + coverage
    │   ├── riscv_cpu/         # Single-cycle RV32I core, R-type (pipelining planned)
    │   └── bringup/           # Basys 3 blink bring-up (bitstream flow)
    ├── build_*.tcl            # Vivado batch synthesis scripts
    ├── hdlbits-solutions/     # SystemVerilog drill solutions
    └── README.md

Planned but not yet in the repo: UART receiver, systolic array (INT8 GEMM),
SoC integration.
