// RV32I program counter
// Daniel Fang

module program_counter(
    input logic clk,
    input logic rst_n,
    output logic [31:0] pc
);

always_ff @ (posedge clk or negedge rst_n) begin

    if (!rst_n) begin
        pc <= '0;
    
    end else begin
        pc <= pc + 32'd4;
    end
end

endmodule

