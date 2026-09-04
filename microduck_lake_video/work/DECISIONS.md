# Lake episode — what was done, what to decide

Folder: `/Users/remi/agentic_video_montage/microduck_lake_video/work/candidates/`
Open any `lake_E0x_*_vertical.mp4` to hear a music option; `lake_00_no_music_vertical.mp4` is captions only.

## Autonomous calls (veto in one line)
- **Cut:** source 2.0 s -> 61.0 s (59 s). 2.0 s is the last static frame before the pan.
- **Captions:** same look as episode 1. Your lines are tagged **THE HUMAN**: "But why?", "But...", "Are you scared?".
  The excuse is split as "Because, well..." / "the meteorological conditions are..." / "not optimal right now." (follows the nervous pause in the line).
- **Vertical frame:** captions sit 160 px above the bottom (ep1 landscape used 90 px) so phone UI does not cover them.
- **Music identity:** episode 1 direction was "light orchestral adventure, companionship, a bit serious" (D02 family). The 8 new tracks keep the french horn + pizzicato identity and bend it toward this episode:
  - E01 adventure_bittersweet, E02 adventure_nervous, E03 adventure_rain (clarinet), E04 pixar_confession (piano),
    E05 adventure_march_soft, E06 music_box_adventure, E07 strings_courage, E08 adventure_ep2 (same theme, minor key).
- **Mix:** ep1 template (ducked under dialogue, fades with the picture at the end), but this take was recorded ~14 dB hotter than ep1,
  so the music gain and the ducking threshold were rescaled per track to reproduce ep1's music-to-voice balance.
  `lake_E08_adventure_ep2_softer6dB_vertical.mp4` is the same as E08 with the music 6 dB lower, in case ep1's balance feels loud here.

## Round 2 (after your feedback)
- **Wind:** it is low-frequency rumble (<150 Hz), 0-9 s of the cut, with gusts again at 12-16 s and ~20 s. Spectral/RNN denoisers did nothing or killed the voice.
  Fix applied: steep 220 Hz high-pass on the whole track (nothing audible lives below 220 Hz elsewhere), light denoise + 10 dB makeup on the opening only
  (Reachy is far from the phone there, so its two first lines were ~18 dB quieter than the rest). Previews in `work/wind/` (opened):
  `preview_orig.mp4` vs `preview_H_hp220.mp4` (no gain) vs `preview_L_hp220_dn_gain10.mp4` (chosen) vs `preview_M_hp220_dn_gain14.mp4` (louder),
  and `preview_9to22s_orig.mp4` vs `preview_9to22s_FINAL.mp4` for the gusts under the lake line.
- **Music level:** back to episode 1's exact settings (music -12 dB, same ducking threshold). The "match the ratio" idea is dropped; `_softer6dB` removed.

## Decisions for you (RESOLVED: final = E04 then T1 switch, see NOTES.md)
1. **Music pick:** which E0x (or "more takes of E0x", or "none")? Default if you say nothing: E08.
2. **Wind fix:** OK as chosen (+10 dB opening), or prefer no makeup gain / +14 dB?
3. **Ending:** keep 61.0 s, or end 0.5 s earlier/later?
4. **Hand-off:** once picked, the final goes to `~/Videos/microduck_lake_<track>_vertical.mp4`.

## Round 4: music switch at the reveal (separate folder, candidates untouched)
Folder: `work/candidates_switch/`. E04 (Pixar confession) plays until the garden fills the frame (40.9 s), is cut sharply, 0.3 s of nothing, then an upbeat cue kicks in at 41.2 s and runs to the end (fades with the picture).
Second-cue options (22 s ElevenLabs cues, `work/music_switch/`):
- T1 adventure_kickoff: french horn call, brisk pizzicato, snare/timpani (closest to the ep1 identity)
- T2 cheeky_march: bassoon/clarinet staccato march, "calling the bluff"
- T3 sunny_reveal: glockenspiel, bright strings, ukulele, claps (the sunniest)
- T4 swashbuckling_mini: brass fanfare, driving strings, castanets (the most heroic)
Levers if you like the idea: pivot instant (40.9 now), gap length (0.3 s), cue B a bit louder than -12 dB for the entrance, or end the upbeat cue early (~56 s) so the head-down lands in silence.
`scripts/mix_two_cues.sh` builds these.
