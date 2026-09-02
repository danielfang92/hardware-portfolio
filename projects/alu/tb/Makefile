# Cocotb and Icarus Verilog build for the ALU
# Run with "make" (venv must be active: source ~/cocotb-env/bin/activate)

SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# alu.sv does `import riscv_pkg::*;`, and that package lives in the neighbouring
# riscv_cpu project. Icarus compiles sources in order, so the package must come
# BEFORE alu.sv or elaboration fails with "unknown type alu_op_t".
VERILOG_SOURCES = $(PWD)/../../riscv_cpu/rtl/riscv_pkg.sv $(PWD)/../rtl/alu.sv

# Top-level module name (must match the module in alu.sv)
TOPLEVEL = alu

# Python test file, without the .py extension
MODULE = test_alu

# No COMPILE_ARGS -P here: the ALU has no parameters to override.

	include $(shell cocotb-config --makefiles)/Makefile.sim
