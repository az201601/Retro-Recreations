# Sound engine (bank 6) — request interface, rendering method, state-1 sounds

Tool: `tools/render_sound.py` → `extracted/sounds/` (`snd_74.wav`,
`snd_73.wav`, `sounds.json`). The tool does **not** decode the sequence
data format by hand: it executes the game's real engine on a small 6502
core and synthesizes audio from the resulting APU register writes, so
the WAVs are the engine's own output (note timing, pitch, envelopes,
noise sweeps) at frame accuracy.

## How the game requests sound

- `$CE20` (fixed bank, A = id) — native request path. Ids `$01–$78`
  store to the pending slot `$F0` and to `$B6` ("current music id",
  with a same-id dedup); ids `$79–$7F` store to `$F0` only; id `$0F` is
  special-cased to both.
- `$CE31` (fixed bank, A = id) — the script VM's SOUND opcode (`$17`)
  path for ids `$22–$78`: a priority gate that only replaces `$F0` when
  no music-class request is pending and the `$72` loop isn't busy.
- Every NMI (when `$27` = 0) switches PRG bank 6 to `$8000` and calls
  `$8000`. After the call, if the engine left a finished music id in
  `$B7` and no music channel is active (`$F1 & $0F` = 0), the wrapper
  copies `$B7` back into `$B6`/`$F0` — music loops by re-request.

## Engine layout (bank 6)

- `$8000` — per-frame tick. If `$F0` has bit 7 clear a request is
  pending: `JSR $8200` starts it. Then channels are serviced (mask
  `$861C` against channel-active byte `$F1`; `$FC` selects 6-channel or
  SFX-only servicing), then `$81C2`/`$80A9` run the per-channel APU
  output stages (dispatch table `$80E5` via `JMP ($F3)`).
- `$8200` — start dispatcher. Sets `$F0 |= $80` (consumed), then:
  id `0` → `$8274`; ids `$01–$78` → `$832E`; ids `$79–$7F` jump via the
  table at `$8220`: `$79`→ mode `$FC`=0, `$7A`→ `$FC`=1 + silence
  channels, `$7B`/`$7C`→ `$F8`/`$F9` toggles, `$7D`→ start 4 channels
  from X=0, `$7E`→ start 2 channels from X=4, `$7F`→ `$8274`.
- `$8274` — **engine reset/stop**: zero `$4000–$4013`, defaults
  (`$4000/$4004=$08`, `$4008=$40`, `$400C=$10`, `$4015=$8F`,
  `$4017=$C0`), clear engine RAM `$0700–$07FC`, preload the master
  stream pointer `$92B5` at `$07EA`, mark all channels inactive.
  Requesting `$7F` therefore produces **no sound** — it silences the
  engine. (Verified by execution: zero audio output.)
- `$832E` — sequence start. Pointer table at `$87B5` indexed by id×2
  (121 nonzero entries). Header byte 0, bits `$30`: clear = music
  (channels 0–3, `$F1` bits 0–3), set = SFX (channels 4–5, `$F1` bits
  4–5); per-channel stream pointers follow in the header, started via
  `$82E3`. Channel state lives at `$0700–$07FF` (`$079C,X` = stream id,
  bit 7 = inactive; `$0766/$076C,X` = stream pointer); `$803F` fetches
  stream events (`$FE` = set loop point/tempo pair, bytes < `$FE` =
  length/index data — full format not decoded; execution doesn't need
  it).

## Rendering method (`tools/render_sound.py`)

6502 core (official opcodes, binary ADC/SBC as on the 2A03) + memory
map: 2 KB RAM mirrored, bank 6 at `$8000`, fixed bank at `$C000` (so
`$CE20/$CE31` run for real). Writes to `$4000–$4017` are logged per
tick. A render = cold-init ticks (zeroed RAM; first tick self-inits via
id 0), the request, then `$8000` ticks until the engine's channel mask
`$F1` clears. Synthesis implements pulse (4 duties, envelope/length,
sweep *muting* only — the engine writes `$4005=$08`, sweep disabled,
and bends pitch in software), triangle (linear/length counters), noise
(LFSR, both taps), DMC, and the standard NESdev mixing formulas at
44.1 kHz/16-bit. `--timeline` re-runs the whole state-1 script
schedule and diffs the APU write streams against the isolated renders.

## State-1 sounds (implemented in GML)

| Frame | Request | Path | Result |
|---|---|---|---|
| 0 (entry, `$D0D7`) | `$7F` | `$CE20` → `$8274` | engine reset — silence. GML mirrors with `audio_stop_all()` at `t == 0`. |
| 464 (SETY 104) | `$74` | VM SOUND → `$CE31` → `$832E` | SFX: pulse-2 tone warbling ≈147–196 Hz + swept noise whoosh, **2.34 s** (`snd_74.wav`). |
| 614 (WAIT start) | `$73` | VM SOUND → `$CE31` → `$832E` | SFX: sparse low pulse + long noise swell, **3.62 s** (`snd_73.wav`). |

Verification: in the full-timeline run, `$73`'s write stream matches
its isolated render exactly; `$74` matches until frame 614, where
`$73`'s start writes join the same tick (`$74` is already finished by
then — 2.34 s < the 2.50 s gap — so the two never interact, on
hardware or in GMS). `$73` rings ~2.6 s past the state-2 transition;
on the NES the SFX channels are not stopped by the music request, and
the GMS WAV behaves the same way.

## Deviations / TODO

- Synthesis is a close APU model, not cycle-level: `$4017` frame-counter
  cadence approximated (240/120 Hz clocks), hardware sweep not
  pitch-tracked (unused by this engine — it writes `$08` to `$4005`),
  DMC implemented but no state-1 sound uses it.
- Sounds for other screens (e.g. state 2's music `$01`, script SOUND
  `$32`) render with the same tool (`--id`) when those screens land;
  music looping via the `$B7` re-request is handled in the harness's
  tick wrapper but not yet needed by any shipped WAV.
