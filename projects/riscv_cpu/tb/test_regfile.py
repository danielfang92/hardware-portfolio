"""cocotb testbenches for RV32I register file"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer



async def setup(dut):
	cocotb.start_soon (Clock(dut.clk, 10, units="ns").start())
	dut.we.value = 0      
	dut.rd_addr.value = 0
	dut.rd_data.value = 0
	dut.rs1_addr.value = 0
	dut.rs2_addr.value = 0
	await RisingEdge(dut.clk) 
