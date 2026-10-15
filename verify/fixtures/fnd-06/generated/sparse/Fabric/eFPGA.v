module eFPGA
    #(
        parameter MaxFramesPerCol=20,
        parameter FrameBitsPerRow=32
    )
    (
        input  Tile_X0Y0_P_A0, //EXTERNAL
        input  Tile_X0Y0_P_A1, //EXTERNAL
        input  Tile_X0Y0_P_A2, //EXTERNAL
        input  Tile_X0Y0_P_A3, //EXTERNAL
        input  Tile_X0Y0_P_ALT, //EXTERNAL
        input  Tile_X0Y0_P_ENABLE, //EXTERNAL
        input  Tile_X0Y0_P_RESET, //EXTERNAL
        output  Tile_X0Y0_P_Y, //EXTERNAL
        input  Tile_X1Y0_P_A0, //EXTERNAL
        input  Tile_X1Y0_P_A1, //EXTERNAL
        input  Tile_X1Y0_P_A2, //EXTERNAL
        input  Tile_X1Y0_P_A3, //EXTERNAL
        input  Tile_X1Y0_P_ALT, //EXTERNAL
        input  Tile_X1Y0_P_ENABLE, //EXTERNAL
        input  Tile_X1Y0_P_RESET, //EXTERNAL
        output  Tile_X1Y0_P_Y, //EXTERNAL
        input  Tile_X1Y1_P_A0, //EXTERNAL
        input  Tile_X1Y1_P_A1, //EXTERNAL
        input  Tile_X1Y1_P_A2, //EXTERNAL
        input  Tile_X1Y1_P_A3, //EXTERNAL
        input  Tile_X1Y1_P_ALT, //EXTERNAL
        input  Tile_X1Y1_P_ENABLE, //EXTERNAL
        input  Tile_X1Y1_P_RESET, //EXTERNAL
        output  Tile_X1Y1_P_Y, //EXTERNAL
        input  Tile_X2Y1_P_A0, //EXTERNAL
        input  Tile_X2Y1_P_A1, //EXTERNAL
        input  Tile_X2Y1_P_A2, //EXTERNAL
        input  Tile_X2Y1_P_A3, //EXTERNAL
        input  Tile_X2Y1_P_ALT, //EXTERNAL
        input  Tile_X2Y1_P_ENABLE, //EXTERNAL
        input  Tile_X2Y1_P_RESET, //EXTERNAL
        output  Tile_X2Y1_P_Y, //EXTERNAL
        input  Tile_X0Y2_P_A0, //EXTERNAL
        input  Tile_X0Y2_P_A1, //EXTERNAL
        input  Tile_X0Y2_P_A2, //EXTERNAL
        input  Tile_X0Y2_P_A3, //EXTERNAL
        input  Tile_X0Y2_P_ALT, //EXTERNAL
        input  Tile_X0Y2_P_ENABLE, //EXTERNAL
        input  Tile_X0Y2_P_RESET, //EXTERNAL
        output  Tile_X0Y2_P_Y, //EXTERNAL
        input  Tile_X2Y2_P_A0, //EXTERNAL
        input  Tile_X2Y2_P_A1, //EXTERNAL
        input  Tile_X2Y2_P_A2, //EXTERNAL
        input  Tile_X2Y2_P_A3, //EXTERNAL
        input  Tile_X2Y2_P_ALT, //EXTERNAL
        input  Tile_X2Y2_P_ENABLE, //EXTERNAL
        input  Tile_X2Y2_P_RESET, //EXTERNAL
        output  Tile_X2Y2_P_Y, //EXTERNAL
        input  [(FrameBitsPerRow*3)-1:0] FrameData, //CONFIG_PORT
        input  [(MaxFramesPerCol*3)-1:0] FrameStrobe, //CONFIG_PORT
        input  UserCLK
);

 //signal declarations

wire Tile_X0Y0_UserCLKo;
wire Tile_X1Y0_UserCLKo;
wire Tile_X2Y0_UserCLKo;
wire Tile_X0Y1_UserCLKo;
wire Tile_X1Y1_UserCLKo;
wire Tile_X2Y1_UserCLKo;
wire Tile_X0Y2_UserCLKo;
wire Tile_X1Y2_UserCLKo;
wire Tile_X2Y2_UserCLKo;
 //configuration signal declarations

wire[FrameBitsPerRow -1:0] Row_Y0_FrameData;
wire[FrameBitsPerRow -1:0] Row_Y1_FrameData;
wire[FrameBitsPerRow -1:0] Row_Y2_FrameData;
wire[MaxFramesPerCol - 1:0] Column_X0_FrameStrobe;
wire[MaxFramesPerCol - 1:0] Column_X1_FrameStrobe;
wire[MaxFramesPerCol - 1:0] Column_X2_FrameStrobe;
wire[FrameBitsPerRow - 1:0] Tile_X0Y0_FrameData_O;
wire[FrameBitsPerRow - 1:0] Tile_X1Y0_FrameData_O;
wire[FrameBitsPerRow - 1:0] Tile_X2Y0_FrameData_O;
wire[FrameBitsPerRow - 1:0] Tile_X0Y1_FrameData_O;
wire[FrameBitsPerRow - 1:0] Tile_X1Y1_FrameData_O;
wire[FrameBitsPerRow - 1:0] Tile_X2Y1_FrameData_O;
wire[FrameBitsPerRow - 1:0] Tile_X0Y2_FrameData_O;
wire[FrameBitsPerRow - 1:0] Tile_X1Y2_FrameData_O;
wire[FrameBitsPerRow - 1:0] Tile_X2Y2_FrameData_O;
wire[MaxFramesPerCol - 1:0] Tile_X0Y0_FrameStrobe_O;
wire[MaxFramesPerCol - 1:0] Tile_X1Y0_FrameStrobe_O;
wire[MaxFramesPerCol - 1:0] Tile_X2Y0_FrameStrobe_O;
wire[MaxFramesPerCol - 1:0] Tile_X0Y1_FrameStrobe_O;
wire[MaxFramesPerCol - 1:0] Tile_X1Y1_FrameStrobe_O;
wire[MaxFramesPerCol - 1:0] Tile_X2Y1_FrameStrobe_O;
wire[MaxFramesPerCol - 1:0] Tile_X0Y2_FrameStrobe_O;
wire[MaxFramesPerCol - 1:0] Tile_X1Y2_FrameStrobe_O;
wire[MaxFramesPerCol - 1:0] Tile_X2Y2_FrameStrobe_O;
wire[MaxFramesPerCol - 1:0] Tile_X0Y3_FrameStrobe_O;
wire[MaxFramesPerCol - 1:0] Tile_X1Y3_FrameStrobe_O;
wire[MaxFramesPerCol - 1:0] Tile_X2Y3_FrameStrobe_O;
 //tile-to-tile signal declarations
wire[0:0] Tile_X0Y0_E;
wire[0:0] Tile_X1Y1_E;

assign Row_Y0_FrameData = FrameData[FrameBitsPerRow*(0+1)-1:FrameBitsPerRow*0];
assign Row_Y1_FrameData = FrameData[FrameBitsPerRow*(1+1)-1:FrameBitsPerRow*1];
assign Row_Y2_FrameData = FrameData[FrameBitsPerRow*(2+1)-1:FrameBitsPerRow*2];
assign Column_X0_FrameStrobe = FrameStrobe[MaxFramesPerCol*(0+1)-1:MaxFramesPerCol*0];
assign Column_X1_FrameStrobe = FrameStrobe[MaxFramesPerCol*(1+1)-1:MaxFramesPerCol*1];
assign Column_X2_FrameStrobe = FrameStrobe[MaxFramesPerCol*(2+1)-1:MaxFramesPerCol*2];

 //tile IO port will get directly connected to top-level tile module
NF_LEFT Tile_X0Y0_NF_LEFT (
    .E(Tile_X0Y0_E),
    .P_A0(Tile_X0Y0_P_A0),
    .P_A1(Tile_X0Y0_P_A1),
    .P_A2(Tile_X0Y0_P_A2),
    .P_A3(Tile_X0Y0_P_A3),
    .P_ALT(Tile_X0Y0_P_ALT),
    .P_ENABLE(Tile_X0Y0_P_ENABLE),
    .P_RESET(Tile_X0Y0_P_RESET),
    .P_Y(Tile_X0Y0_P_Y),
    .UserCLK(UserCLK),
    .UserCLKo(Tile_X0Y0_UserCLKo),
    .FrameData(Row_Y0_FrameData),
    .FrameData_O(Tile_X0Y0_FrameData_O),
    .FrameStrobe(Tile_X0Y2_FrameStrobe_O),
    .FrameStrobe_O(Tile_X0Y0_FrameStrobe_O)
);


 //tile IO port will get directly connected to top-level tile module
NF_RIGHT Tile_X1Y0_NF_RIGHT (
    .W(Tile_X0Y0_E),
    .P_A0(Tile_X1Y0_P_A0),
    .P_A1(Tile_X1Y0_P_A1),
    .P_A2(Tile_X1Y0_P_A2),
    .P_A3(Tile_X1Y0_P_A3),
    .P_ALT(Tile_X1Y0_P_ALT),
    .P_ENABLE(Tile_X1Y0_P_ENABLE),
    .P_RESET(Tile_X1Y0_P_RESET),
    .P_Y(Tile_X1Y0_P_Y),
    .UserCLK(Tile_X1Y1_UserCLKo),
    .UserCLKo(Tile_X1Y0_UserCLKo),
    .FrameData(Tile_X0Y0_FrameData_O),
    .FrameData_O(Tile_X1Y0_FrameData_O),
    .FrameStrobe(Tile_X1Y1_FrameStrobe_O),
    .FrameStrobe_O(Tile_X1Y0_FrameStrobe_O)
);


 //tile IO port will get directly connected to top-level tile module
NF_LEFT
`ifdef EMULATION
    #(
    .Emulate_Bitstream(`Tile_X1Y1_Emulate_Bitstream)
    )
`endif
    Tile_X1Y1_NF_LEFT
    (
    .E(Tile_X1Y1_E),
    .P_A0(Tile_X1Y1_P_A0),
    .P_A1(Tile_X1Y1_P_A1),
    .P_A2(Tile_X1Y1_P_A2),
    .P_A3(Tile_X1Y1_P_A3),
    .P_ALT(Tile_X1Y1_P_ALT),
    .P_ENABLE(Tile_X1Y1_P_ENABLE),
    .P_RESET(Tile_X1Y1_P_RESET),
    .P_Y(Tile_X1Y1_P_Y),
    .UserCLK(UserCLK),
    .UserCLKo(Tile_X1Y1_UserCLKo),
    .FrameData(Row_Y1_FrameData),
    .FrameData_O(Tile_X1Y1_FrameData_O),
    .FrameStrobe(Column_X1_FrameStrobe),
    .FrameStrobe_O(Tile_X1Y1_FrameStrobe_O)
);


 //tile IO port will get directly connected to top-level tile module
NF_RIGHT
`ifdef EMULATION
    #(
    .Emulate_Bitstream(`Tile_X2Y1_Emulate_Bitstream)
    )
`endif
    Tile_X2Y1_NF_RIGHT
    (
    .W(Tile_X1Y1_E),
    .P_A0(Tile_X2Y1_P_A0),
    .P_A1(Tile_X2Y1_P_A1),
    .P_A2(Tile_X2Y1_P_A2),
    .P_A3(Tile_X2Y1_P_A3),
    .P_ALT(Tile_X2Y1_P_ALT),
    .P_ENABLE(Tile_X2Y1_P_ENABLE),
    .P_RESET(Tile_X2Y1_P_RESET),
    .P_Y(Tile_X2Y1_P_Y),
    .UserCLK(Tile_X2Y2_UserCLKo),
    .UserCLKo(Tile_X2Y1_UserCLKo),
    .FrameData(Tile_X1Y1_FrameData_O),
    .FrameData_O(Tile_X2Y1_FrameData_O),
    .FrameStrobe(Tile_X2Y2_FrameStrobe_O),
    .FrameStrobe_O(Tile_X2Y1_FrameStrobe_O)
);


 //tile IO port will get directly connected to top-level tile module
NF_SINGLE Tile_X0Y2_NF_SINGLE (
    .P_A0(Tile_X0Y2_P_A0),
    .P_A1(Tile_X0Y2_P_A1),
    .P_A2(Tile_X0Y2_P_A2),
    .P_A3(Tile_X0Y2_P_A3),
    .P_ALT(Tile_X0Y2_P_ALT),
    .P_ENABLE(Tile_X0Y2_P_ENABLE),
    .P_RESET(Tile_X0Y2_P_RESET),
    .P_Y(Tile_X0Y2_P_Y),
    .UserCLK(UserCLK),
    .UserCLKo(Tile_X0Y2_UserCLKo),
    .FrameData(Row_Y2_FrameData),
    .FrameData_O(Tile_X0Y2_FrameData_O),
    .FrameStrobe(Column_X0_FrameStrobe),
    .FrameStrobe_O(Tile_X0Y2_FrameStrobe_O)
);


 //tile IO port will get directly connected to top-level tile module
NF_SINGLE Tile_X2Y2_NF_SINGLE (
    .P_A0(Tile_X2Y2_P_A0),
    .P_A1(Tile_X2Y2_P_A1),
    .P_A2(Tile_X2Y2_P_A2),
    .P_A3(Tile_X2Y2_P_A3),
    .P_ALT(Tile_X2Y2_P_ALT),
    .P_ENABLE(Tile_X2Y2_P_ENABLE),
    .P_RESET(Tile_X2Y2_P_RESET),
    .P_Y(Tile_X2Y2_P_Y),
    .UserCLK(UserCLK),
    .UserCLKo(Tile_X2Y2_UserCLKo),
    .FrameData(Tile_X0Y2_FrameData_O),
    .FrameData_O(Tile_X2Y2_FrameData_O),
    .FrameStrobe(Column_X2_FrameStrobe),
    .FrameStrobe_O(Tile_X2Y2_FrameStrobe_O)
);

endmodule