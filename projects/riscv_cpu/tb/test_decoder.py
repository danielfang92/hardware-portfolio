"""cocotb testbenches for RV32I decoder (R-Type fields)"""
# TO RUN IN MAKEFILE: make MODULE=test_decoder TOPLEVEL=decoder VERILOG_SOURCES=../rtl/decoder.sv

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

def make_r_type(funct7, rs2, rs1, funct3, rd, opcode):
#Construct a 32-bit R-Type instruction from its fields
    return (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode


@cocotb.test()
async def test_add_fields(dut):
#Decode 'add x3, x1, x2' and check every field   
    dut.instruction.value = make_r_type(funct7=0b0000000, rs2=2, rs1=1, funct3=0b000, rd=3, opcode=0b0110011) 
    await Timer(1, "ns") 
    assert dut.opcode.value == 0b0110011, f"opcode wrong: {hex(int(dut.opcode.value))}"
    assert dut.rd.value == 3,             f"rd wrong: {int(dut.rd.value)}"
    assert dut.funct3.value == 0b000,     f"funct3 wrong: {int(dut.funct3.value)}"
    assert dut.rs1.value == 1,            f"rs1 wrong: {int(dut.rs1.value)}"
    assert dut.rs2.value == 2,            f"rs2 wrong: {int(dut.rs2.value)}"
    assert dut.funct7.value == 0b0000000, f"funct7 wrong: {hex(int(dut.funct7.value))}"
    
@cocotb.test()
async def test_sub_fields(dut):
#Decode 'sub x10, x20, x5' and check every field
    dut.instruction.value = make_r_type(funct7=0b0100000,  rs2=5, rs1=20, funct3=0b000, rd=10, opcode=0b0110011)
    await Timer(1, "ns")
    assert dut.opcode.value == 0b0110011, f"opcode wrong: {hex(int(dut.opcode.value))}"
    assert dut.rd.value == 10,            f"rd wrong: {int(dut.rd.value)}"
    assert dut.funct3.value == 0b000,     f"funct3 wrong: {int(dut.funct3.value)}"
    assert dut.rs1.value == 20,           f"rs1 wrong: {int(dut.rs1.value)}"
    assert dut.rs2.value == 5,            f"rs2 wrong: {int(dut.rs2.value)}"
    assert dut.funct7.value == 0b0100000, f"funct7 wrong: {hex(int(dut.funct7.value))}" 
    
@cocotb.test()
async def test_all_ones(dut):
#Max field values: fake instruction with every field bit set, to catch slice-width bugs
    dut.instruction.value = make_r_type(funct7=0b1111111, rs2=0b11111, rs1=0b11111, funct3=0b111, rd=0b11111, opcode=0b1111111)
    await Timer(1, "ns")
    assert dut.opcode.value == 0b1111111, f"opcode wrong: {hex(int(dut.opcode.value))}"
    assert dut.rd.value == 0b11111,             f"rd wrong: {int(dut.rd.value)}"
    assert dut.funct3.value == 0b111,     f"funct3 wrong: {int(dut.funct3.value)}"
    assert dut.rs1.value == 0b11111,            f"rs1 wrong: {int(dut.rs1.value)}"
    assert dut.rs2.value == 0b11111,            f"rs2 wrong: {int(dut.rs2.value)}"
    assert dut.funct7.value == 0b1111111, f"funct7 wrong: {hex(int(dut.funct7.value))}"
    