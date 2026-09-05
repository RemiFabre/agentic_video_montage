# microduck_lake_video — "Microduck and Reachy Mini, episode 2: the lake" (2026-09-04)

Source: `work/source/VID_20260904_152647.mp4` (copy of ~/Downloads, 63.1 s, phone vertical 1080x1920 after rotation, 30 fps).
Scene script + ElevenLabs line WAVs: `/Users/remi/reachy_mini_apps/agentic_robot_theater/scenes/lake/` (branch `scene/lake`).
Episode 1 reference: `~/Videos/microduck_skit/` (same caption look, same music/mix pipeline).

## Pipeline (same as episode 1)
1. `01_trimmed.mp4` = source 2.0 s -> 61.0 s (59.07 s). 2.0 s is the last static frame before the opening pan; 61.0 s = head down.
2. `scripts/align_lines.py` cross-correlates each robot line WAV with the footage -> `line_times.json`
   (hey 3.29, talk 7.26, bad_news 14.99, excuse 34.88, not_scared 53.04 in source time; consistent with the scene beat table).
3. `scripts/transcribe.py` (faster-whisper medium, cpu int8, venv `.venv-whisper`) -> `whisper_words.json`:
   word times inside each TTS WAV + the human lines in the footage ("But why?" 30.86, "But..." 42.3, "Are you scared?" 48.76).
4. `scripts/build_captions.py` -> `captions.json` / `captions.srt` (trimmed timeline). Speaker tags: REACHY MINI / THE HUMAN.
5. `scripts/burn_captions.py` -> `02_captioned.mp4`. PIL overlays (this ffmpeg has no subtitles/drawtext filter).
   Ep1 look: Arial Bold 58, white + 3 px black stroke, amber tag 30 px, black 150-alpha rounded box. Bottom margin 160 px (ep1 landscape used 90).
6. Music: ElevenLabs Music API via `agentic_robot_theater/video/gen_music.py` (62 s, instrumental), 8 tracks E01..E08 in `music/`,
   all variations on ep1's "light orchestral adventure" identity (D02) bent towards this episode's mood (bad news, nervous, scared).
7. `scripts/mix_music.sh` (ep1 template): music -12 dB, sidechain ducking under dialogue, 1.5 s fade-in, fade-out with the picture at the end.
   Outputs in `work/candidates/` (`lake_00_no_music_vertical.mp4` + one per track).

## Known issue (not treated yet)
Wind/handling noise in the mic during the first ~10 s (0-9.6 s of the source, i.e. over "Hey, Microduck!" and "Look, I have to talk to you."), gone afterwards.
Options when Rémi wants it treated: afftdn/arnndn on that window only, or a low-pass/highpass band, or let the music fade-in cover it.

## Mix levels (2026-09-04)
Ep1's mix: D02 mp3 at -12 dB sat ~1.8 dB above the dialogue RMS (dialogue -32 dB RMS, pre-duck), ducking threshold 0.02 (-34 dBFS) so ducking was mild.
Ep2 dialogue is -18.2 dB RMS (13.8 dB hotter). To reproduce the same balance: per-track gain = -18.2 + 1.8 - mp3_rms (E01 -0.1, E02 4.8, E03 1.1, E04 0.8, E05 1.4, E06 5.3, E07 -0.5, E08 3.7 dB)
and sidechain threshold 0.098 (THR env var in scripts/mix_music.sh). `_softer6dB` variant = E08 gain -2.3.
Measure RMS with INPUT seeking (`ffmpeg -ss X -t Y -i f -af astats`); output seeking feeds the whole file to astats.

## Round 2 (2026-09-04, after Rémi's feedback: wind annoying, music too loud)
- The "wind" is sub-150 Hz rumble (per-octave RMS: 0-150 Hz -16 dB, 150-300 Hz -37 dB). It runs 0-9 s of the cut, gusts again 12-16 s and ~20 s, then nothing (-49 dB) for the rest.
  afftdn (any setting) did not touch it; arnndn (sh.rnnn) removed the voice with it. A steep high-pass is the fix.
- `wind/dlg_FINAL.wav`: 0-8.5 s = HP 220 Hz x2 (24 dB/oct) + afftdn nr=15 + 10 dB makeup (Reachy is far from the phone in the opening);
  8-22.5 s = HP 220 x2 only; 22 s-end untouched (keeps Rémi's voice full); 0.5 s crossfades. Muxed onto the captioned video -> `03_captioned_clean.mp4`.
- Level lesson: my earlier "this take is 14 dB hotter than ep1" was the rumble. With it gone, the dialogue is ~-37 dB RMS like ep1 (-32), so ep1's mix settings
  (music -12 dB, sidechain threshold 0.02) apply as-is. The rescaled/"softer" mixes of round 1 were wrong and are deleted.
- `scripts/mix_music.sh` has a THR env var (sidechain threshold); default 0.02 = ep1.

## Round 3 (voice level inconsistent between parts)
- Cause: round 2 added +10 dB makeup on the opening only; the rest stayed at the raw (quiet) level, 5-8 dB under ep1's voice. Music then won.
- `scripts/clean_dialogue.py` -> `wind/dlg_FINAL_v3.wav`: HP220x2 + afftdn + 10 dB on 0-8.5 s; HP220x2 + 9 dB on 8-22.5 s (gusts) and 40.3-44.3 s
  (window-pan handling rumble, pure sub-150 Hz, was -15 dB after gain); HP160x2 + 9 dB elsewhere (keeps Rémi's voice full); 0.4 s crossfades; alimiter -1 dB.
- Result: every voice line within -23..-30 dB RMS (ep1 voice was -32), pan rumble -52 dB. Microduck's sound at 25-27 s sits at -13 dB (recorded close to the phone) — left as content.
- Mixes: ep1 settings (music -12 dB, threshold 0.02). Hands-free listening: `afplay <mp4>` works from the terminal; AppleScript to QuickTime is blocked by a permission prompt.

## Round 4: two-cue mixes (`scripts/mix_two_cues.sh`, output `candidates_switch/`)
Pivot at 40.9 s (garden fills the frame; pan starts 40.3, back on Reachy 43.5). Cue A = E04 faded out over 0.25 s ending at 40.9; cue B starts 41.2 s from its first onset (leading silence trimmed via silencedetect). Both -12 dB, ducked, same as ep1.

## FINAL (2026-09-04, Rémi: "PERFECT")
`final_versions/microduck_lake_E04_then_T1_vertical.mp4` = `candidates_switch/lake_switch_E04_then_T1_adventure_kickoff_vertical.mp4`, copied to `~/Videos/`.
Music: E04 pixar_confession until the garden reveal (40.9 s), 0.3 s silence, T1 adventure_kickoff from 41.2 s to the end. Rebuild:
`THR=0.02 zsh scripts/mix_two_cues.sh 03_captioned_clean.mp4 music/E04_pixar_confession.mp3 music_switch/T1_adventure_kickoff.mp3 out.mp4 40.9 41.2 1.027846 59.066 -12 -11.5`

## Round 5 (2026-09-05): landscape re-cut for YouTube after the vertical post underperformed (~20x less reach than ep1)
- Reasons discussed: Friday post, hype decay, and above all the vertical file became a Short on a long-form channel (Shorts and long-form are recommended separately; ep1 viewers are not shown ep2).
- `scripts/build_landscape.py` -> `landscape/lake_landscape_freeze_A.mp4` (1920x1080, 61.4 s): vertical picture scaled to 608x1080 on black sides;
  freeze at 41.6 s (garden fills the frame), ABSOLUTELY / PERFECT / WEATHER stamp in (Impact 230 px, white, 10 px black stroke, `landscape/make_words.py`),
  0.8 s each with a boom (ElevenLabs SFX `landscape/boom_A_vine.mp3`, -6 dB, peak -6.4 dBFS), then the picture resumes and T1 kicks in. E04 cut at 40.9 as before.
- Thumbnail: ep1's `~/Videos/agentic_socials/thumbnails/MEYsC6ikATo/final.jpg` had its text drawn by gpt-image-2 (rounded font, not on this Mac; all local bases
  already carry a different "NEW FRIEND?" in Impact). Fix: gpt-image-2 edit of final.jpg padded to 3:2 ("replace the text, same font, everything else identical"),
  then only the top 210 px band pasted onto final.jpg -> `thumbnail/composite_episode2_1.jpg` (robots pixel-identical, diff 2.6). Fallback without AI: cv2 inpaint + Passion One.
- Deliverables: `final_versions/microduck_lake_E04_freeze_T1_landscape.mp4`, `final_versions/microduck_lake_thumbnail_episode2_landscape.jpg`, both in ~/Videos.

## FINAL landscape (2026-09-05, Rémi's pick): boom C ("dun"), freeze at 42.6 s
`final_versions/microduck_lake_ep2_landscape.mp4` = `landscape/lake_landscape_freeze_C_late.mp4`, built with
`python3 scripts/build_landscape.py landscape/boom_C_dun.mp3 out.mp4 -6 42.6`. Thumbnail `final_versions/microduck_lake_ep2_thumbnail_landscape.jpg`. Both in ~/Videos.
The earlier freeze at 41.6 s left only 0.7 s of garden before the first word; 42.6 s is the last clean garden frame before the pan back.

## FINAL landscape v2 (2026-09-05): typewriter ending
`final_versions/microduck_lake_ep2_landscape.mp4` (64.1 s) = `landscape/lake_landscape_ending.mp4`, built with
`python3 scripts/build_landscape_v2.py landscape/boom_C_dun.mp3 out.mp4 -6 42.6 57.9 "Nice try but the lake trip is still ON."`
Freeze on Reachy's bowed head at 57.9 s (source), music continues, text types at 18 chars/s (Courier New Bold 66, click per char, bell on the period),
timed so the cue's natural final hit (cue time 17.0-17.5 s) lands on the last letters; 1.5 s hold, fade. The cue is 22 s and ends by itself, so the ending length is bounded by it.

## Thumbnail B (2026-09-05): sad duck + "NICE TRY"
Frame 23.0 s of the cut (01_trimmed, no captions; head just starting to droop, eye visible), 16:9 crop y=360..968 of the vertical frame, upscaled to 1280x720.
Text added by gpt-image-2 edit with ep1's final.jpg as a style reference (prompt `thumbnail/duck/prompt_nicetry.txt`); of 2 outputs one recomposed the shot (diff 24), the other is pixel-faithful (diff 2.1) -> kept.
`final_versions/microduck_lake_ep2_thumbnail_nicetry_landscape.jpg`. Thumbnail A stays `..._thumbnail_landscape.jpg` (ep1 photo, "EPISODE 2"). Both for YouTube Test & Compare.
Lesson: with gpt-image-2 edits, always request n=2 and keep the one whose pixels match the input outside the text; about half the outputs silently recompose.

## Thumbnails B and C, final (2026-09-05)
- B "DEVASTATED" (`final_versions/microduck_lake_ep2_thumbnail_devastated_landscape.jpg`): frame 23.0 s, whole duck sitting. gpt-image-2 always repaints when
  outpainting (three passes, duck re-rendered ~0.73x each time, prompts cannot stop it), so the accepted route is: outpaint (prompt_devastated2.txt) -> ask the model to
  re-frame its own image tighter (prompt_devastated_zoom.txt, feet near the bottom) -> scale 1536x1024 to 1080x720 and fill 100 px per side with mirrored + blurred edges
  (`thumbnail/duck/devastated_wide_1.jpg`). Cropping a 3:2 output to 16:9 always cuts either the text or the feet; widening with mirrored edges is the fix.
  Faithful (real-pixel) fallback: `thumbnail/duck/B2_blur_sides_ai_text.jpg`. Local inpaint + re-text attempts left residue at the top, abandoned.
- C "REAL ROBOTS" painting (`..._thumbnail_painting_realrobots_landscape.jpg`, no-text variant next to it): gpt-image-2 edit with Rémi's pencil-style Reachy Mini
  drawing as image 1 (style + character) and the Microduck product photo as image 2, prompt `thumbnail/painting/prompt_painting_text.txt`; robots called "robot A/B".
  Duck came out faithful. Same 16:9 widening trick. Lifting the model's text as a layer onto another image does not work on textured paper (grain in the mask).
