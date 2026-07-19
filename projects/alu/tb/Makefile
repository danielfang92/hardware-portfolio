# Cocotb and Icarus Verilog build for the ALU
# Run with "make" (venv must be active: source ~/cocotb-env/bin/activate)

SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES = $(PWD)/../rtl/alu.sv

# Top-level module name (must match the module in alu.sv)
TOPLEVEL = alu

# Python test file, without the .py extension
MODULE = test_alu

# No COMPILE_ARGS -P here: the ALU has no parameters to override.

	include $(shell cocotb-config --makefiles)/Makefile.sim
