# AGENTS.md — Co-creating short-form video montages

This document is the brief for an AI coding agent helping a user turn a raw recording (typically a screen-capture demo with voiceover) into a polished long-form + short-form package ready for YouTube, Shorts, TikTok, Reels, LinkedIn, etc. It is the distilled output of one full session that produced two video deliverables and two thumbnails. Read it end-to-end before starting.

The constraint that drives every decision below: **the user is iterating in a tight loop with you and is not going to read prose specs.** Show, don't tell. Render preview frames. Open them on screen. Ask short specific questions. Convergence is fast when the visual feedback loop is fast.

---

## 0. The non-negotiables

- **Never modify the original.** Make a `work/` subfolder and derive everything in there. The original mp4 is sacred. Many of the steps below are destructive (trim, denoise, re-encode); none of them touch the source.
- **Show, don't tell.** When proposing a crop, a layout, a thumbnail, a caption position — render an image, write the absolute path, open it via `eog <abs_path> &` (or platform equivalent). Never describe a layout in prose first. The visual is the proposal.
- **Always cite absolute paths.** The user opens files outside your shell. Relative paths waste a turn.
- **Iterate on stills before video.** Full re-encodes are slow (1–3 min). Preview frames are instant. If you're choosing between layouts, render every candidate as a 1920×1080 (or 1080×1920) PNG and pop them up side by side.
- **Never preemptively over-engineer.** If the user asks for a "simple symmetric center crop" first, give them that crop verbatim. If it loses content, *show* the loss visually — then propose the more complex layout. Skipping the simple version because you know better forces the user to circle back.
- **Fix root causes, not symptoms.** A weird audio artifact at the start? Don't shave 2 seconds off the trim — figure out it's `loudnorm` single-pass adapting gain and switch to two-pass. A subtitle not rendering at the right time? Don't reposition it — figure out that `-ss` before `-i` reset the timeline and use output seek.

---

## 1. The pipeline

```
original.mp4
    │
    ▼
trim         →  work/01_trimmed.mp4         # cut start/end with re-encode
    │
    ▼
denoise      →  work/02_denoised.mp4        # 2-pass loudnorm + afftdn
    │
    ├──► whisper  →  captions.json (word timestamps) + captions.srt (editable)
    │              user edits SRT for proper nouns / contractions whisper mishears
    │
    ├──► detect UI rectangles (only for screen-capture sources)
    │              brightness/saturation profile + grid overlay → user confirms coords
    │
    ▼
montage layout iteration (preview frames)
    │              propose 2–3 stills → user picks → tweak → confirm
    │
    ▼
captions.ass  ←  word-by-word karaoke (cyan highlight)
    │
    ▼
final_versions/long_landscape.mp4    (1920×1080 for YT main / LinkedIn)
final_versions/long_vertical.mp4     (1080×1920 — usually skipped)
final_versions/short_vertical.mp4    (1080×1920 highlights for Shorts / Reels / TikTok)
final_versions/thumbnail_landscape.png  (1536×1024)
final_versions/thumbnail_vertical.png   (1024×1536)
```

Don't run the pipeline straight through. Pause for user approval at every visual decision: trim points, detected rectangles, montage layout, caption text, thumbnail composition, segment cuts for the short. Each pause is a chance to redirect cheaply.

---

## 2. Folder convention

```
work/
├── 02_denoised.mp4              # cleaned source, the input to all montage work
├── captions.{srt,json,ass}      # SRT for human edits, JSON for word timings, ASS for karaoke
├── detected_v5.png              # the chosen rectangle-detection overlay (kept for traceability)
├── montage_NEW_BALANCED.png     # the locked layout still
├── final_versions/              # the deliverables, named with _landscape / _vertical
│   ├── long_landscape.mp4
│   ├── long_vertical.mp4
│   ├── short_vertical.mp4
│   ├── thumbnail_landscape.png
│   └── thumbnail_vertical.png
├── thumbnails/                  # current candidates and base frames for the AI thumbnail
├── iterations/                  # everything rejected, archived for traceability
│   ├── detection/    (early detect scripts + overlays)
│   ├── montage/      (rejected layout previews)
│   ├── samples/      (frame grabs, audio extracts, intermediate trims)
│   ├── long_versions/   (long_v1, long_v3 silence-cut, etc.)
│   ├── short_iterations/  (short_v1, short_v2, …)
│   └── thumbnail_iterations/
└── scripts/
    ├── detect_panes.py         # the brightness-profile detector that worked
    ├── transcribe.py           # whisper SRT/JSON generator
    ├── captions_to_ass.py      # JSON → ASS karaoke
    ├── make_landscape_ass.py   # vertical ASS → landscape ASS (font/margin/PlayRes tweak)
    ├── silence_cut.py          # detect silences, cut, re-time captions
    └── thumbnail_*.py          # gpt-image-2 calls, one per thumbnail variant
```

**Naming convention** for `final_versions/`: every file ends in `_landscape` or `_vertical`. The user uses these as deliverables and won't tolerate ambiguous filenames.

When a version is locked in `final_versions/`, archive the previous one to `iterations/<category>/<old_name>.mp4`. Don't delete; the user may want to compare.

---

## 3. Trim

Cut start and end to drop dead air. *Re-encode* — don't `-c copy` because keyframe-aligned cuts cause drift.

```bash
ffmpeg -ss <start> -to <end> -i original.mp4 \
  -c:v libx264 -preset medium -crf 18 \
  -c:a aac -b:a 192k -movflags +faststart \
  work/01_trimmed.mp4
```

Ask the user for start/end timestamps. They usually know.

---

## 4. Denoise audio (the start-of-clip artifact)

A common foot-gun: `loudnorm` in single-pass mode auto-adapts gain at the start because it has no audio history. Result: the first 1–2 seconds are obviously louder/distorted, then it settles. Users notice instantly and complain.

**Fix: two-pass loudnorm.** First pass measures, second pass applies the measured values explicitly.

```bash
# Pass 1 — measure
ffmpeg -i work/01_trimmed.mp4 \
  -af "highpass=f=80,afftdn=nr=18:nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json" \
  -f null - 2>&1 | tail -25
# Read the JSON: input_i, input_tp, input_lra, input_thresh, target_offset

# Pass 2 — apply with measured values
ffmpeg -i work/01_trimmed.mp4 -c:v copy \
  -af "highpass=f=80,afftdn=nr=18:nf=-25,\
loudnorm=I=-16:TP=-1.5:LRA=11:\
measured_I=<v>:measured_TP=<v>:measured_LRA=<v>:measured_thresh=<v>:offset=<v>:linear=true" \
  -c:a aac -b:a 192k -movflags +faststart work/02_denoised.mp4
```

`afftdn nr=18 nf=-25` is a good baseline for typical webcam-mic hiss. If the user reports residual hiss, bump `nr` to 25–30. `highpass=f=80` cuts low-frequency rumble (HVAC, room hum) without touching speech.

If the user reports a problem at the very start ("intense annoying sound for the first two seconds"), it's almost always loudnorm single-pass. Switch to two-pass before suspecting anything else.

---

## 5. Captions: precise word-level timing with whisper

The user wants captions that highlight word-by-word in sync with speech (CapCut-style). That requires word-level timestamps, which `faster-whisper` provides via `word_timestamps=True`.

### 5.1 Run whisper

```python
from faster_whisper import WhisperModel
model = WhisperModel("medium", device="cuda", compute_type="float16")
segments, info = model.transcribe(
    audio_path, language="en", beam_size=5,
    word_timestamps=True, condition_on_previous_text=True,
)
```

Notes:
- Older `faster-whisper` versions don't accept `vad_filter`. Inspect the signature first if uncertain (`inspect.signature(WhisperModel.transcribe)`).
- Feed it the *denoised* audio. Slightly better accuracy on noisy clips.
- 16 kHz mono WAV is what whisper wants:
  ```bash
  ffmpeg -i in.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 audio16k.wav
  ```

### 5.2 Group words into caption chunks

Don't render whisper's word stream raw. Group into chunks that read fluidly:
- ≤ 7 words per chunk
- ≤ 42 characters per chunk
- ≤ 2.8 s duration per chunk
- split on a > 0.6 s gap or sentence-ending punctuation

This produces ~3–5 word captions that flow naturally with the speech rhythm.

### 5.3 Emit two files

- `captions.srt` — editable. The user will scan it and ask you to fix obvious errors. Whisper consistently mishears:
  - Proper nouns it hasn't seen ("Reachy Mini" → "rich mini")
  - Contractions ("I'd love" → "I love")
  - Words that sound similar in context ("very likely" → "very lucky")
  - Acronyms
- `captions.json` — preserves word-level start/end. **Required** for any timeline-affecting operation later (silence cuts, manual segment cuts that need to snap to word boundaries, regenerating ASS).

### 5.4 ASS karaoke (word-by-word colour highlight)

For CapCut-style highlighting, generate an ASS file where each word is a separate Dialogue line that displays the *whole chunk* with that word colour-tagged.

For each chunk's words `w[0..n-1]`:
- Emit one Dialogue line per word, spanning `w[i].start → w[i+1].start` (last word: `w[n-1].start → w[n-1].end`).
- The line's text is the full chunk, with `w[i]` wrapped in a colour override:

  ```
  ... before ... {\1c&H00FFD75A&}word{\1c&H00FFFFFF&} ... after ...
  ```

  (Cyan #5AD7FF for the active word, white for the rest. ASS colour format is `&HAABBGGRR&` — alpha + BGR, not RGB.)

#### CRITICAL: don't toggle `\b` per word

If you render the active word bold (`\b1`) and the rest non-bold (`\b0`), the text widths change, libass re-flows the line, and the chunk *visibly reshapes* as words step. This is jarring and the user will notice. Solutions:
- Set `Bold=1` in the Style row (everything bold by default).
- Don't put `\b0` or `\b1` in any Dialogue line. Only colour changes.

This was the single most reported caption issue from the live session.

#### Position captions where there's "nothing interesting"

Burned captions need a low-information background. Find a band in the source content where nothing important happens — for a screen-capture demo with two webcam panes + a chart region, the natural caption band is just above the chart region, where the chart's title bar lives.

For 9:16 vertical (1080×1920) with the BALANCED layout (RAW pane top, bars below, face crop right): captions at MarginV ≈ 910 (i.e. y ≈ 1010 in canvas) sit cleanly in the lower third of the RAW pane.

For 16:9 landscape (1920×1080) with a height-filling source: captions at MarginV ≈ 460 sit in the gap above the bars.

### 5.5 Apply user-approved text fixes from one place

When the user approves a caption fix ("change *very lucky* to *very likely*"), apply it in the JSON→ASS converter, not by editing the SRT manually. That way:
- The SRT and ASS stay in sync.
- Re-running the converter (after re-detecting silences, cutting hesitations, etc.) preserves the fix.
- Substitution map example:

  ```python
  for i, w in enumerate(words):
      stripped = w["word"].strip(" ,.!?;:").lower()
      if stripped == "rich":  w["word"] = w["word"].replace("rich", "Reachy")
      elif stripped == "mini": w["word"] = w["word"].replace("mini", "Mini")
      elif stripped == "lucky": w["word"] = w["word"].replace("lucky", "likely")
      elif stripped == "love" and i > 0 and words[i-1]["word"].strip() == "I":
          words[i-1]["word"] = words[i-1]["word"].replace("I", "I'd")
      # context-dependent insertions:
      elif stripped == "if" and matches_pattern(words, i, ["not", "very", "technical"]):
          w["word"] = w["word"].replace("if", "if you're")
  ```

### 5.6 ffmpeg seek and subtitles — common foot-gun

Input seek (`-ss <t> -i input`) resets the timeline so the subtitles filter can't find its cues. **Always use output seek** (`-i input -ss <t>`) when generating preview frames with burned subtitles. Slower but accurate.

If you absolutely need input seek for performance, add `-copyts` to preserve timestamps.

### 5.7 Burning captions

```bash
ffmpeg -i in.mp4 -vf "subtitles=captions.ass" \
  -c:v libx264 -preset medium -crf 20 \
  -c:a aac -b:a 192k -movflags +faststart out.mp4
```

The `subtitles=` filter takes an absolute path and burns into pixels.

For LANDSCAPE captions from a vertical ASS, you don't need to regenerate — just rewrite the header:

```python
text = vertical_ass.read_text()
text = text.replace("PlayResX: 1080", "PlayResX: 1920")
text = text.replace("PlayResY: 1920", "PlayResY: 1080")
# Adjust Style line: smaller font + new MarginV for landscape positioning
text = text.replace(
    "Style: Caps,DejaVu Sans,52,...,3.5,...,910,1",
    "Style: Caps,DejaVu Sans,42,...,3,...,460,1",
)
```

---

## 6. Detect UI rectangles in screen-capture sources

When the source is a screen recording of a multi-pane UI (browser app, dashboard, IDE), you need to know the *exact* pixel coordinates of each content rectangle to compose a montage. **Don't eyeball them.** Detect, overlay, confirm.

### Strategy

For a UI with a dark navy background and bright/colourful content panes:

1. **Sample background colour from a *known* dark-UI region** — not (0, 0). The very corners often have browser chrome (light/white). Better: sample at `img[H-50:H-10, 0:30]`, `img[400:440, 0:20]` etc.
2. **Compute per-row mean luma.** Rows with mean > 60 are inside a bright-content band.
3. **Within that band, compute per-column mean luma.** Columns with mean > 50 separate the panes left/right.
4. **For chart/bars regions below the panes:** detect "any pixel ≠ background" rows. The chart text + orange bars together exceed the navy.

The exact thresholds are content-dependent. Iterate until the result looks right.

### Communicate via overlay

The detection script must produce a PNG with:
- Each detected rectangle drawn with a thick coloured outline (4–5 px).
- A label box on top of each rectangle: `name x=X y=Y w=W h=H` — coordinates immediately readable.
- A faint coordinate grid every 50 px, with yellow numeric labels every 100 px.

The grid is the fallback. If detection is even slightly off, the user can read off the corrected coords and dictate them. The user described this exact format ("detected_v5.png") as "an excellent way of communicating about areas on an image."

---

## 7. Montage layout iteration

This is the slowest, highest-touch phase. Render preview frames, not videos.

### Iteration discipline

1. The user usually has a *first idea* that's simpler than what you'd build. Honour it. Render exactly what they asked for.
2. If it loses critical content, render the loss explicitly (i.e. show what gets cut) so they can see the trade-off.
3. Then propose 2–3 alternatives that recover the lost content. Render each as a still. Pop them all up.
4. Let the user pick or describe a tweak. Re-render.
5. Lock the layout *only* via a still frame they explicitly approve. Don't render the full video until they say so.

### Layout examples that worked

For a UI with two side-by-side webcam panes (RAW + TRACKED) + a chart band:

- **STACK (9:16, 1080×1920):**
  - RAW pane scaled to fill width: 1080×810, top.
  - TRACKED face-crop centred mid-canvas.
  - Chart bars below, full-width.
  - Title in the natural empty space above RAW.
  - Captions at the lower third of the RAW pane.

- **BALANCED (9:16) — the lock for the demo:**
  - RAW full-width 1080×810 at top.
  - Chart split into two columns and *vertically stacked*, then placed in the left half of the bottom region (540×839).
  - TRACKED face-crop as a tall portrait (260×404 source → 540×839) in the right half — height-matched to the stacked chart for visual symmetry.
  - Title strip 271 px at the top.

- **LANDSCAPE (16:9, 1920×1080):**
  - Crop browser chrome at top (y=0..103) and bottommost ~110 px of bars (the less-active rows).
  - Resulting 1258×717 source has aspect 1.755 — within 1.3 % of 16:9 — scales to 1755×1000 with ~82 px navy on each side.
  - 80 px title strip at the top.
  - Captions at MarginV ≈ 460 (just above the bars).

### Useful ffmpeg patterns

**Vertically stack a two-column chart** to fit a tall vertical canvas:

```
[0:v]crop=BW:BH:BX:BY,split=2[full1][full2];
[full1]crop=BW/2:BH:0:0[left];
[full2]crop=BW/2:BH:BW/2:0[right];
[left][right]vstack[stacked]
```

**Compose a 9:16 BALANCED-style montage:**

```
ffmpeg -i in.mp4 -filter_complex "
  [0:v]crop=BW:BH:BX:BY,split=2[bf1][bf2];
  [bf1]crop=BW/2:BH:0:0[bl]; [bf2]crop=BW/2:BH:BW/2:0[br];
  [bl][br]vstack,scale=540:-2[bars];
  [0:v]crop=RAW_w:RAW_h:RAW_x:RAW_y,scale=1080:-2[raw];
  [0:v]crop=FACE_w:FACE_h:FACE_x:FACE_y,scale=540:839[face];
  color=c=0x101426:s=1080x1920:d=<DUR>[bg];
  [bg][raw]overlay=0:271[a];
  [a][bars]overlay=0:1081[b];
  [b][face]overlay=540:1081[c];
  [c]drawtext=fontfile=...:text='<TITLE>':fontsize=52:x=(w-text_w)/2:y=110[d];
  [d]drawbox=x=(w-220)/2:y=190:w=220:h=4:color=0x5AD7FF[e];
  [e]subtitles=captions.ass[v]
" -map [v] -map 0:a -c:v libx264 -crf 20 -c:a aac -b:a 192k out.mp4
```

---

## 8. Cut a short version (manual segment cuts)

Once the long version is locked, the short is built by cherry-picking segments from the long. **Cut from the locked long, not from the raw source** — so the cuts inherit the burned-in title and captions automatically.

### Process

1. Ask the user for rough timestamps of segments to keep ("0:00 to about 1:12, then 1:19-ish to 1:23, then…").
2. Snap each rough timestamp to the nearest natural boundary using `captions.json` word data:
   - The end of a sentence (`word ends with ".!?"`).
   - The largest gap (> ~0.5 s) between two adjacent words.
3. Pad each segment by ~0.2 s on the trailing side so the audio doesn't cut mid-breath.
4. Build with one `ffmpeg filter_complex` using `trim`/`atrim` for each segment and `concat` to stitch:

```
ffmpeg -i long.mp4 -filter_complex "
  [0:v]trim=0.5:72.24,setpts=PTS-STARTPTS[v0];
  [0:a]atrim=0.5:72.24,asetpts=PTS-STARTPTS[a0];
  [0:v]trim=79.36:86.50,setpts=PTS-STARTPTS[v1];
  [0:a]atrim=79.36:86.50,asetpts=PTS-STARTPTS[a1];
  ...
  [v0][a0][v1][a1]...concat=n=N:v=1:a=1[v][a]
" -map [v] -map [a] -c:v libx264 -crf 20 -c:a aac -b:a 192k short.mp4
```

### Audio fade for the final segment

If the very last segment ends near a word boundary and the next word is audible right after the cut (lip-click, breath, "It's"), don't shorten the cut — that drops the final word. Instead apply a 200–300 ms `afade` on the final segment's audio:

```
[0:a]atrim=111.42:114.55,asetpts=PTS-STARTPTS,afade=t=out:st=2.83:d=0.30[a5];
```

This fades audio to silence over the last 0.3 s while the visible video cuts cleanly.

---

## 9. Hesitation / silence cuts (Lever 1)

For tightening a long-winded recording: detect long silences, compress them. Don't blindly remove all silence — many "silences" are deliberate (showing a demo on screen, dramatic pause). Default thresholds:

- **Threshold:** silences ≥ 0.8 s
- **Target:** compress to 0.25 s

Implementation:
1. Run `ffmpeg silencedetect=noise=-30dB:duration=0.8` on the denoised audio. Parse `silence_start:` / `silence_end:` lines.
2. For each silence, mark a "skip range" of `(start + TARGET, end)` — keeps the first 0.25 s as a natural micro-pause.
3. Build keep-ranges (complement of skips). Cut with one `ffmpeg select`/`aselect` pass:

   ```bash
   ffmpeg -i in.mp4 \
     -vf "select='between(t,0,1.5)+between(t,1.75,3.0)+...',setpts=N/FRAME_RATE/TB" \
     -af "aselect='...',asetpts=N/SR/TB" \
     -c:v libx264 -crf 18 -c:a aac out.mp4
   ```

   ffmpeg's `select` treats `between(...)+between(...)` as a sum (any non-zero = keep frame). Works as an OR.

4. **Re-time captions.** Every cut shifts the timeline. For each whisper word, subtract the cumulative skipped duration before its timestamp:

   ```python
   def adjust(t, skips):
       offset = 0.0
       for s, e in skips:
           if t >= e: offset += (e - s)
           elif t >= s: return max(0.0, s - offset)  # word inside cut → clamp
       return max(0.0, t - offset)
   ```

5. Regenerate captions.ass from the adjusted JSON, render the long version with the new audio + new captions.

**Important caveat the user will surface:** silences during demos (where the user is making a movement on screen but not speaking) MUST NOT be cut. If the user objects to a silence-cut version, switch to manual segment cuts (section 8) and forget Lever 1.

There's a Lever 2 for filler-word cuts ("um/uh/er") but whisper usually omits these, requiring extra audio analysis. Only attempt if the user specifically complains about audible filler words.

---

## 10. Thumbnails with gpt-image-2

Thumbnails are generated with OpenAI's `gpt-image-2` (organisation-verified key required). Two approaches that work:

### Approach A — pure compositing (PIL)

When the user wants the photo on top *exactly preserved* and only text below: do it in PIL. No AI. No risk of hallucinated detail.

```python
from PIL import Image, ImageDraw, ImageFont
img = Image.open(base).convert("RGB")
draw = ImageDraw.Draw(img)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 96)
# wrap title to 3 lines, center in band, draw cyan accent rule above
```

### Approach B — gpt-image-2 with the photo as base layout

When the user wants a *designed* bottom band with extra graphic elements (wireframe illustration, dot grid, accents) and is OK with the AI re-rendering the band:

```python
client.images.edit(
    model="gpt-image-2",
    image=open(base_layout_png, "rb"),
    prompt=PROMPT,
    size="1024x1536", quality="high", n=1,
)
```

The base layout is a 1024×1536 (or 1536×1024) PNG you compose with ffmpeg: the photographic top half + a flat dark navy band at the bottom. The prompt tells gpt-image-2 to preserve the top exactly and design the bottom band.

### Multi-image references

For products with a specific visual identity (e.g. a robot with a distinctive silhouette), pass *two* images to `client.images.edit`:

```python
with open(base, "rb") as fh1, open(product_ref, "rb") as fh2:
    r = client.images.edit(
        model="gpt-image-2",
        image=[fh1, fh2],   # SDK accepts a list
        prompt=PROMPT, size="1536x1024", quality="high",
    )
```

Reference images are just visual prompts. To get an *accurate tracing* (not an artistic interpretation):
- State explicitly: "MUST be a faithful tracing of Image 2 — same head tilt, same antenna placement, same eye positions." Be specific about each visual feature.
- Negative-prompt list the wrong patterns: "Do NOT add a humanoid face, mouth, nose, ears, arms, legs, hands."
- Use the word "tracing" and "blueprint" to push the model toward direct replication.
- If the first result is generic, regenerate with an even more directive prompt. Two attempts usually nail it.

### Cost & timing

`gpt-image-2` `high` quality at 1024×1536 or 1536×1024: ~$0.22–0.25 per image, ~150–180 s per call. Don't iterate by tweaking the prompt and regenerating 5 times — write a careful prompt the first time, run it, look, and only regenerate if there's a clear specific issue.

---

## 11. Format & platform recommendations

What to render and where to upload:

| Platform | File | Why |
|---|---|---|
| YouTube main channel | `long_landscape.mp4` (1920×1080) | 16:9 fills the player; algorithm classifies as long-form |
| YouTube Shorts | `short_vertical.mp4` (1080×1920) | 9:16 native; ≤ 3 min cap |
| TikTok | `short_vertical.mp4` | 9:16 native; landscape underperforms severely |
| Instagram Reels | `short_vertical.mp4` | Same as TikTok |
| LinkedIn | `long_landscape.mp4` | Landscape-first feed, technical audience tolerates long-form |
| X / Twitter | `long_landscape.mp4` | 16:9 native on web; consider posting `short_vertical` as a reply |
| Reddit (r/robotics, r/MachineLearning, etc.) | `long_landscape.mp4` | 16:9 player; technical subs want the full demo |
| Personal blog / embed | `long_landscape.mp4` | Standard 16:9 |

**Do not skip making `long_landscape.mp4`.** Every multi-platform deployment needs both the vertical short and a landscape long. The vertical-long version (1080×1920 for the full duration) is rarely used as a deliverable — it's an intermediate from which `short_vertical` is cut.

---

## 12. Communication style

- **Open every preview image with `eog <abs_path> &`** so it pops up. The user is not going to click your relative paths.
- **Cite absolute paths.** Always.
- **Tasks via TaskCreate / TaskUpdate.** Mark in_progress when starting, completed when done. Don't batch updates.
- **Match response length to the task.** A simple confirmation gets a one-line answer. A multi-decision proposal gets headers + a tight summary.
- **End-of-turn summary: 1–2 sentences.** What changed, what's next. Nothing else.
- **No emojis** in code, in comments, in user-facing text — unless the user asks.
- **No co-author / authorship lines** in commits unless the user asks.
- **No "I think we should…"** — propose with a recommendation and a tradeoff, and trust the user to redirect.

---

## 13. Common foot-guns to avoid

- **Single-pass loudnorm at the start.** Always two-pass. (See §4.)
- **`-ss` before `-i`** when burning subtitles in a preview frame. Use output seek. (See §5.6.)
- **Toggling `\b` per word in ASS karaoke.** Causes line reflow. Colour only. (See §5.4.)
- **Eyeballing UI pane coordinates.** Detect and overlay. (See §6.)
- **Rendering full videos to compare layouts.** Use stills. (See §0.)
- **Cutting silences inside demo moments.** Manual segment cuts beat blind silence compression. (See §9.)
- **Pre-emptive complex montages.** Honour the user's first simple idea, *then* show why it doesn't work if it doesn't. (See §0.)
- **Not naming `final_versions/` files with `_landscape` / `_vertical` suffixes.** Ambiguous filenames break the user's distribution flow. (See §2.)
- **Forgetting to pop files via `eog`.** It's the single biggest UX win in the loop.

---

## 14. Reusable snippets

### Word-aligned segment-boundary finder

```python
import json
data = json.load(open("captions.json"))
words = [(w["start"], w["end"], w["word"].strip())
         for s in data["segments"] for w in s.get("words", [])]
prev_end = None
for s, e, t in words:
    if T_LO < s < T_HI:
        gap = f"  GAP={s-prev_end:.2f}s" if prev_end else ""
        print(f"  {s:7.3f} - {e:7.3f}  {t!r}{gap}")
        prev_end = e
```

Use this when the user says "cut around 1:23". Find natural breaks before/after that timestamp and propose specific candidates.

### Coordinate-grid detection overlay

Every detection script's output PNG must include:

```python
for x in range(0, W, 50):
    a = 70 if x % 100 else 130
    draw.line([(x, 0), (x, H)], fill=(255, 255, 255, a))
    if x % 100 == 0:
        draw.rectangle([x, 0, x + 32, 14], fill=(0, 0, 0, 200))
        draw.text((x + 2, 1), str(x), fill=(255, 255, 0))
# same for y
```

Plus the labelled rectangles. The grid is the fallback for the user to dictate corrected coords.

### eog + absolute path response template

```bash
eog /home/<user>/.../preview.png > /dev/null 2>&1 &
# In the response: "Opened: /home/<user>/.../preview.png"
```

For multiple files, batch them in a single `eog file1.png file2.png &` call.

---

## 15. The mental model

The user is the director. You are the editor and the renderer. The user has the taste and the final cut authority. You have the tools and the speed. Convergence is fast when:

- You propose visually, not in prose.
- You ask one specific question per turn.
- You honour the simple version of every request before pitching the complex one.
- You separate "what to render" from "what to keep" — you can render five variants cheaply; only one becomes a deliverable.
- You name and organise files so the user can grab them without thinking.

That's the whole job. The ffmpeg incantations, the whisper recipes, the gpt-image-2 prompts — they're all in service of the loop above.
