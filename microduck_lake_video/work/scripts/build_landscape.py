"""Landscape (1920x1080, black sides) master with the freeze-frame gag at the window reveal:
video freezes at FREEZE, ABSOLUTELY / PERFECT / WEATHER stamp in one by one (HOLD s each) with a boom each,
then the picture resumes and the upbeat cue (T1) kicks in. Music before: E04 cut at PIVOT. Same levels as the vertical final."""
import subprocess, sys
IN = "03_captioned_clean.mp4"; A = "music/E04_pixar_confession.mp3"; B = "music_switch/T1_adventure_kickoff.mp3"; B_OFF = 1.027846
BOOM = sys.argv[1] if len(sys.argv) > 1 else "landscape/boom_A_vine.mp3"
OUT = sys.argv[2] if len(sys.argv) > 2 else "landscape/lake_landscape_freeze.mp4"
BOOM_DB = float(sys.argv[3]) if len(sys.argv) > 3 else -6.0
SRC_END = 59.066; PIVOT = 40.9; FREEZE = 41.6; HOLD = 0.8; N = 3
GAP = HOLD * N; END = SRC_END + GAP; RESUME = FREEZE + GAP
FADE_AT = END - 0.6; MFADE = END - 1.0; THR = 0.02; DB = -12; BDB = -11.5
words = [f"landscape/words_{k}.png" for k in range(1, N + 1)]
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", IN, "-i", A, "-ss", str(B_OFF), "-i", B, "-i", BOOM]
for w in words: cmd += ["-loop", "1", "-t", str(HOLD), "-i", w]
V = "scale=-2:1080,pad=1920:1080:(ow-iw)/2:0:black,fps=30,format=yuv420p,setsar=1"
fc = f"[0:v]{V},split=2[va][vb];[va]trim=0:{FREEZE},setpts=PTS-STARTPTS[p1];[vb]trim={FREEZE},setpts=PTS-STARTPTS[p3];"
for k in range(N): fc += f"[{4+k}:v]fps=30,format=yuv420p,setsar=1[w{k}];"
fc += "[p1]" + "".join(f"[w{k}]" for k in range(N)) + f"[p3]concat=n={N+2}:v=1:a=0,fade=t=out:st={FADE_AT}:d=0.6[vout];"
fc += (f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[a1][a2];[a1]atrim=0:{FREEZE},asetpts=PTS-STARTPTS[d1];"
       f"[a2]atrim={FREEZE},asetpts=PTS-STARTPTS[d3];aevalsrc=0:d={GAP}:s=48000,aformat=sample_rates=48000:channel_layouts=stereo[sil];"
       f"[d1][sil][d3]concat=n=3:v=0:a=1,afade=t=out:st={FADE_AT}:d=0.6,asplit=2[dlg][key];")
fc += (f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:{PIVOT},volume={DB}dB,afade=t=in:st=0:d=1.5,afade=t=out:st={PIVOT-0.25}:d=0.25,apad=whole_dur={END}[ma];"
       f"[2:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={BDB}dB,afade=t=in:st=0:d=0.12,adelay={int(RESUME*1000)}|{int(RESUME*1000)},atrim=0:{END},afade=t=out:st={MFADE}:d=1.0[mb];"
       f"[ma][mb]amix=inputs=2:normalize=0:duration=first[mus];[mus][key]sidechaincompress=threshold={THR}:ratio=5:attack=40:release=700:makeup=1[ducked];")
fc += f"[3:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={BOOM_DB}dB,asplit={N}" + "".join(f"[b{k}]" for k in range(N)) + ";"
for k in range(N):
    t = int((FREEZE + k * HOLD) * 1000); fc += f"[b{k}]adelay={t}|{t},apad=whole_dur={END}[bd{k}];"
fc += "".join(f"[bd{k}]" for k in range(N)) + f"amix=inputs={N}:normalize=0:duration=first[booms];"
fc += "[dlg][ducked][booms]amix=inputs=3:normalize=0:duration=first[aout]"
cmd += ["-filter_complex", fc, "-map", "[vout]", "-map", "[aout]", "-t", str(END), "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT]
subprocess.run(cmd, check=True); print("wrote", OUT, "END", END)
