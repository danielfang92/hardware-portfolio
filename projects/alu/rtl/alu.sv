//32-bit ALU
//Daniel Fang

import riscv_pkg::*;


module alu (
	input logic [31:0] operand_a, 
	input logic [31:0] operand_b,
	input logic [3:0] op,
	output logic zero,
	output logic [31:0] result
	);

	
	
	
	always_comb begin
		case (op)
			ALU_ADD: result = operand_a + operand_b;
			ALU_SUB: result = operand_a - operand_b;
			ALU_AND: result = operand_a & operand_b;
			ALU_OR: result = operand_a | operand_b;
			ALU_XOR: result = operand_a ^ operand_b;
			ALU_SLL: result = operand_a << operand_b[4:0];
			ALU_SRL: result = operand_a >> operand_b[4:0];
			ALU_SRA: result = $signed(operand_a) >>> operand_b[4:0];
			ALU_SLT: result = ($signed(operand_a) < $signed(operand_b)) ? 32'd1:32'd0;
			ALU_SLTU: result = ($unsigned(operand_a) < $unsigned(operand_b)) ? 32'd1:32'd0;
			default: result = 32'd0;
		endcase
	end


	
	assign zero = (result == 32'd0);

endmodule
