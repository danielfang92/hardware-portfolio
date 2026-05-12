# Learning Log

Daily notes documenting my progression in chip design and computer architecture. Started May 2026, logging until end of summer.

## Format

Each entry contains:
- **Date** (YYYY-MM-DD)
- **Time spent** (rough hours)
- **What I did** (concrete actions)
- **What I learned** (key concepts, insights)
- **Stuck on / questions** (things to revisit)


##2026-05-12
**Time spent:** 2 hours

**What I did:**
- Watched Mutlu Lectures 1-2, Reviewing concepts from ELEC271 (Transistors, Gates, Combination Logic)
- Completed HDLBits problems 1-8



---

##2026-05-09

**Time spent:** ~1 hours (setting up)

**What I did:**
- Set up WSL2 with Ubuntu 24.04 on Windows
- Installed open-source toolchain: Verilator 5.020, Icarus Verilog 12.0, Yosys 0.33, GTKWave
- Set up Python venv with cocotb, pytest
- Configured Git with SSH keys, connected to GitHub
- Created portfolio repo with initial structure (docs/, projects/, hdlbits-solutions/)
- Decided to defer Vivado install until June (disk space + Basys 3 still in transit)

**What I learned:**
- WSL2 gives a real Linux environment on Windows. Every chip company runs Linux, this is the standard setup
- The open-source toolchain (Verilator + cocotb + Yosys + GTKWave) covers ~80% of what I need before Vivado matters
- SystemVerilog is the industry standard, not classic Verilog — write everything using `logic`, `always_ff`, `always_comb` from day one
- The full Vivado ML Standard install includes forced Vitis HLS (~10-12 GB extra) — main savings come from selecting only Artix-7 in the device list

**Stuck on / questions:**
- Nothing yet

**Tomorrow:**
- Create HDLBits account (hdlbits.01xz.net)
- Find Onur Mutlu Digital Design playlist on YouTube, bookmark
- Watch Mutlu Lectures (intro)
- Solve HDLBits problems 1-5 (warmup), push solutions to repo

---
