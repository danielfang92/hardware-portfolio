import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

async def reset_dut(dut):
    """Assert reset for a few cycles, then release."""
    dut.rst_n.value = 0
    dut.en.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


@cocotb.test()
async def test_reset_clears_count(dut):
    """Verify that asserting reset clears count to 0."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Apply reset
    dut.rst_n.value = 0
    dut.en.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  
    assert dut.count.value == 0,  f"After reset, count should be 0, got {int(dut.count.value)}"

    dut._log.info("Reset test passed.")


@cocotb.test()
async def test_count_up(dut):
    """Verify counter counts 0->15 in sequence."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    dut.en.value = 1

    for expected in range(1, 16):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")     
        actual = int(dut.count.value)
        assert actual == expected, \
            f"Cycle {expected}: expected {expected}, got {actual}"

    dut._log.info("Count-up test passed!")


@cocotb.test()
async def test_wrap_around(dut):
    """Verify counter wraps from 15 back to 0."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    dut.en.value = 1

    # Run 15 cycles to reach 15
    for _ in range(15):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")  
    assert dut.count.value == 15,  f"Expected count=15 before wrap, got {int(dut.count.value)}"

    # One more cycle should wrap to 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  
    assert dut.count.value == 0, f"Expected wrap to 0, got {int(dut.count.value)}"

    dut._log.info("Wrap-around test passed!")


@cocotb.test()
async def test_enable_holds(dut):
    """Verify counter holds its value when enable is low."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)

    # Count to 5
    dut.en.value = 1
    for _ in range(5):
        await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    held_value = int(dut.count.value)

    # Disable and check counter holds for 10 cycles
    dut.en.value = 0
    for _ in range(10):
        await RisingEdge(dut.clk)
        assert int(dut.count.value) == held_value, \
            f"Counter should hold at {held_value}, got {int(dut.count.value)}"

    dut._log.info("Enable-hold test passed!")
