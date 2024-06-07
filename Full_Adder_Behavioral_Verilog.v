module Full_Adder_Behavioral_Verilog( 
  input X1, 
  input X2, 
  input X3,
  input X4,
  input X5,
  input X6,
  input X7,
  input X8,
  input Cin, 
  output S, 
  output Cout
  );  
    reg[1:0] temp;
   always @(*)
   begin 
   temp = {1'b0,X1} + {1'b0,X2}+{1'b0,Cin};
   end 
   assign S = temp[0];
   assign Cout = temp[1];
endmodule  