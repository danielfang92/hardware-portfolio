// uart_tx.sv
// UART transmitter: 8N1 framing, parameterizable baud rate
// Daniel Fang

module uart_tx #(
    parameter int CLK_FREQ_HZ = 100_000_000,
    parameter int BAUD_RATE   = 115_200
) (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] tx_data,
    input  logic       tx_start,
    output logic       tx_serial,
    output logic       tx_busy,
    output logic       tx_done
);

    // How many clock cycles make up one UART bit at the chosen baud rate
    localparam int BAUD_DIVIDER = CLK_FREQ_HZ / BAUD_RATE;

    // The four states the transmitter moves through for each byte
    typedef enum logic [1:0] {
        IDLE  = 2'b00,
        START = 2'b01,
        DATA  = 2'b10,
        STOP  = 2'b11
    } state_t;

    // Which state we're currently in
    state_t state;

    // Counts clock cycles so we know when one bit period has elapsed
    logic [15:0] baud_counter;

    // Tracks which of the 8 data bits we're sending right now
    logic [2:0] bit_index;

    // Holds a copy of the byte we're transmitting so the caller can change tx_data freely
    logic [7:0] data_latched;

    // Goes high for one cycle each time a full bit period completes
    logic baud_tick;

    // Baud counter: counts up every clock, wraps when it reaches one bit period.
    // Stays at zero while idle so each new byte starts on a clean bit boundary.
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            baud_counter <= 16'd0;
        end else if (state == IDLE) begin
            baud_counter <= 16'd0;
        end else if (baud_counter == BAUD_DIVIDER - 1) begin
            baud_counter <= 16'd0;
        end else begin
            baud_counter <= baud_counter + 16'd1;
        end
    end

    // baud_tick pulses high exactly when the counter hits the end of a bit period
    assign baud_tick = (baud_counter == BAUD_DIVIDER - 1);

//Transmitter FSM
always_ff @ (posedge clk or negedge rst_n) begin
	if (!rst_n) begin
		state <= IDLE;
		bit_index <= 3'b0;
		data_latched <= 8'b0;
		tx_serial <= 1'b1;
		tx_busy <= 1'b0;
		tx_done <= 1'b0;	
	end 
	else begin tx_done <=1'b0;

	case (state)
		IDLE: begin
			tx_serial = 1'b1;
			tx_busy = 1'b0;
			if (tx_start) begin
				data_latched = tx_data;
				state <= START;
				tx_busy <= 1'b1;
			end
		end

		START: begin
			tx_serial = 1'b0;
			if (baud_tick) begin
			state <= DATA;
			bit_index <= 3'b0;
			end
		end	
		
		DATA: begin
			tx_serial = data_latched[bit_index];
			if (baud_tick) begin
				if (bit_index = 3'd7) begin
					state <= STOP;
				end else begin
					bit_index <= bit_index + 3'd1;
				end
				
		end
	end

		 STOP: begin
			tx_serial <= 1'b1;
			if (baud_tick) begin
                        state   <= IDLE;
                        tx_done <= 1'b1;
                        end
                end

		default: begin
                	state <= IDLE;
                end
            endcase
        	end
	end



endmodule



