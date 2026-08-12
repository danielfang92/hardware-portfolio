"""cocotb testbenches for RV32I register file"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def setup(dut):
# # Init inputs to 0 to avoid undefined X on startup
	cocotb.start_soon (Clock(dut.clk, 10, unit="ns").start())


async def write_reg(dut, addr, data):
# Write 'data' into register 'addr', then drop write-enable
	dut.rd_addr.value = addr
	dut.rd_data.value = data
	dut.we.value = 1
	await RisingEdge(dut.clk)    
	dut.we.value = 0
	await Timer(1, unit="ns")


@cocotb.test()
#Check correct value is written to a register
async def test_write_then_read(dut):
	await setup(dut)
	await write_reg(dut, 5, 0xDEADBEEF)
	dut.rs1_addr.value = 5
	await Timer (1, unit="ns")
	assert dut.rs1_data.value == 0xDEADBEEF, f"x5 expected 0xDEADBEEF, got {hex(int(dut.rs1_data.value))}"


@cocotb.test()
#Check writing non-zero value to x0 is discarded, x0 must always read 0
async def test_x0_stays_zero(dut):
	await setup(dut)
	await write_reg(dut, 0, 0xFFFFFFFF)
	dut.rs1_addr.value = 0
	await Timer (1, unit="ns")
	assert dut.rs1_data.value == 0, f"x0 must read 0, got {hex(int(dut.rs1_data.value))}"

@cocotb.test()
#Check nothing is written to a register when write enable is low
async def test_no_write_when_we_low(dut):
	await setup(dut)
	await write_reg(dut, 10, 0x12345678)
	dut.rd_addr.value = 10
	dut.rd_data.value = 0xFFFFFFFF
	dut.we.value = 0
	await RisingEdge(dut.clk)
	dut.rs1_addr.value = 10
	await Timer(1, unit="ns")
	assert dut.rs1_data.value == 0x12345678, f"x10 shouldn't change, (read 0x12345678), got {hex(int(dut.rs1_data.value))}"


@cocotb.test()
#both read ports return the correct, independent values at once
async def test_two_reads(dut):
	await setup(dut)
	await write_reg(dut, 3, 0xAAAAAAAA)
	await write_reg(dut, 7, 0x55555555)
	await Timer (1, unit="ns")
	dut.rs1_addr.value = 3
	dut.rs2_addr.value = 7
	await Timer(1, unit="ns")
	assert dut.rs1_data.value == 0xAAAAAAAA, f"port1 (x3) expected 0xAAAAAAAA, got {hex(int(dut.rs1_data.value))}"
	assert dut.rs2_data.value == 0x55555555, f"port2 (x7) expected 0x55555555, got {hex(int(dut.rs2_data.value))}"
