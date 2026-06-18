"""Cocotb testbench for UART transmitter"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def test_idle_state(dut):
	"""Verify TX line stays HIGH when idling"""



@cocotb.test()
async def test_transmit_single_byte(dut):
	"""Verify TX correctly sends one byte"""


