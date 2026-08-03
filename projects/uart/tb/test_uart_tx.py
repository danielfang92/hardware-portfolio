"""Cocotb testbench for the UART transmitter."""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


# Must match the Makefile parameter override: 8 clocks per bit
CLKS_PER_BIT = 8
CLK_PERIOD_NS = 10


async def start_clock(dut):
    """Kick off the system clock."""
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD_NS, unit="ns").start())


async def reset_dut(dut):
    """Hold reset low for a few cycles, then release."""
    dut.rst_n.value = 0
    dut.tx_start.value = 0
    dut.tx_data.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, unit="ns") #output flip flops may need moment to propagate new values


async def sample_bit(dut):
    """Wait one full bit period, then return the value on tx_serial."""
    for _ in range(CLKS_PER_BIT):
        await RisingEdge(dut.clk)
    await Timer(1, unit="ns")
    return int(dut.tx_serial.value)


@cocotb.test()
async def test_idle_state(dut):
    """TX line should sit HIGH when not transmitting."""
    await start_clock(dut)
    await reset_dut(dut)
    # After reset, with no tx_start, the line must be idle high
    assert int(dut.tx_serial.value) == 1, \
        f"Idle line should be HIGH, got {int(dut.tx_serial.value)}"
    dut._log.info("Idle state test passed.")


@cocotb.test()
async def test_transmit_single_byte(dut):
    """Send one byte and verify the full 8N1 frame on the wire."""
    await start_clock(dut)
    await reset_dut(dut)

    test_byte = 0xA5  # 1010_0101

    # Pulse tx_start for one cycle with the data on the bus
    dut.tx_data.value = test_byte
    dut.tx_start.value = 1
    await RisingEdge(dut.clk)
    dut.tx_start.value = 0

    # The FSM moves IDLE -> START on this edge. We're now entering the start bit.
    # Sample the start bit (should be LOW)
    start_bit = await sample_bit(dut)
    assert start_bit == 0, f"Start bit should be LOW, got {start_bit}"

    # Sample the 8 data bits, LSB first
    for i in range(8):
        bit = await sample_bit(dut)
        expected = (test_byte >> i) & 1
        assert bit == expected, \
            f"Data bit {i}: expected {expected}, got {bit}"

    # Sample the stop bit (should be HIGH)
    stop_bit = await sample_bit(dut)
    assert stop_bit == 1, f"Stop bit should be HIGH, got {stop_bit}"

    dut._log.info("Single byte transmission test passed!")
