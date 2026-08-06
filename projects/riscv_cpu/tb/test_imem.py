"""cocotb testbenches for RV32I instruction memory"""
# TO RUN IN MAKEFILE: make MODULE=test_imem TOPLEVEL=imem VERILOG_SOURCES=../rtl/imem.sv
import cocotb
from cocotb.triggers import Timer


@cocotb.test()    
async def test_imem_zero_fills(dut):
# test slots past the program to ensure they are zero-filled
    dut.addr.value = 144
    await Timer(1, unit="ns")
    assert dut.instruction.value == 0, f"instruction should be 0, got {int(dut.instruction.value)}"
    
@cocotb.test()
async def test_imem_increment(dut):
#test that the instruction memory returns the correct instruction for each address increment
    dut.addr.value = 0
    await Timer(1, unit="ns")
    assert dut.instruction.value == 0x002081B3, f"instruction should be 0x002081B3, got {hex(int(dut.instruction.value))}"
    dut.addr.value = 4
    await Timer(1, unit="ns")
    assert dut.instruction.value == 0x40208233, f"instruction should be 0x40208233, got {hex(int(dut.instruction.value))}"  
    dut.addr.value = 8
    await Timer(1, unit="ns")
    assert dut.instruction.value == 0x0020F2B3, f"instruction should be 0x0020F2B3, got {hex(int(dut.instruction.value))}"


