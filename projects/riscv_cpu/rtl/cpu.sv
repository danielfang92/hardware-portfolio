// RV32I single-cycle CPU — R-type only
// Daniel Fang
//dataflow: pc>instruction memory> decoder >split into control and registerfile
import riscv_pkg::*;

module cpu (
    input logic clk,
    input logic rst_n
);

logic [31:0] pc, instruction;
logic [6:0] opcode, funct7;
logic [4:0] rd, rs1, rs2;
logic [2:0] funct3;
logic [31:0] rs1_data, rs2_data, alu_result;
alu_op_t     alu_op;
logic        reg_write, zero;


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
    .rs2 (rs2)
);

regfile u_regfile (
    .clk      (clk),
    .rs1_addr (rs1),
    .rs2_addr (rs2),
    .rs1_data (rs1_data),
    .rs2_data (rs2_data),
    .rd_addr  (rd),
    .rd_data  (rs1_data),
    .we       (reg_write)
);
control u_control (
    .opcode (opcode),
    .funct3 (funct3),
    .funct7 (funct7),
    .alu_op (alu_op),
    .reg_write (reg_write)
);

alu u_alu (
    .operand_a (rs1_data),
    .operand_b (rs2_data),
    .op (alu_op),
    .result (alu_result),
    .zero (zero)
);


endmodule