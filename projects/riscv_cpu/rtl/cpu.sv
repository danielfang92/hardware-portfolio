// RV32I single-cycle CPU — R-type only
// Daniel Fang
//dataflow: pc>instruction memory> decoder >split into control and registerfile
`timescale 1ns/1ps
import riscv_pkg::*;

module cpu (
    input logic clk,
    input logic rst_n
);

logic [31:0] pc, instruction;
logic [6:0] opcode, funct7;
logic [4:0] rd, rs1, rs2;
logic [2:0] funct3;
logic [31:0] rs1_data, rs2_data, alu_result, imm_i, operand_b;
alu_op_t     alu_op;
logic        reg_write, zero, alu_src;


program_counter u_pc (
    .clk (clk),
    .rst_n (rst_n),
    .pc (pc)
);

imem u_imem (
    .addr (pc),
    .instruction (instruction)
);

decoder u_decoder (
    .instruction (instruction),
    .opcode (opcode),
    .funct3 (funct3),
    .funct7 (funct7),
    .rd (rd),
    .rs1 (rs1),
    .rs2 (rs2),
    .imm_i (imm_i)
);

regfile u_regfile (
    .clk      (clk),
    .rs1_addr (rs1),
    .rs2_addr (rs2),
    .rs1_data (rs1_data),
    .rs2_data (rs2_data),
    .rd_addr  (rd),
    .rd_data  (alu_result),
    .we       (reg_write)
);
control u_control (
    .opcode (opcode),
    .funct3 (funct3),
    .funct7 (funct7),
    .alu_op (alu_op),
    .reg_write (reg_write),
    .alu_src (alu_src)
);

// operand_b mux: R-type takes rs2, I-type takes the sign-extended immediate
assign operand_b = alu_src ? imm_i : rs2_data;

alu u_alu (
    .operand_a (rs1_data),
    .operand_b (operand_b),
    .op (alu_op),
    .result (alu_result),
    .zero (zero)
);


endmodule