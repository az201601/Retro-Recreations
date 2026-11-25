/// scr_stage01_spawn_actors()  |  generated from NES room object lists
/// Requires every referenced obj_* resource in the GMS 1.4 project.
/// Spawns all actors up-front, unlike the ROM's scroll-column insertion.
/// Exit, faucet, Monterey and boss behavior require implementation.

// seating
instance_create(384, 544, obj_enemy_honeybee);
instance_create(512, 672, obj_enemy_fork_rat);
instance_create(640, 576, obj_enemy_honeybee);
instance_create(816, 704, obj_enemy_fork_rat);
instance_create(1088, 544, obj_enemy_honeybee);
instance_create(1248, 592, obj_enemy_fork_rat);
instance_create(1376, 608, obj_enemy_honeybee);
instance_create(1568, 576, obj_enemy_honeybee);
instance_create(1728, 592, obj_enemy_fork_rat);
instance_create(1904, 544, obj_enemy_honeybee);
instance_create(1936, 704, obj_enemy_fork_rat);
instance_create(2016, 672, obj_stage01_exit_right);

// kitchen
instance_create(240, 1936, obj_enemy_fake_box);
instance_create(432, 1984, obj_enemy_spoon_rat);
instance_create(688, 1952, obj_enemy_fake_box);
instance_create(928, 1888, obj_enemy_spoon_rat);
instance_create(1248, 1984, obj_enemy_spoon_rat);
instance_create(1424, 1984, obj_enemy_fake_box);
instance_create(1504, 1920, obj_enemy_spoon_rat);
instance_create(1456, 1616, obj_enemy_fake_box); // ROM vertical-spawn flag
instance_create(1584, 1632, obj_enemy_bottle_cork);
instance_create(1664, 1728, obj_enemy_spoon_rat);
instance_create(1712, 1632, obj_enemy_bottle_cork);
instance_create(1840, 1632, obj_enemy_bottle_cork);
instance_create(1952, 1728, obj_enemy_fake_box);
instance_create(2000, 1600, obj_star_prize);
instance_create(2016, 1728, obj_stage01_exit_right);

// grill
instance_create(448, 1472, obj_enemy_fork_rat);
instance_create(704, 1376, obj_enemy_honeybee);
instance_create(960, 1472, obj_enemy_fork_rat);
instance_create(1248, 1312, obj_enemy_honeybee);
instance_create(1312, 1472, obj_enemy_fork_rat);
instance_create(1584, 1328, obj_sink_valve);
instance_create(1728, 1488, obj_zipper_in_box);
instance_create(1776, 1440, obj_stage01_exit_right);

// monterey
instance_create(128, 1168, obj_monterey_refill);

// water_rabbit
instance_create(1264, 384, obj_boss_water_rabbit);
