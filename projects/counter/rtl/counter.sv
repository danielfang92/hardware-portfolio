// 4-bit binary counter with async reset and enable
// Counts 0->15 then wraps to 0 b/c 4 bit overflow
// Daniel Fang

module counter #(parameter int WIDTH = 4) ( input logic clk, input logic rst_n, input logic en, output logic [WIDTH-1:0] count);

always_ff @ (posedge clk or negedge rst_n) begin

	if (!rst_n)
		count <= 4'b0000;

	else if (en)
		count <= count + 4'b0001;
	end

endmodule

 
		
		  

