/// scr_nes_palette_init()
// Exact 64-entry NTSC NES palette from oracle/palette/nestopia.pal
// (Nestopia 2.0.0 f1e02d1). Do not use FCEUX/2C02G approximations.

var i;
global.nes_pal[ 0] = make_colour_rgb(102, 102, 102); // $00
global.nes_pal[ 1] = make_colour_rgb(  0,  42, 136); // $01
global.nes_pal[ 2] = make_colour_rgb( 20,  18, 167); // $02
global.nes_pal[ 3] = make_colour_rgb( 59,   0, 164); // $03
global.nes_pal[ 4] = make_colour_rgb( 92,   0, 126); // $04
global.nes_pal[ 5] = make_colour_rgb(110,   0,  64); // $05
global.nes_pal[ 6] = make_colour_rgb(108,   7,   0); // $06
global.nes_pal[ 7] = make_colour_rgb( 86,  29,   0); // $07
global.nes_pal[ 8] = make_colour_rgb( 51,  53,   0); // $08
global.nes_pal[ 9] = make_colour_rgb( 12,  72,   0); // $09
global.nes_pal[10] = make_colour_rgb(  0,  82,   0); // $0A
global.nes_pal[11] = make_colour_rgb(  0,  79,   8); // $0B
global.nes_pal[12] = make_colour_rgb(  0,  64,  77); // $0C
global.nes_pal[13] = make_colour_rgb(  0,   0,   0); // $0D
global.nes_pal[14] = make_colour_rgb(  0,   0,   0); // $0E
global.nes_pal[15] = make_colour_rgb(  0,   0,   0); // $0F
global.nes_pal[16] = make_colour_rgb(173, 173, 173); // $10
global.nes_pal[17] = make_colour_rgb( 21,  95, 217); // $11
global.nes_pal[18] = make_colour_rgb( 66,  64, 255); // $12
global.nes_pal[19] = make_colour_rgb(117,  39, 254); // $13
global.nes_pal[20] = make_colour_rgb(160,  26, 204); // $14
global.nes_pal[21] = make_colour_rgb(183,  30, 123); // $15
global.nes_pal[22] = make_colour_rgb(181,  49,  32); // $16
global.nes_pal[23] = make_colour_rgb(153,  78,   0); // $17
global.nes_pal[24] = make_colour_rgb(107, 109,   0); // $18
global.nes_pal[25] = make_colour_rgb( 56, 135,   0); // $19
global.nes_pal[26] = make_colour_rgb( 13, 147,   0); // $1A
global.nes_pal[27] = make_colour_rgb(  0, 143,  50); // $1B
global.nes_pal[28] = make_colour_rgb(  0, 124, 141); // $1C
global.nes_pal[29] = make_colour_rgb(  0,   0,   0); // $1D
global.nes_pal[30] = make_colour_rgb(  0,   0,   0); // $1E
global.nes_pal[31] = make_colour_rgb(  0,   0,   0); // $1F
global.nes_pal[32] = make_colour_rgb(255, 255, 255); // $20
global.nes_pal[33] = make_colour_rgb(100, 176, 255); // $21
global.nes_pal[34] = make_colour_rgb(146, 144, 255); // $22
global.nes_pal[35] = make_colour_rgb(198, 118, 255); // $23
global.nes_pal[36] = make_colour_rgb(242, 106, 255); // $24
global.nes_pal[37] = make_colour_rgb(255, 110, 204); // $25
global.nes_pal[38] = make_colour_rgb(255, 129, 112); // $26
global.nes_pal[39] = make_colour_rgb(234, 158,  34); // $27
global.nes_pal[40] = make_colour_rgb(188, 190,   0); // $28
global.nes_pal[41] = make_colour_rgb(136, 216,   0); // $29
global.nes_pal[42] = make_colour_rgb( 92, 228,  48); // $2A
global.nes_pal[43] = make_colour_rgb( 69, 224, 130); // $2B
global.nes_pal[44] = make_colour_rgb( 72, 205, 222); // $2C
global.nes_pal[45] = make_colour_rgb( 79,  79,  79); // $2D
global.nes_pal[46] = make_colour_rgb(  0,   0,   0); // $2E
global.nes_pal[47] = make_colour_rgb(  0,   0,   0); // $2F
global.nes_pal[48] = make_colour_rgb(255, 255, 255); // $30
global.nes_pal[49] = make_colour_rgb(192, 223, 255); // $31
global.nes_pal[50] = make_colour_rgb(211, 210, 255); // $32
global.nes_pal[51] = make_colour_rgb(232, 200, 255); // $33
global.nes_pal[52] = make_colour_rgb(250, 194, 255); // $34
global.nes_pal[53] = make_colour_rgb(255, 196, 234); // $35
global.nes_pal[54] = make_colour_rgb(255, 204, 197); // $36
global.nes_pal[55] = make_colour_rgb(247, 216, 165); // $37
global.nes_pal[56] = make_colour_rgb(228, 229, 148); // $38
global.nes_pal[57] = make_colour_rgb(207, 239, 150); // $39
global.nes_pal[58] = make_colour_rgb(189, 244, 171); // $3A
global.nes_pal[59] = make_colour_rgb(179, 243, 204); // $3B
global.nes_pal[60] = make_colour_rgb(181, 235, 242); // $3C
global.nes_pal[61] = make_colour_rgb(184, 184, 184); // $3D
global.nes_pal[62] = make_colour_rgb(  0,   0,   0); // $3E
global.nes_pal[63] = make_colour_rgb(  0,   0,   0); // $3F

// Active PPU palette RAM ($3F00-$3F1F) initialized to Title defaults
for (i = 0; i < 32; i += 1) {
    global.ppu_pal[i] = $0F;
}
