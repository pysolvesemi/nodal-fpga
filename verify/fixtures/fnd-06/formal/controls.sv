module false_control;
  // A-CONTROL-FALSE: required normal step-0 solver counterexample.
  always @* begin A_CONTROL_FALSE: assert(1'b0); end
endmodule
module zero_control;
  // X-CONTROL-ZERO-EXPORT: deliberately has no assertion; export guard must fail.
  wire omitted = 1'b1;
endmodule
// H-CONTROL-SELECT0 is enabled ONLY in the switch_SINGLE derivative by
// -D FND06_OVERCONSTRAIN. Both original covers remain in switch.sv.
