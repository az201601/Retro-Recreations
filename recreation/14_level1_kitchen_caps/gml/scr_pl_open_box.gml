/// scr_pl_open_box(column, row, new kind)
// Called by obj_player. The crate or bonus box in that block is gone (new kind 0), or a crate left the
// bonus box that was inside it (new kind 3). obj_stage1 draws the background there from the next frame on.
var c = argument0;
var r = argument1;
stage.lv_box[r, c] = argument2;
stage.lv_kind[r, c] = 0;                        // nothing to stand on or to walk into any more
var n = stage.lv_open_n;
stage.lv_open_i[n] = stage.lv_bi[r, c];         // which entry of the box table
stage.lv_open_t[n] = stage.lt;                  // when
stage.lv_open_k[n] = (argument2 == 3);          // true: a bonus box is shown there, false: the background
stage.lv_open_n = n + 1;
