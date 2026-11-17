/// rm_title - Room Creation Code
// Room: 256 x 240, no views.  Instance layer: obj_gamecontroller (persistent).
// The title artwork (assets_vec/ui/title_screen.png) is drawn by obj_title, so
// no background needs to be assigned.
// ============================================================================
global.game_state = "title";
instance_create(0, 0, obj_title);
