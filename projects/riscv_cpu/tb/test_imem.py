"""cocotb testbenches for RV32I instruction memory"""
# Run with: make imem   (from projects/riscv_cpu/tb/)
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()    
async def test_imem_zero_fills(dut):
# test slots past the program to ensure they are zero-filled
    dut.we.value = 0
    dut.addr.value = 144
    await Timer(1, unit="ns")
    assert dut.instruction.value == 0, f"instruction should be 0, got {int(dut.instruction.value)}"
    
@cocotb.test()
async def test_imem_increment(dut):
#test that the instruction memory returns the correct instruction for each address increment
    dut.we.value = 0
    dut.addr.value = 0
    await Timer(1, unit="ns")
    assert dut.instruction.value == 0x002081B3, f"instruction should be 0x002081B3, got {hex(int(dut.instruction.value))}"
    dut.addr.value = 4
    await Timer(1, unit="ns")
    assert dut.instruction.value == 0x40208233, f"instruction should be 0x40208233, got {hex(int(dut.instruction.value))}"  
    dut.addr.value = 8
    await Timer(1, unit="ns")
    assert dut.instruction.value == 0x0020F2B3, f"instruction should be 0x0020F2B3, got {hex(int(dut.instruction.value))}"




@cocotb.test()
async def test_imem_write_port(dut):
#a write lands on the clock edge, at the word index given, and leaves neighbours alone
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.we.value = 1
    dut.waddr.value = 5
    dut.wdata.value = 0xDEADBEEF
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.we.value = 0
    dut.addr.value = 5 * 4                  # byte address of word 5
    await Timer(1, unit="ns")
    assert dut.instruction.value == 0xDEADBEEF, f"word 5 should be 0xDEADBEEF, got {hex(int(dut.instruction.value))}"
    dut.addr.value = 4 * 4                  # neighbour untouched
    await Timer(1, unit="ns")
    assert dut.instruction.value == 0, f"word 4 should still be 0, got {hex(int(dut.instruction.value))}"
    # we low: a write must not land
    dut.waddr.value = 5
    dut.wdata.value = 0x12345678
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    dut.addr.value = 5 * 4
    await Timer(1, unit="ns")
    assert dut.instruction.value == 0xDEADBEEF, f"write with we=0 landed: got {hex(int(dut.instruction.value))}"
