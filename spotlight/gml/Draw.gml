var tile = tiles[max(0,cursor_frame)];
draw_background_part(pages[tile div 16], (tile mod 4)*256, ((tile mod 16) div 4)*240, 256, 240, 0, 0);
