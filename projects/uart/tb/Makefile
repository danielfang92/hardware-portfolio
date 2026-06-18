# Cocotb and Icarus Verilog build for uart_tx
# Run with "make"

SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES = $(PWD)/../rtl/uart_tx.sv

TOPLEVEL = uart_tx

MODULE = test_uart_tx

	include $(shell cocotb-config --makefiles)/Makefile.sim




