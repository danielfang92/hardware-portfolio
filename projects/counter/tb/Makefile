# Cocotb + Verilator setup for the counter project
# Run with: make

SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES = $(PWD)/../rtl/counter.sv

# Top-level module name (must match `module counter` in counter.sv)
TOPLEVEL = counter

# Python test module (must match test_counter.py filename, without .py)
MODULE = test_counter

# Enable waveform dump
#EXTRA_ARGS += --trace --trace-structs

	include $(shell cocotb-config --makefiles)/Makefile.sim
