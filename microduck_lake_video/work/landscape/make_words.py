"""Three cumulative overlays of ABSOLUTELY / PERFECT / WEATHER on the frozen landscape frame (Impact, full width, meme style)."""
from PIL import Image, ImageDraw, ImageFont
IMPACT = "/System/Library/Fonts/Supplemental/Impact.ttf"
base = Image.open("freeze_41.6.png").convert("RGBA"); W, H = base.size
words = ["ABSOLUTELY", "PERFECT", "WEATHER"]
TARGET_W = 1250
MAX_SIZE = 230
def fit(word):
    lo, hi = 50, 900
    while hi - lo > 1:
        mid = (lo + hi) // 2; f = ImageFont.truetype(IMPACT, mid)
        if ImageDraw.Draw(Image.new("L", (1, 1))).textlength(word, font=f) <= TARGET_W: lo = mid
        else: hi = mid
    lo = min(lo, MAX_SIZE); return ImageFont.truetype(IMPACT, lo), lo
fonts = [fit(w) for w in words]
sizes = [s for _, s in fonts]
# three rows sharing the height; row centres
total = sum(sizes) * 0.95; gap = (H - total) / 4
ys = []; y = gap
for s in sizes:
    ys.append(y + s * 0.95 / 2); y += s * 0.95 + gap
for k in range(1, 4):
    img = base.copy(); d = ImageDraw.Draw(img)
    for i in range(k):
        f, s = fonts[i]
        d.text((W / 2 + 10, ys[i] + 10), words[i], font=f, fill=(0, 0, 0, 200), anchor="mm")  # drop shadow
        d.text((W / 2, ys[i]), words[i], font=f, fill=(255, 255, 255, 255), anchor="mm", stroke_width=10, stroke_fill=(0, 0, 0, 255))
    img.convert("RGB").save(f"words_{k}.png")
print("sizes", sizes)
