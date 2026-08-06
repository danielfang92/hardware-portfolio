# Learning Log

Notes documenting my progression in chip design and computer architecture. Started May 2026, logging until end of summer.

## Format

Each entry contains:
- **Date** (YYYY-MM-DD)
- **Time spent** (rough hours)
- **What I did** (concrete actions)
- **What I learned** (key concepts, insights)
- **Stuck on / questions** (things to revisit)


## 2026-07-27 to 2026-08-05

**RV32I datapath building blocks: register file (verified, pushed), decoder, program counter, and instruction memory. Each module mutation-tested before commit.**

### What I built and did
- `regfile.sv` — 32×32, two read ports, one write port, x0 hardwired to zero, no architectural reset. RTL first written Jul 27 (testbench in progress), finished and pushed Aug 3.
- `decoder.sv` — R-type field extraction only: `opcode[6:0]`, `rd[11:7]`, `funct3[14:12]`, `rs1[19:15]`, `rs2[24:20]`, `funct7[31:25]`. Three directed benches (add, sub, all-ones).
- `program_counter.sv` — async-reset PC, increments by 4 each cycle. Renamed the module from `pc` to `program_counter`.
- `imem.sv` — 64-word instruction memory, combinational read, `addr[7:2]` word index, zero-filled at init, preloaded with three R-type words. Two benches (zero-fill, increment).
- Tooling cleanup: migrated cocotb `units=` → `unit=`, removed duplicate/stale files, made the Makefile overridable per DUT.

### Computer architecture / RV32I lessons
- **PC increments by 4** because instructions are 4 bytes and memory is byte-addressed — each address names one byte, and an instruction spans four consecutive addresses.
- **Byte address vs word index**: the PC counts bytes, the array counts words. `addr[7:2]` converts — drop the two low bits to divide by 4, keep six bits to match a 64-entry array.
- **Decoder field positions are deliberate**: `funct3` and `funct7` sit in non-adjacent parts of the instruction so that `opcode`, `rd`, `funct3`, and `rs1` stay at fixed bit positions across R/I/S/B types. Fixed positions mean the decoder extracts them identically regardless of type — no type-dependent muxing.
- **Each format allocates the same 32 bits differently**: J-type has no `funct3`/`funct7` because there's only one jump operation to select; those bits become a 20-bit immediate instead.
- **x0 needs two independent guards**: a write-block (`rd_addr != 0`) and a read-force-zero. With no reset, `registers[0]` is undefined, so the read guard is what actually makes x0 read as zero.
- **Reset asymmetry**: no reset on the register file is deliberate — software initializes it. The PC is the opposite; nothing else can initialize it, so it must have one.

### SystemVerilog lessons
- **Async reset semantics**: `pc` clears the moment `rst_n` drops, not on a clock edge. This changes testbench timing — after deasserting reset, the next rising edge already increments.
- **Out-of-bounds reads on unpacked arrays return X** — defined behavior, not a crash or a wrap.
- **Zero-filling at init vs leaving X**: zero-filling makes untouched slots defined, so an overrun doesn't propagate X into `reg_write`. The tradeoff is that running past the program is silent — `32'h00000000` isn't a legal instruction but nothing announces it. A real CPU would trap.
- **Index width matters for portability**: `addr[7:2]` gives a 6-bit index for a 64-slot array. `addr[31:2]` divides by 4 correctly but leaves a 30-bit index for that same array — a width mismatch Icarus tolerates and Vivado won't.
- **Module and port sharing a name** (`pc`) is legal and Icarus handles it, but renaming the module to `program_counter` removes the ambiguity when it's instantiated in the top level.

### cocotb-specific lessons
- **Missing `@` on `cocotb.test()`** produces "No tests were discovered" — the line becomes a bare function call at import time and nothing registers. No syntax error, just silence.
- **X can't convert to int**: when the target register was never written it held X, so the assert failed as `ValueError: Can't convert LogicArray to int` rather than a clean value mismatch. The error type itself was the clue.

### Verification lessons
- **Test through the interface, not internals.** Checking `dut.mem[36]` directly still passes under the imem index mutation, because the array is fine and only the read path is broken. Driving `addr = 144` catches it. Interface access is also portable — VPI visibility into unpacked arrays varies by simulator.
- **All-ones and directed tests are blind to different bugs.** All-ones catches width errors but can't catch a swapped `rs1`/`rs2` (both fields are 31). Directed tests with distinct values catch swaps but miss width errors. Both are necessary.
- **Any field left at a realistic value in an all-ones test is unprotected.** The opcode was still `0b0110011`, whose bits `[5:0]` also equal 51, so an `opcode[5:0]` slice bug would have passed unnoticed. Changed it to `0b1111111`.

### Tooling and process
- **Icarus caches compiled output in `sim_build/`.** Switching DUTs without clearing it gives "Couldn't find root handle" and a toplevel mismatch. Fixed structurally with `SIM_BUILD ?= sim_build/$(TOPLEVEL)` instead of remembering `rm -rf`.
- **Makefile variables changed to `?=`** so `TOPLEVEL`, `MODULE`, and `VERILOG_SOURCES` are overridable per DUT. Command-line variables override `=` assignments anyway — what `?=` adds is environment-variable override.
- **cocotb 2.0 renamed `units=` to `unit=`.** The old form still works but warns. `cocotb.fork()` was removed; `start_soon` replaces it.
- **Unicode full-width digits** pasted into a test file look like ASCII but aren't valid Python. Cost real debugging time.

### Debugging methodology practiced
Mutation-tested each module before committing — deliberately broke the RTL and confirmed the tests caught it:
1. **regfile**: `registers[rd_addr + 1]` sent writes to the wrong register. Three tests failed; `test_x0_stays_zero` still passed, because it reads x0 and the read guard force-zeroes it regardless. Failures showed as `ValueError: Can't convert LogicArray to int` — the target register was never written, so it held X. A test surviving a mutation tells you something about which path it actually checks.
2. **decoder**: `rd` sliced as `[10:7]` instead of `[11:7]`. Both directed tests passed — `rd=3` is `00011` and `rd=10` is `01010`, bit 11 clear in both, so the narrow slice returned identical values. Only the all-ones test caught it.
3. **imem**: indexed with `addr` instead of `addr[7:2]`. `addr=0` passed (`mem[0]` either way), `addr=4` failed with a clean mismatch, and the unwritten-slot test hit an out-of-bounds read.

### Open items
- **Register file coverage gap**: only about five of 32 registers are tested. Closing it needs a loop writing a unique value per register — identical values wouldn't catch aliasing.
- **Silent program overrun**: zero-fill means running past the program returns `32'h00000000`, which isn't a legal instruction but nothing traps. A real CPU would.
- Not yet built: control unit, `cpu.sv` top-level integration.

### Reflection
The pattern worth naming, because it bit me three separate times: a test value coincided with the broken behavior and hid a bug. `rd=3` and `rd=10` under the slice mutation, opcode `0b0110011` in the all-ones test, `addr=0` under the imem index mutation. Before writing an assert, ask what wrong behavior would still produce this expected value. If the answer is "several," change the value.

The missing-`@` bug is the same family as the ALU's fake 3/3 from last week — output that doesn't mean what it appears to. Both looked like success. Neither was.

---


## 2026-07-18

**RV32I ALU shipped — reference model, constrained-random stimulus, and functional coverage. Mutation-tested.**

### What I built and did
- `alu.sv` — 10 operations: ADD, SUB, AND, OR, XOR, SLL, SRL, SRA, SLT, SLTU.
- `test_alu.py` — Python reference model, directed edge tests, constrained-random stimulus, and hand-rolled functional coverage.

### Verification lessons
- **Green means nothing until you've seen it go red.** The first run reported 3/3 PASS, but every test body was `pass` — cocotb reported three passing tests that checked nothing. The tell was SIM TIME `0.00ns`: no `await` ever fired, so no simulation time elapsed. A test that can't fail isn't a test.
- **Reference models must come from the spec, not from reading your own RTL** — otherwise the test only confirms the RTL matches itself.
- **Verification effort should scale with design complexity.** The ALU has ~2^64 input combinations plus subtle signed/unsigned and shift-masking edge cases, so it earned a reference model, constrained-random stimulus, and coverage. A bit-slicing decoder, by contrast, only needs a handful of directed tests.

### Debugging methodology practiced
1. **Mutation**: removed `$signed()` from SRA, turning it into SRL. All three tests failed loudly with precise messages, which confirmed the reference model was doing real work and not just tracking the RTL.

### Reflection
The fake 3/3 was the lesson of the project. Three green checkmarks that verified nothing is worse than a red failure, because it feels like progress. Now I don't trust a passing test until I've watched it fail on a mutation.

---


## 2026-06-17 to 2026-07-08

**UART transmitter complete — 8N1 framing, parameterizable baud, 4-state FSM, 2/2 cocotb tests passing.**

### What I built and did
- Jun 17: set up the UART project — empty module scaffold with 2/2 cocotb passing. Repo hygiene: removed a `.save` backup, added `*.save` to `.gitignore`, added the counter dumpfile.
- Jul 8: `uart_tx.sv` complete — 8N1 framing, parameterizable baud rate, four-state FSM (IDLE / START / DATA / STOP), 2/2 cocotb tests passing.
- Added `CLAUDE.md` project context.

### Open items
- UART receiver (`uart_rx.sv`) + loopback test — optional extension, not started.

---


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
