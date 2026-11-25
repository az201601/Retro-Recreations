/// scr_stage01_jet_step() | simple dynamic overlay, not a decoded NES effect
visible = (global.stage01_part == 2 && global.stage01_sink_active);
image_yscale = max(0.05, global.stage01_sink_fill / 100);
