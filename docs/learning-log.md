# Learning Log

Notes documenting my progression in chip design and computer architecture. Started May 2026, logging until end of summer.

## Format

Each entry contains:
- **Date** (YYYY-MM-DD)
- **Time spent** (rough hours)
- **What I did** (concrete actions)
- **What I learned** (key concepts, insights)
- **Stuck on / questions** (things to revisit)

## 2026-09-01 — Program counter mutation test (closing an audit gap)

**A portfolio audit flagged that every other module had a documented mutation but `program_counter` did not — the only `pc` fault in the log was the accidental unconnected-net bug found during CPU bring-up, which was luck, not a deliberate test. Closed that gap with two real mutations, both caught, RTL restored untouched. Run by Claude Code; I review here.**

### What was run
Baseline first (`test_program_counter.py`, 2/2 PASS), then one mutation at a time against `program_counter.sv`, reverting between each, then a final baseline to confirm restoration.

- **Mutation 1 — increment `pc <= pc + 32'd4` → `+ 32'd1`.** Caught by `test_pc_increments`: `AssertionError: After 1 clock cycle, pc should be 4, got 1`. `test_pc_resets_to_zero` still passed — reset is a separate path, unaffected by the increment amount. Clean one-to-one: the fault maps to exactly the test that targets it.
- **Mutation 2 — reset value `pc <= '0` → `pc <= 32'd4`.** Caught by *both* tests: `test_pc_resets_to_zero` directly (`should be 0, got 4`), and `test_pc_increments` as collateral (`should be 4, got 8`) because a wrong reset seed offsets every subsequent value.
- **Restore** — reverted to `+ 32'd4` and `'0`; baseline back to 2/2 PASS; `git diff` on the RTL clean.

### What I learned
- **Mutation testing validates the test, not the design.** A green suite only means something if a known-wrong RTL turns it red. Both mutations flipping the suite to FAIL is the actual evidence the two asserts have teeth — the same discipline the CPU-level integration mutations gave me, now applied to the one module that was missing it.
- **A mutation caught by two tests is redundancy, not extra coverage.** The reset mutation tripping both asserts tells me the increment test isn't independent of the reset value — it assumes reset lands at 0. That's fine here (reset is proven by its own test first), but worth noticing: collateral failures can mask *which* thing actually broke.
- The deprecated `units=` warning fired again on line 8 (audit finding #8) — still passing under cocotb 2.0.1, still needs migrating to `unit=`. Not fixed in this pass; logged.

## 2026-09-01 — First Vivado synthesis run (Basys 3 / Artix-7)

**First time pushing RTL through real synthesis + place + route in Vivado 2025.2, batch mode, targeting `xc7a35tcpg236-1`. Goal was post-implementation timing and area numbers, not a board program. Run done autonomously by Claude Code against untouched RTL; I review the numbers here.**

### What was run
- `build_regfile.tcl` — register file, out-of-context.
- `build_cpu.tcl` — full single-cycle core. Failed in implementation; see below.
- `build_bringup.tcl` — a throwaway 27-bit blink counter, taken end-to-end to a real bitstream to prove the whole flow (synth → opt → place → route → `write_bitstream`) works before the board arrives.

### The numbers that are real
- **`bringup_blink`** — closed timing at 100 MHz with **WNS +7.204 ns** (setup met), WHS +0.324 ns (hold met). Fmax ≈ 1000 / (10 − 7.204) ≈ **358 MHz**. **1 LUT, 27 flip-flops, 2 IOB.** Bitstream written (188,847 bytes). This is the only design in the run with a real register-to-register path, so it's the only meaningful Fmax.
- **`regfile` (out-of-context)** — **109 Slice LUTs (0.52% of the device)**: 65 as logic + 44 as distributed RAM. **0 flip-flops.** Vivado inferred the 32×32 array as LUTRAM, not 1024 discrete FFs — one write port, two async read ports maps naturally onto distributed RAM. Area is the useful number here; timing is not (next point).

### What I learned about synthesis vs. simulation
- **A register file has no register-to-register paths, so a clock period doesn't constrain anything inside it.** Every path is input→flop (write setup) or flop→output (read). With no I/O delay constraints, the timing report came back `WNS = NA`. There is no honest "closed timing at X MHz" claim for a regfile in isolation — that claim only means something once the block sits between other registers in the CPU. Simulation never made this distinction visible; synthesis does.
- **113 top-level ports won't fit a 106-pin package.** `regfile` exposes 113 signals (two 32-bit read buses + a 32-bit write bus + addresses + controls). The cpg236 package has 106 bonded user I/O. Placement failed on I/O overutilization until I switched to out-of-context synthesis, which is the correct way to characterize an internal block anyway — it never touches the chip boundary, so no I/O buffers and no pin placement. Good reminder that "number of ports" is a physical constraint, not just an interface choice.
- **A synthesis top with no observable outputs optimizes to nothing.** `cpu.sv` has only `clk` and `rst_n` — no outputs. Every phase of `opt_design` reported "removed 0 cells" only because the whole datapath was already unobservable and swept; `place_design` then errored `[Place 30-494] The design is empty`. The register writes are real in simulation because the testbench reaches into the hierarchy to read them, but to hardware, a value that never leaves the chip is dead logic. To get real CPU area/timing I need to expose something — a debug output port (e.g. the current instruction or a register value to the LEDs/an output bus), or `DONT_TOUCH` on the regfile. **Not an RTL bug; a design-completeness gap.** Full error saved to `vivado_cpu/error.log`.
- **`create_clock` needs an open, synthesized design.** The first script defined the clock with `[get_ports clk]` *before* `synth_design` — `get_ports` has no netlist to query yet, so it threw `[Common 17-53] No open design`, and Vivado's line-echo misattributed it to the preceding command. Fixed by moving `create_clock` to after `synth_design`. Cleaner still is to put the constraint in an XDC, which is how the bringup build does it.
- The Digilent master constraint file is `Basys-3-Master.xdc` (dashes around the 3), clock on pin **W5**, LD0 on **U16**. Everything ships commented out; you uncomment only the pins you use and match port names exactly.

### Open items
- **CPU can't be characterized until it has an observable output.** Decide between a debug output port and `DONT_TOUCH`. A debug port is the more honest choice — it's closer to how the design will actually be brought up on the board.
- No timing/area numbers for the CPU yet — the number that would actually matter (a real Fmax with logic between registers) is still pending that fix.
- `regfile` timing is unconstrained by construction; revisit with input/output delays only if I ever want I/O-path numbers, which I probably don't.

### Resume-ready (real numbers only)
- "Took RTL through synthesis, place-and-route, and bitstream generation in Vivado 2025.2 targeting a Xilinx Artix-7 (Basys 3, `xc7a35tcpg236-1`); closed timing at 100 MHz with 7.2 ns of setup slack (≈358 MHz Fmax)."
- "Characterized an RV32I register file out-of-context on Artix-7: 109 LUTs (0.5% of device), with the 32×32 array inferred as distributed RAM."
- Deliberately *not* claiming a CPU frequency — the top-level has no observable output yet, so its logic optimizes away. Recorded as an open item rather than a fabricated number.

## 2026-08-12 to 2026-09-01

**Single-cycle RV32I core complete — six modules integrated in cpu.sv, executing R-type programs, with four CPU-level tests and integration mutation testing.**

### What I built and did
- `cpu.sv` — top-level integration. Instantiates the program counter, imem, decoder, control unit, register file, and ALU, and wires them into a datapath. No new logic, all structural.
- `test_cpu.py` — four CPU-level tests plus helpers for loading programs into imem and seeding registers.
- Ran four integration mutations, each caught and restored.

### The integration bug worth remembering
`pc` was declared as an internal wire in `cpu.sv` but never connected to `u_pc`'s output port. Nothing drove it, so it sat at X forever. That X flowed into imem's address, the decoder split X into X fields, the register file read X, the ALU computed X, and X landed in x3. Every downstream symptom traced to one missing connection.

**An undriven net produces full-width X, not a wrong value.** A logic bug gives you an incorrect number; X means no driver, or an X input. When an entire output is X, look for a floating net before debugging the logic. Icarus does not warn about a forgotten named port connection — the module simply doesn't drive it.

### Verification lessons
- **A CPU-level testbench needs its own scaffolding.** Registers can't be seeded through the regfile's write port, because `rd_addr`, `rd_data` and `we` are already driven by the decoder, ALU and control inside `cpu.sv` — driving them from the testbench too puts X on those nets. Writing the array directly (`dut.u_regfile.registers[addr].value`) bypasses the conflict. Scaffolding only; it goes away once `addi` exists and programs can initialise their own registers.
- **The dependent-instruction test is the one that proves the writeback path connects.** A program where every instruction reads only seeded registers would pass even if writeback were subtly wrong. `sub x3, x1, x2` followed by `add x4, x3, x2` forces the second instruction to read what the first wrote.
- **Testing x0 at integration level can't inspect `registers[0]` directly.** With no reset, that slot holds X whether or not the write-block worked — so an assert against 0 fails on correct hardware. Reading x0 *through the datapath* (`add x3, x0, x0`) exercises both guards and observes it the way real code would.
- **An overrun test with an all-zero instruction cannot fail.** `0x00000000` has `rd` = bits [11:7] = 0, so even with `reg_write` stuck high the write targets x0, which is blocked anyway. Nothing observable changes. Replacing the overrun word with `0x00000FFF` gives `rd` = 31, so a broken opcode gate visibly clobbers a register. Confirmed by mutating `control.sv`'s check to `if (1'b1)` — the test failed with the nonzero word and would have passed with zeros.
- **Canary values must be ones the bug cannot accidentally produce.** With `we` tied high, `0x00000FFF` decodes rs1=0 and rs2=0, so the ALU computes 0+0 and writes 0 to x31. Seeding x31 with `0xABCD` catches that; seeding it with 0 would not, because the corrupt value equals the expected value.
- **Commutative operations cannot detect operand order.** Swapping `operand_a` and `operand_b` failed only the two tests containing SUB. The x0 and overrun tests use ADD exclusively and are structurally blind to that mutation.

### Integration mutations run
1. **`pc` unconnected** — every test failed with X in the result register. Found during bring-up rather than as a deliberate mutation.
2. **ALU operands swapped** — tests 1 and 2 failed (both contain SUB); tests 3 and 4 passed, being ADD-only.
3. **`we` tied high** — caught by the overrun test's x31 canary, but only after changing the overrun instruction from `0x00000000` to `0x00000FFF`.
4. **`rd_data` connected to `rs1_data` instead of `alu_result`** — three of four failed. `test_x0_stays_zero` passed because `rs1_data` reads x0 as 0, which is also the expected result.

### The pattern, now on its fourth and fifth instance
A test value that coincides with the broken behaviour hides the bug. So far: `rd=3` and `rd=10` under the decoder slice mutation; opcode `0b0110011` in the all-ones test; `addr=0` under the imem index mutation; commutative operations under the operand swap; and a zero-valued canary under the stuck write-enable.

Before writing an assert, ask what *wrong* behaviour would still produce this expected value. If the answer is "several," change the value.

### Open items
- Only ADD, SUB and AND are exercised end-to-end. The other seven ALU operations are verified at unit level but never run through the full datapath.
- `test_r_type_program` relies on imem's hardcoded contents rather than calling `load_program`, making it order-dependent in principle.
- Register seeding reaches into the module hierarchy. Remove once I-type exists.

### Next
Phase 2 — I-type immediates. Extend the decoder to extract immediates, add sign extension and an `alu_src` mux, teach control opcode `0010011`. Unlocks `addi`, which removes the seeding scaffolding.

### Reflection
Integration was the phase I'd expected to be hardest, and it was — but not for the reason I anticipated. The wiring itself was mechanical. What took the time was one forgotten port connection that produced a failure mode indistinguishable from a broken datapath. The lesson generalises: at integration level, the first question on a wrong result should be "what's undriven," not "what's my logic doing wrong."

The mutation testing was more informative here than at unit level. Three of the four mutations were survived by at least one test, and in every case the reason was structural — the test couldn't distinguish correct from broken given the operations and values it used. That's a sharper version of something I'd already seen at module level.

## 2026-08-06 to 2026-08-11

**Control unit built and verified; ALU op encoding moved into a shared package. Six modules now verified — the datapath is complete except for top-level integration.**

### What I built and did
- `control.sv` — R-type control unit. Takes opcode, funct3, funct7; outputs `alu_op` and `reg_write`. Two directed tests: all ten R-type operations decode correctly, and a non-R-type opcode leaves `reg_write` low.
- `riscv_pkg.sv` — package holding the `alu_op_t` enum, imported by both `alu.sv` and `control.sv`.
- Confirmed Vivado 2025.2 launches offline ahead of travel.

### Computer architecture lessons
- **Opcode gives the category, funct3 and funct7 give the operation.** All ten R-type arithmetic instructions share opcode `0110011`. funct3 narrows it to one operation or a pair; funct7 bit 30 separates the two pairs funct3 can't — ADD/SUB and SRL/SRA.
- **funct3 doesn't map onto my ALU encoding.** funct3 `001` is SLL but ALU code 1 is SUB. The RISC-V encoding was chosen in the spec for its own reasons; my ALU encoding was chosen by me. Control is a genuine translation layer, not a passthrough.
- **Datapath versus control.** The datapath (regfile, ALU, memories) is capable of many things and decides nothing. Control decides which of them happens this cycle. Control never sees data — only the instruction's identity. That separation is why adding loads later means teaching control a new opcode rather than rewriting the decoder.
- **A single-cycle CPU is one long combinational path** from the PC's output back to the register file's write-data input, with flip-flops at each end. Only two things are clocked: the PC advancing and the register write landing. The clock period must cover the whole path, which is why single-cycle designs are slow — every instruction pays the worst-case cost.
- **No instruction register in a single-cycle design.** An IR exists to hold an instruction *between* cycles. Fetch, decode, and execute all happen within one period here, so there's nothing to hold across. The IR reappears as the IF/ID pipeline register when I pipeline.

### SystemVerilog lessons
- **Packages are for shared declarations, not hardware.** `package riscv_pkg; ... endpackage` holds types and parameters; nothing is instantiated. `import riscv_pkg::*;` before the module. The package must come first in `VERILOG_SOURCES` or Icarus reports "unknown type alu_op_t" — compile order matters for packages in a way it doesn't for modules.
- **Typing a port as `alu_op_t` instead of `logic [3:0]`** is the payoff for the package — the type carries the meaning, and a mismatch becomes a compile error rather than a silent wrong encoding.
- **`always_comb` needs every output assigned on every path.** Assign both outputs unconditionally at the top, then override inside the branch. Without the top-level default, the non-R-type path leaves `alu_op` unassigned and the synthesizer infers a latch — a real bug in combinational logic, not a style issue.
- **Everything between blocks in a module is concurrent.** An `assign` isn't an instruction that executes; it's a permanent connection. Where it sits in the file relative to an `initial` or `always_ff` block has no effect. Only statements *inside* a procedural block are ordered — which is why the zero-fill loop must come before the instruction writes in imem.
- **Packed versus unpacked dimensions.** `logic [31:0] mem [0:63]` — the dimension before the name is how wide one element is (packed, behaves like a number), the dimension after is how many elements there are (unpacked, behaves like a collection). `mem + 1` is meaningless; `mem[5] + 1` isn't.
- **Storage goes in the module body, not the port list.** Ports are the interface — what crosses the boundary. The array is implementation. There's also no such thing as a wire carrying "32 separate registers," so unpacked arrays can't be ports in any synthesizable sense.

### Verification lessons
- **Mutation:** removed the `funct7 = 0100000` branch so SUB fell through to the default and decoded as ADD. The SUB check caught it. The ADD/SUB and SRL/SRA pairs are the whole point of the test — a control unit that ignored funct7 entirely would pass if I'd only tested one of each pair.
- **The non-R-type test is what proves the opcode gate exists.** Without it, control would happily decode a load as an arithmetic op and nothing would notice — everything in imem is R-type right now, so it would work by luck until it didn't.
- **A failure message should name the case.** `f"funct3={funct3:03b} funct7={funct7:07b}: expected {name}, got {name}"` tells me which of ten operations broke. A bare assert tells me nothing.

### Tooling
- Set up Ollama with Qwen 2.5 Coder 7B (fits 8GB VRAM on the RTX 5060) and Continue in VS Code, ahead of losing Claude access while travelling.
- Ollama's installer needs `zstd` on Ubuntu — `sudo apt-get install zstd` first.
- Small local models emit hallucinated tool calls when asked open-ended questions like "any mistakes in this?" Narrow, symptom-specific prompts with the file attached work; broad review requests produce confident generic output.

### Open items
- `cpu.sv` top-level integration — instantiate all six modules and wire them. Two things to remember: the regfile takes `clk` but no `rst_n`, and the first program test will read x1 and x2 before anything writes them, so they must be seeded through the write port from the testbench (there's no `addi` yet to load constants).
- After that: I-type immediates, then loads/stores, branches, data memory. Then pipelining.

### Working conditions
Travelling in China Aug 12–29. Claude is unavailable in the region, so assistance is DeepSeek's web interface plus local Qwen via Ollama. Written `PROJECT_CONTEXT.md` at the repo root to paste in as context, since neither tool carries state between sessions. Plan is to favour bounded work — extending the decoder to I-type from the RISC-V spec — over open-ended debugging, since integration bugs are the thing a small model is least able to help with.

### Reflection
The control unit was the smallest module so far and the one where I most clearly understood *why* each line was there before writing it. That's a change from the register file, where I was still working out the reset question mid-build.

The thing I'd do differently this week: too much of Aug 11 went to tooling — Ollama, Continue, VPN questions, model comparisons — the night before a flight, when integration was the thing that actually mattered. The setup was worth doing; doing it instead of `cpu.sv` was not.

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
