# Top-level regression driver for the hardware portfolio.
#
# Each project under projects/ carries its own cocotb Makefile that sets its own
# TOPLEVEL / MODULE / VERILOG_SOURCES / COMPILE_ARGS. Those are per-DUT and
# cannot share one variable namespace (uart's -P baud overrides would leak into
# the counter build), so every target below re-invokes make in a fresh
# sub-process with -C. Same reasoning as the per-module targets in
# projects/riscv_cpu/tb/Makefile.
#
#   make            # full regression, stops on the first failing project
#   make alu        # one project
#   make clean      # remove sim_build dirs, waveforms and results.xml
#
# Environment (see README.md):
#   python3 -m venv env && source env/bin/activate
#   pip install -r requirements.txt

PROJECTS := counter uart alu cpu

# Target name -> testbench directory. The cpu target's directory does not match
# its name, so the mapping is explicit rather than derived from the target.
DIR_counter := projects/counter/tb
DIR_uart    := projects/uart/tb
DIR_alu     := projects/alu/tb
DIR_cpu     := projects/riscv_cpu/tb

.PHONY: all $(PROJECTS) clean

# cocotb-config ships inside the venv, and every project Makefile calls it to
# locate Makefile.sim. Without this guard a missing venv fails deep inside a
# sub-make with a bare "cocotb-config: command not found". $(error) fires at
# parse time, so it stops before any project runs. Skipped for `clean`, which
# needs no simulator.
ifneq ($(MAKECMDGOALS),clean)
ifeq ($(shell command -v cocotb-config 2>/dev/null),)
$(error cocotb not found. Set up the environment first: python3 -m venv env && source env/bin/activate && pip install -r requirements.txt)
endif
endif

# Prerequisites run left to right and make aborts on the first non-zero exit,
# so a failing project is never buried under later output.
all: $(PROJECTS)

$(PROJECTS):
	$(MAKE) -C $(DIR_$@)

clean:
	@for d in $(foreach p,$(PROJECTS),$(DIR_$(p))); do \
	    $(MAKE) -C $$d clean; \
	done
	rm -rf $(foreach p,$(PROJECTS),$(DIR_$(p))/sim_build)
