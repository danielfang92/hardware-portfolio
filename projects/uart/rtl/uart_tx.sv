//uart_tx.sv
// UART Transmitter: 8N1 framing, parameterizable baud rate
// Daniel Fang

module uart_tx #( parameter int baud_rate = 115_200, parameter int clk_freq_hz = 100_000)
( input logic clk, input logic rst_n, input logic [7:0] tx_data, input logic tx_start, 
output logic tx_serial, output logic tx_busy, output logic tx_done);


endmodule
