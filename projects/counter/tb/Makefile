# Cocotb + Verilator setup for the counter project
# Run with: make

SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES = $(PWD)/../rtl/counter.sv

# Top-level module name (must match `module counter` in counter.sv)
TOPLEVEL = counter

# Python test module (must match test_counter.py filename, without .py)
MODULE = test_counter

# Waveform dump: cocotb's Icarus flow generates its own dump wrapper
# (sim_build/counter.fst) when WAVES=1. Override on the CLI with `make WAVES=0`.
WAVES ?= 1

	include $(shell cocotb-config --makefiles)/Makefile.sim
