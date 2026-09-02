# Cocotb + Icarus Verilog builds for the RISC-V CPU project.
#
# This project has several DUTs (the CPU and each sub-module), so there is no
# single TOPLEVEL. Use a named target per module; a bare `make` runs the whole
# suite and stops on the first failing module:
#
#   make            # full suite: regfile, imem, decoder, pc, control, cpu
#   make cpu        # just the CPU integration tests
#   make regfile    # just the register file  (imem, decoder, pc, control too)
#
# Each named target re-invokes this Makefile's `sim` target (cocotb's actual
# run) in a sub-process with the right TOPLEVEL / MODULE / VERILOG_SOURCES and
# its own SIM_BUILD dir (so one module's compiled netlist never gets reused for
# another). Source order matters: riscv_pkg.sv defines alu_op_t and must precede
# any module that imports it (control, cpu); cpu.sv also pulls the ALU from the
# neighbouring alu project.
#
# venv must be active:  source ~/cocotb-env/bin/activate

SIM ?= icarus
TOPLEVEL_LANG ?= verilog

RTL := $(PWD)/../rtl
PKG := $(RTL)/riscv_pkg.sv
ALU := $(PWD)/../../alu/rtl/alu.sv

.PHONY: test regfile imem decoder pc control cpu

# Bare `make` == full suite, sequential, stops on the first failing module.
test: regfile imem decoder pc control cpu

regfile:
	$(MAKE) sim TOPLEVEL=regfile MODULE=test_regfile SIM_BUILD=sim_build/regfile \
	    VERILOG_SOURCES="$(RTL)/regfile.sv"

imem:
	$(MAKE) sim TOPLEVEL=imem MODULE=test_imem SIM_BUILD=sim_build/imem \
	    VERILOG_SOURCES="$(RTL)/imem.sv"

decoder:
	$(MAKE) sim TOPLEVEL=decoder MODULE=test_decoder SIM_BUILD=sim_build/decoder \
	    VERILOG_SOURCES="$(RTL)/decoder.sv"

pc:
	$(MAKE) sim TOPLEVEL=program_counter MODULE=test_program_counter SIM_BUILD=sim_build/pc \
	    VERILOG_SOURCES="$(RTL)/program_counter.sv"

control:
	$(MAKE) sim TOPLEVEL=control MODULE=test_control SIM_BUILD=sim_build/control \
	    VERILOG_SOURCES="$(PKG) $(RTL)/control.sv"

cpu:
	$(MAKE) sim TOPLEVEL=cpu MODULE=test_cpu SIM_BUILD=sim_build/cpu \
	    VERILOG_SOURCES="$(PKG) $(RTL)/program_counter.sv $(RTL)/imem.sv $(RTL)/decoder.sv $(RTL)/control.sv $(RTL)/regfile.sv $(ALU) $(RTL)/cpu.sv"

# cocotb's Makefile.sim provides the actual `sim` target (plus `clean`).
include $(shell cocotb-config --makefiles)/Makefile.sim
