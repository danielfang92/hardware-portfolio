//RV32I instruction memory 
//Daniel Fang

module imem (
    input logic [31:0] addr,
    output logic [31:0] instruction
);
    
logic [31:0] mem [0:63];

assign instruction = mem[addr[7:2]];

integer i;
initial begin
    for (i=0; i<64; i=i+1) begin
        mem[i] = 32'd0;
    end

    mem[0] = 32'h002081B3;
    mem[1] = 32'h40208233;
    mem[2] = 32'h0020F2B3;
end

endmodule
