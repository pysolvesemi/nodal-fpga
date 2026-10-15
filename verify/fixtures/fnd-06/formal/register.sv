// 13 sampled pre-edge states, 12 transitions. No initial DUT/shadow q constraint.
module register_formal(input clock);
  (* anyconst *) reg [15:0] init;
  (* anyconst *) reg reset_value, ff;
  (* anyseq *) reg [3:0] inputs;
  (* anyseq *) reg en, sr;
  reg initialized = 0;
  reg q_shadow;
  reg previous_initialized, previous_en, previous_sr, previous_q, previous_d, previous_o;
  wire observed;
  wire d = (init >> (inputs[0]+2*inputs[1]+4*inputs[2]+8*inputs[3])) & 1;
  LUT4c_frame_config_dffesr dut(.I(inputs),.O(observed),.Ci(1'b0),.Co(),
    .SR(sr),.EN(en),.UserCLK(clock),.ConfigBits({reset_value,1'b0,ff,init}));
  always @(posedge clock) begin
    initialized <= 1;
    if(en) q_shadow <= sr ? reset_value : d;
    previous_initialized <= initialized;
    previous_en <= en; previous_sr <= sr;
    previous_q <= q_shadow; previous_d <= d; previous_o <= observed;
  end
  // Observe current pre-edge state without an extra clocked property register.
  always @* begin
    // H-REG-INIT-ONLY
    H_REG_INIT_ONLY: assume(initialized || (en && sr));
    // A-REG-FF
    A_REG_FF: assert(!initialized || !ff || observed==q_shadow);
    // A-REG-COMB
    A_REG_COMB: assert(ff || observed==d);
    // C-REG-Q0
    C_REG_Q0: cover(initialized && ff && q_shadow==0 && observed==0);
    // C-REG-Q1
    C_REG_Q1: cover(initialized && ff && q_shadow==1 && observed==1);
    // C-REG-FF0
    C_REG_FF0: cover(initialized && !ff && d==1 && observed==d);
    // C-REG-FF1
    C_REG_FF1: cover(initialized && ff && q_shadow==1 && observed==q_shadow);
    // C-REG-R0
    C_REG_R0: cover(initialized && ff && !reset_value && previous_en && previous_sr && observed==0 && q_shadow==0);
    // C-REG-R1
    C_REG_R1: cover(initialized && ff && reset_value && previous_en && previous_sr && observed==1 && q_shadow==1);
    // C-REG-CAPTURE
    C_REG_CAPTURE: cover(initialized && previous_initialized && ff && previous_en && !previous_sr && q_shadow!=previous_q && observed==q_shadow && observed==previous_d);
    // C-REG-HOLD-SR
    C_REG_HOLD_SR: cover(initialized && previous_initialized && ff && !previous_en && previous_sr && previous_q!=reset_value && observed==q_shadow && q_shadow==previous_q && observed==previous_o);
    // C-REG-RESET
    C_REG_RESET: cover(initialized && previous_initialized && ff && previous_en && previous_sr && previous_q!=reset_value && observed==q_shadow && q_shadow==reset_value);
  end
endmodule
