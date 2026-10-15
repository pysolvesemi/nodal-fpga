// Four actual generated switch DUTs. No configuration storage abstraction here.
module switch_SINGLE;
  (* anyconst *) reg local_input, secondary, select_input;
  wire observed;
  NF_SINGLE_switch_matrix dut(.P_X0(local_input),.P_X1(1'b0),.P_X2(1'b0),.P_X3(1'b0),
    .P_XA(secondary),.P_XE(1'b0),.P_XR(1'b0),.L_O(1'b0),.L_Co(1'b0),
    .L_I0(observed),.ConfigBits(select_input),.ConfigBits_N(~select_input));
  always @* begin
    // A-MUX-ORDER/NF_SINGLE
    A_MUX_ORDER: assert(observed == (select_input ? secondary : local_input));
    // C-MUX-LOCAL/NF_SINGLE
    C_MUX_LOCAL: cover(!local_input && secondary && !select_input && !observed);
    // C-MUX-SECONDARY/NF_SINGLE
    C_MUX_SECONDARY: cover(!local_input && secondary && select_input && observed);
`ifdef FND06_OVERCONSTRAIN
    // H-CONTROL-SELECT0
    H_CONTROL_SELECT0: assume(select_input==0);
`endif
  end
endmodule
module switch_LEFT;
  (* anyconst *) reg local_input, secondary, select_input;
  wire observed;
  NF_LEFT_switch_matrix dut(.P_X0(local_input),.P_X1(1'b0),.P_X2(1'b0),.P_X3(1'b0),
    .P_XA(secondary),.P_XE(1'b0),.P_XR(1'b0),.L_O(1'b0),.L_Co(1'b0),
    .L_I0(observed),.ConfigBits(select_input),.ConfigBits_N(~select_input));
  always @* begin
    // A-MUX-ORDER/NF_LEFT
    A_MUX_ORDER: assert(observed == (select_input ? secondary : local_input));
    // C-MUX-LOCAL/NF_LEFT
    C_MUX_LOCAL: cover(!local_input && secondary && !select_input && !observed);
    // C-MUX-SECONDARY/NF_LEFT
    C_MUX_SECONDARY: cover(!local_input && secondary && select_input && observed);
  end
endmodule
module switch_MID;
  (* anyconst *) reg local_input, secondary, select_input;
  wire observed;
  NF_MID_switch_matrix dut(.P_X0(local_input),.P_X1(1'b0),.P_X2(1'b0),.P_X3(1'b0),
    .P_XA(1'b0),.P_XE(1'b0),.P_XR(1'b0),.L_O(1'b0),.L_Co(1'b0),
    .W0(secondary),.L_I0(observed),.ConfigBits(select_input),.ConfigBits_N(~select_input));
  always @* begin
    // A-MUX-ORDER/NF_MID
    A_MUX_ORDER: assert(observed == (select_input ? secondary : local_input));
    // C-MUX-LOCAL/NF_MID
    C_MUX_LOCAL: cover(!local_input && secondary && !select_input && !observed);
    // C-MUX-SECONDARY/NF_MID
    C_MUX_SECONDARY: cover(!local_input && secondary && select_input && observed);
  end
endmodule
module switch_RIGHT;
  (* anyconst *) reg local_input, secondary, select_input;
  wire observed;
  NF_RIGHT_switch_matrix dut(.P_X0(local_input),.P_X1(1'b0),.P_X2(1'b0),.P_X3(1'b0),
    .P_XA(1'b0),.P_XE(1'b0),.P_XR(1'b0),.L_O(1'b0),.L_Co(1'b0),
    .W0(secondary),.L_I0(observed),.ConfigBits(select_input),.ConfigBits_N(~select_input));
  always @* begin
    // A-MUX-ORDER/NF_RIGHT
    A_MUX_ORDER: assert(observed == (select_input ? secondary : local_input));
    // C-MUX-LOCAL/NF_RIGHT
    C_MUX_LOCAL: cover(!local_input && secondary && !select_input && !observed);
    // C-MUX-SECONDARY/NF_RIGHT
    C_MUX_SECONDARY: cover(!local_input && secondary && select_input && observed);
  end
endmodule
