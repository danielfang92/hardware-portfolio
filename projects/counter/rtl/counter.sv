// WIDTH-bit binary counter with async reset and enable
// Counts 0 -> (2**WIDTH - 1) then wraps to 0 on overflow
// Daniel Fang

module counter #(parameter int WIDTH = 4) ( input logic clk, input logic rst_n, input logic en, output logic [WIDTH-1:0] count);

always_ff @ (posedge clk or negedge rst_n) begin

	if (!rst_n)
		count <= '0;                 // fills to WIDTH bits

	else if (en)
		count <= count + 1'b1;       // 1'b1 zero-extends to WIDTH in the add

	end

endmodule

 
		
		  

