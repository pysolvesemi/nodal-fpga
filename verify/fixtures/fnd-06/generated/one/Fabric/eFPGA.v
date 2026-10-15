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
        input  [(FrameBitsPerRow*1)-1:0] FrameData, //CONFIG_PORT
        input  [(MaxFramesPerCol*1)-1:0] FrameStrobe, //CONFIG_PORT
        input  UserCLK
);

 //signal declarations

wire Tile_X0Y0_UserCLKo;
 //configuration signal declarations

wire[FrameBitsPerRow -1:0] Row_Y0_FrameData;
wire[MaxFramesPerCol - 1:0] Column_X0_FrameStrobe;
wire[FrameBitsPerRow - 1:0] Tile_X0Y0_FrameData_O;
wire[MaxFramesPerCol - 1:0] Tile_X0Y0_FrameStrobe_O;
wire[MaxFramesPerCol - 1:0] Tile_X0Y1_FrameStrobe_O;
 //tile-to-tile signal declarations

assign Row_Y0_FrameData = FrameData[FrameBitsPerRow*(0+1)-1:FrameBitsPerRow*0];
assign Column_X0_FrameStrobe = FrameStrobe[MaxFramesPerCol*(0+1)-1:MaxFramesPerCol*0];

 //tile IO port will get directly connected to top-level tile module
NF_SINGLE Tile_X0Y0_NF_SINGLE (
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
    .FrameStrobe(Column_X0_FrameStrobe),
    .FrameStrobe_O(Tile_X0Y0_FrameStrobe_O)
);

endmodule