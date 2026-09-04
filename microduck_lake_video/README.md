# microduck_lake_video

"Microduck and Reachy Mini, episode 2: the lake" (2026-09-04), a 59 s vertical phone skit. Final: `work/final_versions/microduck_lake_E04_then_T1_vertical.mp4` (also in `~/Videos/`).

Only the scripts, timing files and notes are versioned here (media is git-ignored). Read `work/NOTES.md` for the full recipe, timings and the lessons of the session, and `work/DECISIONS.md` for the decision log as it was shown to Rémi. The generic lessons are folded into the root `AGENTS.md` (section 16).

Pipeline in one line: trim -> align TTS line WAVs to the footage (`scripts/align_lines.py`) -> whisper word times (`scripts/transcribe.py`) -> `captions.json` (`scripts/build_captions.py`) -> PIL caption burn (`scripts/burn_captions.py`) -> dialogue clean-up (`scripts/clean_dialogue.py`) -> ElevenLabs music beds -> ducked mix (`scripts/mix_music.sh`, or `scripts/mix_two_cues.sh` for a mid-video music switch).
