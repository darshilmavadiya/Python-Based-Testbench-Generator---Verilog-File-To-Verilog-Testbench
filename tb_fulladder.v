/* 
This is the Auto-Generated testbench. 
Written by Darshil Mavadiya and Anant Kothivar 
*/

`include "timescale.v"
module tb_fulladder;

reg     [3:0]    a        ;
reg     [3:0]    b        ;
reg              c_in     ;
wire             c_out    ;

fulladder uut (
    .a        (    a        ),
    .b        (    b        ),
    .c_in     (    c_in     ),
    .c_out    (    c_out    )
);

parameter PERIOD = 10;

initial begin
    $dumpfile("db_tb_fulladder.vcd");
    $dumpvars(0, tb_fulladder);
    clk = 1'b0;
    #(PERIOD/2);
    forever
        #(PERIOD/2) clk = ~clk;

	#10 
	a = 1'b0, b = 1'b0, c_in = 1'b0
	#30 
	a = 1'b0, b = 1'b0, c_in = 1'b1
	#50 
	a = 1'b0, b = 1'b1, c_in = 1'b0
	#70 
	a = 1'b0, b = 1'b1, c_in = 1'b1
	#90 
	a = 1'b1, b = 1'b0, c_in = 1'b0
	#110 
	a = 1'b1, b = 1'b0, c_in = 1'b1
	#130 
	a = 1'b1, b = 1'b1, c_in = 1'b0
	#150 
	a = 1'b1, b = 1'b1, c_in = 1'b1

end
endmodule
