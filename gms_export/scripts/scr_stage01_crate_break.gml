/// scr_stage01_crate_break() | reveal the prize only when destroyed/opened
if (hidden_drop == 1) instance_create(x, y, obj_rre);
if (hidden_drop == 2) instance_create(x, y, obj_acorn);
instance_destroy();
