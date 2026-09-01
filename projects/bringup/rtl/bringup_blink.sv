module bringup_blink (
    input  logic clk,     // 100 MHz onboard clock
    output logic led
);
    logic [26:0] counter = 0;
    always_ff @(posedge clk) counter <= counter + 1;
    assign led = counter[26];  // ~0.75 Hz blink
endmodule
