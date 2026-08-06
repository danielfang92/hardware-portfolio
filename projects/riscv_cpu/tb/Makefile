SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES ?= $(PWD)/../rtl/regfile.sv
TOPLEVEL ?= regfile
MODULE ?= test_regfile
SIM_BUILD ?= sim_build/$(TOPLEVEL)
include $(shell cocotb-config --makefiles)/Makefile.sim
