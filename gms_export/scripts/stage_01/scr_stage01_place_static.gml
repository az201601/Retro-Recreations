/// scr_stage01_place_static()  |  generated from original USA NES ROM
/// Attach to obj_stage01_controller Create event in rm_stage_01_restaurant.
/// Room size: 2048x2048. View: 256x240; initial view x=0, y=512.
/// Import each bg_restaurant_* and ts_restaurant_* PNG as a GMS Background.
/// Tile dimensions: 16x16, NO interpolation. BG 10000; tiles 1000.
/// Collision grid value 1 = NES one-way from above; 2 = solid.
/// Later: call ds_grid_destroy(global.stage01_collision_grid) on Room End.
var grid_rows, row_text, row_y, cell_x, tile_id, xx, yy;
global.stage01_collision_grid = ds_grid_create(128, 128);
ds_grid_clear(global.stage01_collision_grid, 0);

// seating | NES world 0,512 | 2048x256 source pixels
tile_add(bg_restaurant_seating, 0, 0, 2048, 256, 0, 512, 10000);
grid_rows[0] = "ffffffffffffffffff202a2b2727272727272a2b272727272727272727202727" + "2727272727272720ffffffffffffffffffffffffffffffffff202a2b27272727" + "27272a2b2727272727272727272027272727272727272720ffffffffffffffff" + "ffffffffffffffffff202a2b2727272727272a2b272727272727272727202727";
grid_rows[1] = "ffffffffffffffffff20272a2b2727272727272a2b2727272727272727202b27" + "2727272727272720ffffffffffffffffffffffffffffffffff20272a2b272727" + "2727272a2b2727272727272727202b272727272727272720ffffffffffffffff" + "ffffffffffffffffff20272a2b2727272727272a2b2727272727272727202b27";
grid_rows[2] = "ffffffffffffffffff2026262c2d2626262626262c2d26262626262626202c2d" + "2626262626262620ffffffffffffffffffffffffffffffffff2026262c2d2626" + "262626262c2d26262626262626202c2d2626262626262620ffffffffffffffff" + "ffffffffffffffffff2026262c2d2626262626262c2d26262626262626202c2d";
grid_rows[3] = "ffffffffffffffffff2016161628291616162e16162829161616162e16201628" + "2916162f16161620ffffffffffffffffffffffffffffffffff20161616282916" + "16162e16162829161616162e162016282916162f16161620ffffffffffffffff" + "ffffffffffffffffff2016161628291616162e16162829161616162e16201628";
grid_rows[4] = "ffffffffffffffffff20162e16162829162f1616161628291616161616201616" + "2829161616161620ffffffffffffffffffffffffffffffffff20162e16162829" + "162f16161616282916161616162016162829161616161620ffffffffffffffff" + "ffffffffffffffffff20162e16162829162f1616161628291616161616201616";
grid_rows[5] = "ffffffffffffffffa7acacacacacacacacacacacacacacacacacacacacacacac" + "acacacacacacacacab21ffffffffffffffffffffffffffffa7acacacacacacac" + "acacacacacacacacacacacacacacacacacacacacacacacacab21ffffffffffff" + "ffffffffffffffffa7acacacacacacacacacacacacacacacacacacacacacacac";
grid_rows[6] = "ffffffffffffffff2319181918191819181918191819181918191819181d1819" + "18191819181918191822ffffffffffffffffffffffffffff2319181918191819" + "181918191819181918191819181d181918191819181918191822ffffffffffff" + "ffffffffffffffff2319181918191819181918191819181918191819181d1819";
grid_rows[7] = "ffffffffffffffffa8a9aaffffffffffffffffffffffffffffffffff1e1fffff" + "ffffa4a5a6ffffffffffffffffffffffffffffffffffffffa8a9aaffffffffff" + "ffffffffffffffffffffffff1e1fffffffffa4a5a6ffffffffffffffffffffff" + "ffffffffffffffffa8a9aaffffffffffffffffffffffffffffffffff1e1fffff";
grid_rows[8] = "ffffffffffadaeff070809ffa1a0ffffffffffffffffffffffffffff1c17ffad" + "aeff122425ffffadaeffffffffffffffffffffffffadaeff070809ffa1a0ffff" + "ffffffffffffffffffffffff1c17ffadaeff122425ffffadaeffffffffffffff" + "ffffffffffadaeff070809ffa1a0ffffffffffffffffffffffffffff1c17ffad";
grid_rows[9] = "ffffffff91908f920d0e0fff0506ffffffffffffffffffffffffffff1a1b9190" + "8f92131415ff91908f92ffffffffffffffffffff91908f920d0e0fff0506ffff" + "ffffffffffffffffffffffff1a1b91908f92131415ff91908f92ffffffffffff" + "ffffffff91908f920d0e0fff0506ffffffffffffffffffffffffffff1a1b9190";
grid_rows[10] = "a2ffffffd6d7d8d8d8d8d8d8d9dadbffffffffa3ffffa2ffffffffffd6d7d8d8" + "d8d8d8d8d8d8d9dadbffffffffa3ffffa2ffffffd6d7d8d8d8d8d8d8d9dadbff" + "ffffffa3ffffa2ffffffffffd6d7d8d8d8d8d8d8d8d8d9dadbffffffffa3ffff" + "a2ffffffd6d7d8d8d8d8d8d8d9dadbffffffffa3ffffa2ffffffffffd6d7d8d8";
grid_rows[11] = "03ffffffffffffffff10ffffffffffffffffff04ffff03ffffffffffffffffff" + "ffff10ffffffffffffffffffff04ffff03ffffffffffffffff10ffffffffffff" + "ffffff04ffff03ffffffffffffffffffffff10ffffffffffffffffffff04ffff" + "03ffffffffffffffff10ffffffffffffffffff04ffff03ffffffffffffffffff";
grid_rows[12] = "dcd1d3d4d5ffffffff11ffffffffffd0d1d3d4ddffffdcd1d3d4d5ffffffffff" + "ffff11ffffffffffffd0d1d3d4ddffffdcd1d3d4d5ffffffff11ffffffffffd0" + "d1d3d4ddffffdcd1d3d4d5ffffffffffffff11ffffffffffffd0d1d3d4ddffff" + "dcd1d3d4d5ffffffff11ffffffffffd0d1d3d4ddffffdcd1d3d4d5ffffffffff";
grid_rows[13] = "ffff10ffffffffffff11ffffffffffffff10ffffffffffff10ffffffffffffff" + "ffff11ffffffffffffffff10ffffffffffff10ffffffffffff11ffffffffffff" + "ff10ffffffffffff10ffffffffffffffffff11ffffffffffffffff10ffffffff" + "ffff10ffffffffffff11ffffffffffffff10ffffffffffff10ffffffffffffff";
grid_rows[14] = "ffff11ffffffffffff11ffffffffffffff11ffffffffffff11ffffffffffffff" + "ffff11ffffffffffffffff11ffffffffffff11ffffffffffff11ffffffffffff" + "ff11ffffffffffff11ffffffffffffffffff11ffffffffffffffff11ffffffff" + "ffff11ffffffffffff11ffffffffffffff11ffffffffffff11ffffffffffffff";
grid_rows[15] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
for (row_y = 0; row_y < 16; row_y += 1) {
    row_text = grid_rows[row_y];
    for (cell_x = 0; cell_x < 128; cell_x += 1) {
        tile_id = scr_stage01_hex_byte(row_text, cell_x);
        if (tile_id != 255) {
            xx = 0 + cell_x * 16;
            yy = 512 + row_y * 16;
            tile_add(ts_restaurant_seating, (tile_id mod 16) * 16,
                     floor(tile_id / 16) * 16, 16, 16, xx, yy, 1000);
            if (tile_id >= 208 && tile_id != 249) {
                ds_grid_set(global.stage01_collision_grid, xx div 16, yy div 16, 2);
            } else if (tile_id >= 160 && tile_id != 249) {
                ds_grid_set(global.stage01_collision_grid, xx div 16, yy div 16, 1);
            }
        }
    }
}

// kitchen | NES world 0,1536 | 2048x512 source pixels
tile_add(bg_restaurant_kitchen, 0, 0, 2048, 512, 0, 1536, 10000);
grid_rows[0] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffff57ffffffffffffffffffffffffffff57" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
grid_rows[1] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffff57ffffffffffffffffffffffffffff57" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
grid_rows[2] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffff57ffffffc2c3c3c3c4ffffffffffff57" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc2c3";
grid_rows[3] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffff57ffffff585959595affffffffffff57" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff5859";
grid_rows[4] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffb3b3b3b3b3b3b3b3c7c6c5c6c5c6c5b5" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffb4b3b3b3b3b3";
grid_rows[5] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffff57ffffff55ffff556c5f5e5f5e5f5e55" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff55ff";
grid_rows[6] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffff57ffffffffffffff6d6d6d6d6d6d6d57" + "ffffffafffffffffffffffafffffffffffffffafffffffffffffffffffffffff";
grid_rows[7] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffff57ffffffffffffffffffffffffffff57" + "ffffff65ffffffffffffff65ffffffffffffff65ffffffffffffffffffffffff";
grid_rows[8] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffc2c3c3c3c3c4ffffffff53ffffffff57" + "ffff606162ffffffffff606162ffffffffff606162ffffffffffffffffffffff";
grid_rows[9] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffff58595959595affffffff54ffffffff57" + "ffff630102ffffffffff630102ffffffffff630102ffffffffffffffffff6667";
grid_rows[10] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffb3b3b3b3b3b5ffffffffffffffffff57" + "ffff68696affffffffff68696affffffffff68696affffffffffffffffff6b9f";
grid_rows[11] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffff57ffffff55ffffffffffffffffffff57" + "3f3f7071723f3f3f3f3f7071723f3f3f3f3f7071723f3f3f3f3f3f3f3f3f9f9f";
grid_rows[12] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffff57ffb7c0c1ffffffffffffffffffff57" + "e3e4e4e5e6e4e4e7e3e4e4e5e6e4e4e7e3e4e4e5e6e4e4e7e3e4e4e5e6e4e4e7";
grid_rows[13] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffff57ff4d4e4fffffffffffffffffffff57" + "e85151e9e85151e9e85151e9e85151e9e85151e9e85151e9e85151e9e85151e9";
grid_rows[14] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffc7c6c5c6b3b5ffffffffffffffffff57" + "e85151e9e85151e9e85151e9e85151e9e85151e9e85151e9e85151e9e85151e9";
grid_rows[15] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
grid_rows[16] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "57ffffffffffffffffffffffffffff57ffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffff6c5f5e5f55ffffffffffffffffffff57" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
grid_rows[17] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "57ffffffffffffffffffffffffffff57ffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffff576d6d6dffffffffffffffffffffff57" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
grid_rows[18] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "57ffffffffffffffffffffffffffff57ffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffff57ffffffffffb4b3c7c6c5c6c5c6c5b3" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
grid_rows[19] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "57ffffffffffffffffffffffffffff57ffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffff57ffffffffffff556c5f5e5f5e5f5e57" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
grid_rows[20] = "ffffc2c3c3c3c4ffffffb4b3b3b5ffffb7c0c1ffffffffffffffb7c0c1ffffff" + "57ffb7c0c1ffffffffffffffb4b3b3b5ffffc2c3c3c3c4ffffffb4b3b3b5ffff" + "b7c0c1ffffffffffffffb7c0c1ffffff5753ff53ffffffff6d6d6d6d6d6d6d57" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
grid_rows[21] = "ffff585959595affffffff55ffffffff4d4e4fffffffffffffff4d4e4fffffff" + "57ff4d4e4fffffffffffffffff55ff57ffff585959595affffffff55ffffffff" + "4d4e4fffffffffffffff4d4e4fffffff57ffff54ffffffffffffffffffffff57" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
grid_rows[22] = "b4b3b3b3b3b3b3b3b3b3b3b5ffffffffb4b3b3b3b3b5ffffb4b3b3b3b3b5ffff" + "b4b3b3b3b3b5ffffb4b3b3b3b3b5ff57b4b3b3b3b3b3b3b3b3b3b3b5ffffffff" + "b4b3b3b3b3b5ffffb4b3b3b3b3b5ffff57ffffffffffffffffffffffc2c3c3c3" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
grid_rows[23] = "ff55ffffffffffffffff55ffffffffffff55ffffffffffffff55ffff55ffffff" + "5755ffff55ffffffff55ffff55ffff57ff55ffffffffffffffff55ffffffffff" + "ff55ffffffffffffff55ffff55ffffff57ffffffffffffffffffffff58595959" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
grid_rows[24] = "ffffffffbbbcbdbebfffffffffffffffffffff4647ffffffffffbbbcbdbebfff" + "57ffc2c3c3c3c4ffffffffffffffff57ffffffffbbbcbdbebfffffffffffffff" + "ffffff4647ffffffffffbbbcbdbebfff57ffffffffffffff53ffb4b3b3b3b3b3" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
grid_rows[25] = "ffffffff404244ffffffffffb4b3b3b5ffffb6bab8b9ffffffff404244ffffff" + "57ff585959595affffffffffffffff57ffffffff404244ffffffffffb4b3b3b5" + "ffffb6bab8b9ffffffff404244ffffff57ffffffffffffff54ffff55ffffff57" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
grid_rows[26] = "ffffffff404244ffb7c0c1bbbcbdbebfffff40414243ffffffff404244ffffff" + "57ff585959595affffffc2c3c3c3c457ffffffff404244ffb7c0c1bbbcbdbebf" + "ffff40414243ffffffff404244ffffff57ffc2c3c3c3c4ffffffffffb7c0c1b7" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
grid_rows[27] = "3f3f3f3f484c4b3f4d4e4f484c4b3f3f3f3f48494a4b3f3f3f3f484c4b3f3f3f" + "57ff585959595affffff585959595a573f3f3f3f484c4b3f4d4e4f484c4b3f3f" + "3f3f48494a4b3f3f3f3f484c4b3f3f3f57ff585959595affffffffff4d4e4f4d" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
grid_rows[28] = "dedee2e2e1dee2e2e2e2dededee1dedee2e2e1dee1dedededee1e1dee2e2e2e2" + "e2e2e1dee1dedededee1dedededededededee2e2e1dee2e2e2e2dededee1dede" + "e2e2e1dee1dedededee1e1dee2e2e2e2e2e2e1dee1dedededee1e1dee2e2e2e2" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
grid_rows[29] = "3e3e3e3e453e3e3e3e3e3e3e3e453e3e3e3e453e453e3e3e3e45453e3e3e3e3e" + "3e3e453e453e3e3e3e453e3e3e3e3e3e3e3e3e3e453e3e3e3e3e3e3e3e453e3e" + "3e3e453e453e3e3e3e45453e3e3e3e3e3e3e453e453e3e3e3e45453e3e3e3e3e" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
grid_rows[30] = "e3e4e4e5e6e4e4e73737373737373737e3e4e4e5e6e4e4e73737373737373737" + "37373737373737373737373737373737e3e4e4e5e6e4e4e73737373737373737" + "e3e4e4e5e6e4e4e73737373737373737e3e4e4e5e6e4e4e73737373737373737" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
grid_rows[31] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
for (row_y = 0; row_y < 32; row_y += 1) {
    row_text = grid_rows[row_y];
    for (cell_x = 0; cell_x < 128; cell_x += 1) {
        tile_id = scr_stage01_hex_byte(row_text, cell_x);
        if (tile_id != 255) {
            xx = 0 + cell_x * 16;
            yy = 1536 + row_y * 16;
            tile_add(ts_restaurant_kitchen, (tile_id mod 16) * 16,
                     floor(tile_id / 16) * 16, 16, 16, xx, yy, 1000);
            if (tile_id >= 208 && tile_id != 249) {
                ds_grid_set(global.stage01_collision_grid, xx div 16, yy div 16, 2);
            } else if (tile_id >= 160 && tile_id != 249) {
                ds_grid_set(global.stage01_collision_grid, xx div 16, yy div 16, 1);
            }
        }
    }
}

// grill | NES world 0,1280 | 1792x256 source pixels
tile_add(bg_restaurant_grill, 0, 0, 1792, 256, 0, 1280, 10000);
grid_rows[0] = "ffffffffffffffffffffffffffffffff57ffffffffffffffffffffffffffff57" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "57ffffffffffffffffffffffffffff57ffffffffffffffffffff57ffffffffff" + "57ffffffffffffffffffffffff57ffff";
grid_rows[1] = "ffffffffffffffffffffffffffffffff57ffffffffffffffffffffffffffff57" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "57ffffffffffffffffffffffffffff57ffffffffffffffffffff57ffffffffff" + "57ffffffffffffffffffffffff57ffff";
grid_rows[2] = "c3c3c4ffffffffffffffffffffffffff57ffffffffffffffffffffffffffff57" + "ffffffffffffffffffffb7c0c1ffffffffffffffffffffffffffffffffffffff" + "57ffffffffffffffffffffffffffff57ffffffffffffffffffffb7c0c1ffffff" + "57cbcccccdffffffffffffffff57ffff";
grid_rows[3] = "59595affffffffffffffffffffffffff57ffffffffffffffffffffffffffff57" + "ffffffffffffffffffff4d4e4fffffffffffffffffffffffffffffffffffffff" + "57ffffffffffffffffffffffffffff57ffffffffffffffffffff4d4e4fffffff" + "578889ed8c8d8c8d8e8e8e8e8eedffff";
grid_rows[4] = "b4b3b3b3b3b5ffffffffffffb7c0c1ffb4b5ffffc8c9c9c9c9c9c9c9c9caff57" + "c2c3c3c3c4ffffffb4b3b3b3b3b5ffffb7c0c1ffffffffffffffb7c0c1ffffff" + "b4b5ffffc8c9c9c9c9c9c9c9c9caff57c2c3c3c3c4ffffffb4b3b3b3b5ffffb4" + "b3b3b5ee8b8a8b000000000000eeffff";
grid_rows[5] = "ff55ffff55ffffffffffffff4d4e4fff5755ffff73747583847583847576ff57" + "585959595affffffff55ffff55ffffff4d4e4fffffffffffffff4d4e4fffffff" + "5755ffff73747583847583847576ff57585959595affffffff5557ff55ffffff" + "5587ffee8a8b00000000000000eeffff";
grid_rows[6] = "ffffffffffffffffffffb4b3b3b3b3b557ffffff7a00858600858600007bff57" + "b4b3b3b3b3b3b3b3b3b5ffffffffffffb4b3b3b3b3b5ffffb4b3b3b3b3b5ffff" + "57ffffff7a00858600858600007bff57b4b3b3b3b3b3b3b3b3b557ffffffffff" + "5787ffee8b9f9f9f9f9f9f9f9feeffff";
grid_rows[7] = "ffffffffffffffffffffff55ffff55ff57ffffff777d7e7e7e7e7e7e7f7bff57" + "ffffffffffffffff55ffffffffffffffff55ffffffffffffff55ffff55ffffff" + "57ffffff777d7e7e7e7e7e7e7f7bff57ffffffffffffffff55ff57ffffffffff" + "5787ffee9f9f9f9f9f9f9f9f9fee6667";
grid_rows[8] = "ffffffffbbbcbdbebfffbbbcbdbebfffb4b5ffff7700000000000000007bff57" + "ffffffffffffffffffffffffffffffffffffff4647ffffffffffbbbcbdbebfff" + "b4b5ffff7700000000000000007bff57ffffffffffffffffffff57ffffffffff" + "b4b3b5ee9f9f9f9f9f9f9f9f9fee6b9f";
grid_rows[9] = "ffffffff404244ffffff404244ffffff5755ffff777d7e7e7e7e7e7e7f7bff57" + "ffffffffffffffffffffffffffffffffffffb6bab8b9ffffffff404244ffffff" + "5755ffff777d7e7e7e7e7e7e7f7bff57ffffffffffffffffffff57ffffffffff" + "5755ffee9f9f9f9f9f9f9f9f9fee6b9f";
grid_rows[10] = "ffffffff404244ffffff404244ffffff57ffffff79808080808080808078ff57" + "ffffb7c0c1b7c0c1ffffffffffffffffffff40414243ffffffff404244ffffff" + "57ffffff79808080808080808078ff57ffffffffb7c0c1b7c0c157ffffffffff" + "5787ffee9f9f9f9f9f9f9f9f9feee0de";
grid_rows[11] = "3f3f3f3f484c4b3f3f3f484c4b3f3f3f57ffffffffffffffffffffffffffff57" + "3f3f4d4e4f4d4e4f3f3f3f3f3f3f3f3f3f3f48494a4b3f3f3f3f484c4b3f3f3f" + "57ffffffffffffffffffffffffffff573f3f3f3f4d4e4f4d4e4f57ffffffffff" + "5787ffee9f9f9f9f9f9f9f9f9fee3d3e";
grid_rows[12] = "dedee2e2e1dee2e2e2e2dededee1dedededfffffeaebebebebebebebebecff57" + "e0dee1dee1dee2e2dee1dee2e2e2e2dee2e2e1dee1dedededee1e1dee2e2e2e2" + "dedfffffeaebebebebebebebebecff57e0dee1dee1dee2e2dedf57ffffffffff" + "5787ffee9f9f9f9f9f9f9f9f9fee3737";
grid_rows[13] = "3e3e3e3e453e3e3e3e3e3e3e3e453e3e3e3cffff73747575838475757576ff57" + "3d3e453e453e3e3e3e453e3e3e3e3e3e3e3e453e453e3e3e3e45453e3e3e3e3e" + "3e3cffff73747575838475757576ff573d3e453e453e3e3e3e3c57ffffffffff" + "5787ffeef0f0f0f0f0f0f0f0f0ee3737";
grid_rows[14] = "e3e4e4e5e6e4e4e737373737373737373737ffff7a00008586000000007bff57" + "37373737373737373737373737373737e3e4e4e5e6e4e4e73737373737373737" + "3737ffff7a00008586000000007bff573737373737373737373757ffffffffff" + "5787ffeef1f1f1f1f1f1f1f1f1ee3737";
grid_rows[15] = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" + "ffffffffffffffffffffffffffffffff";
for (row_y = 0; row_y < 16; row_y += 1) {
    row_text = grid_rows[row_y];
    for (cell_x = 0; cell_x < 112; cell_x += 1) {
        tile_id = scr_stage01_hex_byte(row_text, cell_x);
        if (tile_id != 255) {
            xx = 0 + cell_x * 16;
            yy = 1280 + row_y * 16;
            tile_add(ts_restaurant_grill, (tile_id mod 16) * 16,
                     floor(tile_id / 16) * 16, 16, 16, xx, yy, 1000);
            if (tile_id >= 208 && tile_id != 249) {
                ds_grid_set(global.stage01_collision_grid, xx div 16, yy div 16, 2);
            } else if (tile_id >= 160 && tile_id != 249) {
                ds_grid_set(global.stage01_collision_grid, xx div 16, yy div 16, 1);
            }
        }
    }
}

// monterey | NES world 0,1024 | 256x256 source pixels
tile_add(bg_restaurant_monterey, 0, 0, 256, 256, 0, 1024, 10000);
grid_rows[0] = "ffffffffffffffffffffffffffffffff";
grid_rows[1] = "ffffffffffffffffffffffffffffffff";
grid_rows[2] = "ffffffffffffffffffffffffffffffff";
grid_rows[3] = "ffffffffffffffffffffffffffffffff";
grid_rows[4] = "ffffffffffffffffffffffffffffffff";
grid_rows[5] = "ffffffffffffffffffffffffffffffff";
grid_rows[6] = "ffffffffffffffffffc0c4c3ffffffc0";
grid_rows[7] = "c378ffffffffffffff5fc460c5c6785f";
grid_rows[8] = "60ffffffffffffffff53c456ff71ff53";
grid_rows[9] = "56ffffffffc0c1c3c0c4c3c5c4c6c0c4";
grid_rows[10] = "c6ffffffff54c1555fc460ff9e838888";
grid_rows[11] = "71ffffffff53c15653c456ff9e848686";
grid_rows[12] = "c9c9c9c9c9c9c9c9c9c9c9c9c9c9c9c9";
grid_rows[13] = "cacacacacacacacacacacacacacacaca";
grid_rows[14] = "c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8c8";
grid_rows[15] = "ffffffffffffffffffffffffffffffff";
for (row_y = 0; row_y < 16; row_y += 1) {
    row_text = grid_rows[row_y];
    for (cell_x = 0; cell_x < 16; cell_x += 1) {
        tile_id = scr_stage01_hex_byte(row_text, cell_x);
        if (tile_id != 255) {
            xx = 0 + cell_x * 16;
            yy = 1024 + row_y * 16;
            tile_add(ts_restaurant_monterey, (tile_id mod 16) * 16,
                     floor(tile_id / 16) * 16, 16, 16, xx, yy, 1000);
            if (tile_id >= 208 && tile_id != 249) {
                ds_grid_set(global.stage01_collision_grid, xx div 16, yy div 16, 2);
            } else if (tile_id >= 160 && tile_id != 249) {
                ds_grid_set(global.stage01_collision_grid, xx div 16, yy div 16, 1);
            }
        }
    }
}

// water_rabbit | NES world 1024,256 | 256x256 source pixels
tile_add(bg_restaurant_water_rabbit, 0, 0, 256, 256, 1024, 256, 10000);
grid_rows[0] = "ffffffffffffffffffffffffffffffff";
grid_rows[1] = "ffffffffffffffffffffffffffffffff";
grid_rows[2] = "ffffffffffffffffffffffffffffffff";
grid_rows[3] = "ffffffffffffffffffffffffffffffff";
grid_rows[4] = "cecececeb2ffffb0b1b1cececeb2ffff";
grid_rows[5] = "6f976f7c82ffff967c6f976f7c82ffff";
grid_rows[6] = "ffffffffffffffffffffffffffffffff";
grid_rows[7] = "ffffffffffffffffffffffffffffffff";
grid_rows[8] = "ffffffb0b1b1ceb2ffffb0b1b1b1b1b2";
grid_rows[9] = "ffffff967c6f7c82ffff967c6f977c82";
grid_rows[10] = "ffffffffffffffffffffffffffffffff";
grid_rows[11] = "ffffffffffffffffffffffffffffffff";
grid_rows[12] = "f8f3f3f2fffffafbfbf3f3f3f3f2ffff";
grid_rows[13] = "f8f3f3f2fffffafbfbf3f3f3f3f2ffff";
grid_rows[14] = "f8f3f3f2fffffafbfbf3f3f3f3f2ffff";
grid_rows[15] = "ffffffffffffffffffffffffffffffff";
for (row_y = 0; row_y < 16; row_y += 1) {
    row_text = grid_rows[row_y];
    for (cell_x = 0; cell_x < 16; cell_x += 1) {
        tile_id = scr_stage01_hex_byte(row_text, cell_x);
        if (tile_id != 255) {
            xx = 1024 + cell_x * 16;
            yy = 256 + row_y * 16;
            tile_add(ts_restaurant_water_rabbit, (tile_id mod 16) * 16,
                     floor(tile_id / 16) * 16, 16, 16, xx, yy, 1000);
            if (tile_id >= 208 && tile_id != 249) {
                ds_grid_set(global.stage01_collision_grid, xx div 16, yy div 16, 2);
            } else if (tile_id >= 160 && tile_id != 249) {
                ds_grid_set(global.stage01_collision_grid, xx div 16, yy div 16, 1);
            }
        }
    }
}
