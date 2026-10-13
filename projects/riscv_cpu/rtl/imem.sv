//RV32I instruction memory
//Daniel Fang
`timescale 1ns/1ps

module imem (
    input  logic        clk,
    // Write port: loads a program from outside. Because the contents can
    // change after synthesis, Vivado can't treat them as constants and fold
    // the decoder/control/ALU down to the few instructions in the init block.
    input  logic        we,
    input  logic [5:0]  waddr,          // word index (0-63), not a byte address
    input  logic [31:0] wdata,
    // Read port: combinational fetch, byte address from the PC
    input  logic [31:0] addr,
    output logic [31:0] instruction
);

logic [31:0] mem [0:63];

assign instruction = mem[addr[7:2]];

always_ff @(posedge clk) begin
    if (we) begin
        mem[waddr] <= wdata;
    end
end

// Power-on contents. A loaded program overwrites these.
integer i;
initial begin
    for (i=0; i<64; i=i+1) begin
        mem[i] = 32'd0;
    end

    mem[0] = 32'h002081B3; //add x3, x1, x2
    mem[1] = 32'h40208233; // sub x4, x1, x2
    mem[2] = 32'h0020F2B3; // and x5, x1, x2
end

endmodule
