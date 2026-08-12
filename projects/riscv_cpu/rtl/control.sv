//RISC-V Control Unit, R-type only
//Daniel Fang


import riscv_pkg::*;

module control (
    input  logic [6:0] opcode,
    input  logic [2:0] funct3,
    input  logic [6:0] funct7,
    output alu_op_t    alu_op,
    output logic       reg_write
);

always_comb begin
    reg_write = 1'b0;
    alu_op = ALU_ADD;
    if (opcode == 7'b0110011) begin // R-type
        reg_write = 1'b1;
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
    end
end

endmodule