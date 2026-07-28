//32-bit ALU
//Daniel Fang





module alu (
	input logic [31:0] operand_a, 
	input logic [31:0] operand_b,
	input logic [3:0] op,
	output logic zero,
	output logic [31:0] result
	);

	
	typedef enum logic [3:0] {
	 ALU_ADD  = 4'b0000,   // 0
   	 ALU_SUB  = 4'b0001,   // 1
   	 ALU_AND  = 4'b0010,   // 2
   	 ALU_OR   = 4'b0011,   // 3
   	 ALU_XOR  = 4'b0100,   // 4
   	 ALU_SLL  = 4'b0101,   // 5
    	 ALU_SRL  = 4'b0110,   // 6
   	 ALU_SRA  = 4'b0111,   // 7
   	 ALU_SLT  = 4'b1000,   // 8
   	 ALU_SLTU = 4'b1001    // 9
} alu_op_t;
	 
	
	
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
