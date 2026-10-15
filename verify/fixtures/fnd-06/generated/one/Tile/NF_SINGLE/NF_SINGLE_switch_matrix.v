 // NumberOfConfigBits: 1
module NF_SINGLE_switch_matrix
    #(
        parameter NoConfigBits=1
    )
    (
        input  L_O,
        input  L_Co,
        input  P_X0,
        input  P_X1,
        input  P_X2,
        input  P_X3,
        input  P_XA,
        input  P_XE,
        input  P_XR,
        output  L_I0,
        output  L_I1,
        output  L_I2,
        output  L_I3,
        output  L_Ci,
        output  L_SR,
        output  L_EN,
        output  P_RESULT,
 //global
        input  [NoConfigBits-1:0] ConfigBits,
        input  [NoConfigBits-1:0] ConfigBits_N
);
parameter GND0 = 1'b0;
parameter GND = 1'b0;
parameter VCC0 = 1'b1;
parameter VCC = 1'b1;
parameter VDD0 = 1'b1;
parameter VDD = 1'b1;

wire[2-1:0] L_I0_input;
 //The configuration bits (if any) are just a long shift register
 //This shift register is padded to an even number of flops/latches
 //switch matrix multiplexer L_I0 MUX-2
assign L_I0_input = {P_XA,P_X0};
cus_mux21 inst_cus_mux21_L_I0 (
    .A0(L_I0_input[0]),
    .A1(L_I0_input[1]),
    .S(ConfigBits[0+0]),
    .X(L_I0)
);

 //switch matrix multiplexer L_I1 MUX-1
assign L_I1 = P_X1;

 //switch matrix multiplexer L_I2 MUX-1
assign L_I2 = P_X2;

 //switch matrix multiplexer L_I3 MUX-1
assign L_I3 = P_X3;

 //switch matrix multiplexer L_Ci MUX-1
assign L_Ci = GND0;

 //switch matrix multiplexer L_EN MUX-1
assign L_EN = P_XE;

 //switch matrix multiplexer L_SR MUX-1
assign L_SR = P_XR;

 //switch matrix multiplexer P_RESULT MUX-1
assign P_RESULT = L_O;

endmodule