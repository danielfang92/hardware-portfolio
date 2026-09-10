# Hardware Portfolio

Electrical Engineering student at Queen's University. Interested in RTL design, design verification, and computer architecture.

## Tech Stack

- **HDL:** SystemVerilog
- **Simulation:** Icarus Verilog + cocotb (Python)
- **Synthesis:** AMD Vivado 2025.2 (Artix-7 / Basys 3)
- **Verification:** cocotb testbenches, Python reference models, constrained-random stimulus, functional coverage, mutation testing
- **Languages:** SystemVerilog, Python, Tcl

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
failure. Individual projects:

```bash
make counter    # 4-bit parameterized counter
make uart       # UART transmitter (8N1)
make alu        # 32-bit RV32I ALU
make cpu        # single-cycle core: regfile, imem, decoder, pc, control, cpu
make clean      # remove build artifacts
```

Waveforms are dumped to each project's `tb/sim_build/` and open with GTKWave.

## Documentation

- [Setup notes](docs/setup.md) — toolchain and environment
- [Learning log](docs/learning-log.md) — technical notes
