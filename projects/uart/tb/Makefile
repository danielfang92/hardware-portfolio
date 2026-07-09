# Cocotb and Icarus Verilog build for uart_tx
# Run with "make"

SIM ?= icarus
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES = $(PWD)/../rtl/uart_tx.sv

TOPLEVEL = uart_tx
# Override parameters for fast simulation: 8 clocks per bit instead of 868
COMPILE_ARGS += -P uart_tx.CLK_FREQ_HZ=1000000
COMPILE_ARGS += -P uart_tx.BAUD_RATE=125000

MODULE = test_uart_tx

	include $(shell cocotb-config --makefiles)/Makefile.sim




