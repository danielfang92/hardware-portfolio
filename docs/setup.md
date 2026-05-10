# Development Environment Setup

This document describes the toolchain used in this portfolio.

## Operating System
- **Host:** Windows 11
- **Development environment:** Ubuntu 24.04 LTS via WSL2

## Hardware (planned)
- **FPGA Board:** Digilent Basys 3 (AMD Artix-7 XC7A35T-1CPG236C)

## Toolchain

### Simulation
- **Verilator** 5.020 — fast Verilog/SystemVerilog simulator (primary)
- **Icarus Verilog** 12.0 — alternative simulator
- **GTKWave** — waveform viewer

### Verification
- **cocotb** — Python-based testbench framework
- **pytest** — test runner integration
- **SystemVerilog Assertions (SVA)** — for property-based verification

### Synthesis
- **Yosys** 0.33 — open-source synthesis (used for formal verification flows)
- **AMD Vivado ML Standard 2025.2** — production synthesis and FPGA  programming (planned for June)

### Formal Verification
- **SymbiYosys (sby)** — bounded model checking and formal property proofs

### Languages
- SystemVerilog (RTL design + verification)
- Python 3.12 (cocotb testbenches, automation)
- C/C++ (reference models, embedded code)

### Version Control
- Git + GitHub
- SSH key authentication

## Installation Notes

### WSL2 Setup
wsl --install -d Ubuntu

### Toolchain Install (Ubuntu)
sudo apt install -y verilator iverilog gtkwave yosys make git build-essential python3 python3-venv
python3 -m venv ~/cocotb-env
source ~/cocotb-env/bin/activate
pip install cocotb cocotb-test pytest

## Project Structure
hardware-portfolio/
├── docs/                  # Documentation, learning log, setup notes
├── projects/              # Individual RTL projects
│   ├── counter/           # 4-bit counter (warmup, May 2026)
│   ├── uart/              # UART tx/rx (June 2026)
│   ├── alu/               # 32-bit ALU with UVM-style verification (June 2026)
│   ├── riscv-cpu/         # Pipelined RV32I CPU (July 2026)
│   └── systolic-array/    # INT8 GEMM accelerator (August 2026)
├── hdlbits-solutions/     # SystemVerilog drilling solutions
└── README.md
