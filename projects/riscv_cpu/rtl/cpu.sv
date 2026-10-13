// RV32I single-cycle CPU — R-type + I-type (OP-IMM)
// Daniel Fang
//dataflow: pc>instruction memory> decoder >split into control and registerfile
`timescale 1ns/1ps
import riscv_pkg::*;

module cpu (
    input  logic        clk,
    input  logic        rst_n,
    // Write-back (commit) port: what the current instruction writes, and where
    // it came from. Without outputs, synthesis sees nothing observable and
    // removes the whole design, so these make the datapath real hardware.
    output logic        wb_en_o,
    output logic [4:0]  wb_rd_o,
    output logic [31:0] wb_data_o,
    output logic [31:0] pc_o
);

logic [31:0] pc, instruction;
logic [6:0] opcode, funct7;
logic [4:0] rd, rs1, rs2;
logic [2:0] funct3;
logic [31:0] rs1_data, rs2_data, alu_result, imm_i, operand_b;
alu_op_t     alu_op;
logic        reg_write, reg_we, zero, alu_src;


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

// No instruction retires while reset is held. The PC sits at 0 during reset,
// so instruction 0 is decoded on every edge; without this gate it would write
// the regfile each cycle (addi x1, x1, 1 would count up). Gated here rather
// than in control (pure decode, no notion of reset) or in regfile (a generic
// storage block with no reset input).
assign reg_we = reg_write & rst_n;

regfile u_regfile (
    .clk      (clk),
    .rs1_addr (rs1),
    .rs2_addr (rs2),
    .rs1_data (rs1_data),
    .rs2_data (rs2_data),
    .rd_addr  (rd),
    .rd_data  (alu_result),
    .we       (reg_we)
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

// Commit port. A write to x0 is discarded by the regfile, so report its data
// as 0 (the riscv-formal RVFI rule): the port shows what actually landed,
// not what the ALU happened to compute.
assign wb_en_o   = reg_we;     // report only writes that actually happen
assign wb_rd_o   = rd;
assign wb_data_o = (rd == 5'd0) ? 32'd0 : alu_result;
assign pc_o      = pc;


endmodule