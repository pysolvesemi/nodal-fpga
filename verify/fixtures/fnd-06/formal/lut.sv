// Independent contract; actual archived source LUT and models_pack are DUT inputs.
module lut_formal;
  (* anyconst *) reg [15:0] init;
  (* anyconst *) reg [3:0] inputs;
  wire observed;
  wire expected = (init >> (inputs[0]+2*inputs[1]+4*inputs[2]+8*inputs[3])) & 1;
  LUT4c_frame_config_dffesr dut(.I(inputs),.O(observed),.Ci(1'b0),.Co(),
    .SR(1'b0),.EN(1'b0),.UserCLK(1'b0),.ConfigBits({3'b000,init}));
  always @* begin
    // A-LUT-ALL
    A_LUT_ALL: assert(observed == expected);
    // C-LUT-A6D3-A1
    C_LUT_A6D3_A1: cover(init==16'hA6D3 && inputs==4'b0001 && observed==1);
    // C-LUT-A6D3-A8
    C_LUT_A6D3_A8: cover(init==16'hA6D3 && inputs==4'b1000 && observed==0);
    // C-LUT-ONEHOT-HIT
    C_LUT_ONEHOT_HIT: cover(init==16'h0002 && inputs==4'b0001 && observed==1);
    // C-LUT-ONEHOT-MISS
    C_LUT_ONEHOT_MISS: cover(init==16'h0002 && inputs==4'b1000 && observed==0);
  end
endmodule
