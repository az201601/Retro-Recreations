# Rescue Rangers 2 font sheet for GMS 1.4

`spr_font_rr2_8x10.png` is an 80×70 PNG containing **70 frames of 8×10 px**. It is
the 8×16 sheet cropped to the tallest ink row (row 9), so descenders (`g j p q y`)
are preserved without adding blank rows that would widen line spacing.

## Frame order

| Frames | Contents |
| --- | --- |
| 0 | blank (space) |
| 1–26 | `A`–`Z` |
| 27–52 | `a`–`z` |
| 53–62 | `0`–`9` |
| 63 | `:` |
| 64 | first double-quote glyph (open) |
| 65 | second double-quote glyph (closed) |
| 66 | `/` |
| 67 | `.` |
| 68 | `-` |
| 69 | blank (unused) |

## Import into GameMaker Studio 1.4.1760

1. Create sprite `spr_font_rr2` and import the PNG.
2. **Image → Convert to Frames…** — width **8**, height **10**, separators/margins 0.
   You should get **70 frames**.
3. Set sprite **Origin** to **(0, 0)**.
4. Create the font once (e.g. in a controller's Create event):

```gml
global.fnt_rr2 = font_add_sprite_ext(
    spr_font_rr2,
    ' ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789:^@/.-~',
    false,
    0
);
```

In text strings, type `^` for the opening quote and `@` for the closing quote;
they map to frames 64 and 65. Avoid using a literal `"` as a key: straight/curly
quote confusion can make the glyph fail to draw. Draw with `draw_set_font(global.fnt_rr2)`,
`draw_set_colour(c_white)`, `draw_set_halign(fa_left)`, `draw_set_valign(fa_top)`.
With 8×10 frames, plain `draw_text()` already has a tight 10 px line pitch; no
`sep` override is required.

## Line pitch — important

**Advance the next line by 10 px, not 8 px.** The cells are 8 px wide but 10 px
tall (the extra 2 px hold the descenders). If you position lines manually, use
`y + line_index * 10`. An 8 px step clips/crams the descenders into the next line.

Also note that a bare `#` in a GML string means newline — use `\#` or `chr(35)`
if you need a literal hash character in dialogue.
