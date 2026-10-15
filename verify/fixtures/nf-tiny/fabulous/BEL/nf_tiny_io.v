// Independently authored, transparent reference-input wiring; not generated RTL.
// No lookup table, state, configuration storage, or expected-result model lives here.
`default_nettype none
module nf_tiny_io (
    (* FABulous, EXTERNAL *) input A0,
    (* FABulous, EXTERNAL *) input A1,
    (* FABulous, EXTERNAL *) input A2,
    (* FABulous, EXTERNAL *) input A3,
    (* FABulous, EXTERNAL *) input ALT,
    (* FABulous, EXTERNAL *) input ENABLE,
    (* FABulous, EXTERNAL *) input RESET,
    (* FABulous, EXTERNAL *) output Y,
    output X0, X1, X2, X3, XA, XE, XR,
    input RESULT
);
    assign X0 = A0;
    assign X1 = A1;
    assign X2 = A2;
    assign X3 = A3;
    assign XA = ALT;
    assign XE = ENABLE;
    assign XR = RESET;
    assign Y = RESULT;
endmodule
`default_nettype wire
