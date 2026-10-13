//RISC-V Control Unit, R-type only
//Daniel Fang
`timescale 1ns/1ps

import riscv_pkg::*;

module control (
    input  logic [6:0] opcode,
    input  logic [2:0] funct3,
    input  logic [6:0] funct7,
    output alu_op_t    alu_op,
    output logic       reg_write,
    output logic       alu_src
);

always_comb begin
    reg_write = 1'b0;
    alu_op    = ALU_ADD;
    alu_src   = 1'b0;                   // default: operand_b comes from rs2
    if (opcode == OPCODE_R_TYPE) begin // R-type: reg-reg, operand_b = rs2
        reg_write = 1'b1;
        alu_src   = 1'b0;
        case (funct3)
            3'b000: case (funct7) 
                7'b0000000: alu_op = ALU_ADD;
                7'b0100000: alu_op = ALU_SUB;
                default:   alu_op = ALU_ADD;
            endcase       
            3'b001: alu_op = ALU_SLL;
            3'b010: alu_op = ALU_SLT;
            3'b011: alu_op = ALU_SLTU;
            3'b100: alu_op = ALU_XOR;
            3'b101: case (funct7) 
                7'b0000000: alu_op = ALU_SRL;
                7'b0100000: alu_op = ALU_SRA;
                default:   alu_op = ALU_SRL;
            endcase
            3'b110: alu_op = ALU_OR;
            3'b111: alu_op = ALU_AND;
            default: alu_op = ALU_ADD;
        endcase
    end else if (opcode == OPCODE_I_TYPE) begin // OP-IMM: reg-imm, operand_b = imm
        reg_write = 1'b1;
        alu_src   = 1'b1;
        case (funct3)
            3'b000: alu_op = ALU_ADD;   // ADDI  (no SUBI, so never checks funct7)
            3'b010: alu_op = ALU_SLT;   // SLTI
            3'b011: alu_op = ALU_SLTU;  // SLTIU
            3'b100: alu_op = ALU_XOR;   // XORI
            3'b110: alu_op = ALU_OR;    // ORI
            3'b111: alu_op = ALU_AND;   // ANDI
            3'b001: alu_op = ALU_SLL;   // SLLI  (shamt = imm[4:0])
            3'b101: case (funct7)       // SRLI / SRAI share funct3=101
                7'b0000000: alu_op = ALU_SRL;
                7'b0100000: alu_op = ALU_SRA;
                default:    alu_op = ALU_SRL;
            endcase
            default: alu_op = ALU_ADD;
        endcase
    end
end

endmodule