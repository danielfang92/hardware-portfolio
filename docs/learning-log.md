# Learning Log

Daily notes documenting my progression in chip design and computer architecture. Started May 2026, logging until end of summer.

## Format

Each entry contains:
- **Date** (YYYY-MM-DD)
- **Time spent** (rough hours)
- **What I did** (concrete actions)
- **What I learned** (key concepts, insights)
- **Stuck on / questions** (things to revisit)


## 2026-06-08 to 2026-06-13

**Counter project shipped locally — 4/4 cocotb tests passing, pushed to GitHub.**

### What I built and did
- `counter.sv` — parameterized 4-bit counter with active-low async reset and enable
- `test_counter.py` — cocotb testbench with 4 tests:
  - `test_reset_clears_count` — reset clears count to 0
  - `test_count_up` — counts 0 through 15
  - `test_wrap_around` — wraps from 15 back to 0 (natural overflow)
  - `test_enable_holds` — count holds when en=0
- `Makefile` — Icarus Verilog + cocotb build config
- `.gitignore` for build artifacts
- completed Counters and Latches and Flip-flops sections of HDLBits Problem set
### Toolchain set up
- Icarus Verilog 12.0 as simulator (Verilator was too old in apt — 5.032 vs cocotb's required 5.036)
- cocotb 2.0.1 in Python 3.13 venv
- Make + GTKWave + Vivado WebPACK 2025.2 (installed in background)

### SystemVerilog lessons
- **Active-low async reset convention**: `always_ff @(posedge clk or negedge rst_n)` + `if (!rst_n)` — what real chips use (AMD, ARM defaults). HDLBits uses active-high sync because it's simpler to teach.
- **Parameterized modules**: `module name #(parameter int WIDTH = 4) (...)` — the `#(...)` block is for compile-time parameters, must come before port list `(...)`.
- **Sensitivity list = physical cell selection**: putting reset in sensitivity list tells synthesizer to use the async-reset flip-flop cell (with dedicated reset pin), not the sync-reset cell.
- **`always_comb` vs `always_ff` latch behavior**: missing assignment in `always_comb` infers a latch (bad, error in modern tools). Missing assignment in `always_ff` is fine — FF holds its previous value (standard register-with-enable pattern).
- **Natural overflow** wraps a 4-bit counter at 15 → 0 for free; no `if (count == 15)` check needed when wrap point matches signal width.

### cocotb-specific lessons
- **Sampling timing quirk**: `await RisingEdge(dut.clk)` returns AT the clock edge, BEFORE flip-flops propagate their new values. Adding `await Timer(1, units="ns")` after `RisingEdge` lets FF outputs settle before reading. Without it, you sample pre-edge values and see "off by one" failures.
- **Input change propagation**: setting a control signal like `en` doesn't take effect until the next clock edge. When testing hold behavior, must wait one full cycle after setting `en=0` before capturing the held value.
- **Python is strict about tabs vs spaces**: mixed indentation = `TabError`. Fix: `expand -t 4 file.py > tmp && mv tmp file.py` to normalize to spaces.
- **cocotb scoreboard pattern**: `assert dut.signal.value == expected, f"context: expected X, got {int(dut.signal.value)}"` — the f-string only evaluates on failure, giving rich debug info.

### Debugging methodology practiced
Real DV workflow: wrote tests, ran simulation, read failures, traced to root cause. Bug hunt log:
1. Signal name mismatch: testbench used `dut.reset`, design used `rst_n` → `AttributeError: counter contains no child object named reset`
2. Missing `Timer` import → `NameError`
3. Comment swallowed `dut.en.value = 1` line → silent test failure
4. Pre-edge vs post-edge sampling → "expected 1 got 0" failures
5. Mixed tabs and spaces from pasting code → Python `TabError`
6. Setting `en=0` between clock edges → "Counter should hold at 4, got 5" timing failure

Each bug was solved by reading the simulator output, tracing the file/line, and fixing the root cause. This is what DV engineers actually dp.

### Git workflow practiced
- Three-stage model: working directory → staging area (`git add`) → repository (`git commit`)
- `git push` syncs local commits to GitHub
- `.gitignore` keeps build artifacts (`sim_build/`, `results.xml`, `__pycache__/`, `*.vcd`) out of the repo

### Time spent
~6 hours including HDL problems, debugging, and toolchain setup.

### Open items
- Order Basys 3 (Digilent address validation failing on BC postal code)
- Start UART project tomorrow or Monday (Jun 15 per master plan v3)
- Begin outreach to Queen's seniors / QUIP alumni at AMD Markham, Qualcomm, NVIDIA, etc. to gain insight on DV/Design careers
- Check Queen's MyCareer portal weekly for QUIP postings (open August-October)

### Reflection
First time doing real DV end-to-end. The "design works in HDLBits browser" → "design works in local toolchain" gap was bigger than expected — most of tonight's bugs were testbench + toolchain issues, not design issues. The cocotb sampling-semantics fix (`Timer(1, "ns")` after every `RisingEdge`) was the most important lesson — that's a quirk every cocotb engineer learns eventually. Now it's in the muscle memory.

The actual counter design was correct on the first try. Everything else was learning the verification ecosystem. That's exactly what should be slow on the first project and fast on subsequent ones.

---


## 2026-05-13 to 2026-06-07
**What I did:**
- Completed Verilog Language section of HDLBits (Vectors, Modules:Hiearchy, Procedures, Other Verilog Features
-Set up Vivado, WSL and Ubuntu Configured Git on New Laptop

## 2026-05-12
**Time spent:** 2 hours

**What I did:**
- Watched Mutlu Lectures 1-2, Reviewing concepts from ELEC271 (Transistors, Gates, Combination Logic)
- Completed HDLBits problems 1-8



---

## 2026-05-09

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
