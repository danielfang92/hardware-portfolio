// 32x32 register file for RV32I
// Daniel Fang

module regfile (
	input logic  clk,
	input logic [4:0] rs1_addr,
	input logic [4:0] rs2_addr,
	input logic [31:0] rd_data,
	input logic [4:0] rd_addr,
	input logic we,
	output logic [31:0] rs1_data,
	output logic [31:0] rs2_data
);

logic [31:0] registers [0:31];

assign rs1_data = (rs1_addr == 5'd0) ? 32'd0 : registers[rs1_addr];
assign rs2_data = (rs2_addr == 5'd0) ? 32'd0 : registers[rs2_addr];

// No reset,software initializes registers before use.
always_ff @ (posedge clk) begin
	if (we && rd_addr != 5'd0) begin
		registers[rd_addr] <= rd_data;
	end
end
	
endmodule
