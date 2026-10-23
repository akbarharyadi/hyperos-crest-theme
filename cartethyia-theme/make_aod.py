"""Square always-on-display images (the HyperOS "Gambar kustom" AOD frame is 1:1).

Usage: python make_aod.py <art_dir> <out_dir>
A: Cartethyia head-to-waist from the cut-out sprite, aqua glow, fades into black.
B: the same portrait inside the gold crest octagon used by the icons and widget.
"""
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw

ART, OUT = sys.argv[1], sys.argv[2]
N, K = 1080, 3
GOLD, AQUA, ICE = (216, 178, 106), (120, 205, 255), (240, 247, 255)

sprite = Image.open(f"{ART}/Cartethyia_Full_Sprite.png").convert("RGBA")   # 1424x2068
# head-to-waist window of the sprite, square
bust = sprite.crop((150, 0, 150 + 1150, 1150)).resize((N, N), Image.LANCZOS)


def glow_bg(strength=0.55):
    yy, xx = np.mgrid[0:N, 0:N]
    r = np.sqrt((xx - N * 0.5) ** 2 + (yy - N * 0.42) ** 2) / (N * 0.55)
    g = (np.clip(1 - r, 0, 1) ** 2.2 * strength)[..., None]
    bg = (np.array(AQUA) * 0.55 + np.array((30, 50, 120)) * 0.45) * g
    return Image.fromarray(bg.astype("uint8")).convert("RGBA")


def fade_edges(im, start=0.62):
    """Fade the image to black towards the bottom so the figure has no hard cut."""
    a = np.asarray(im).astype(np.float32)
    y = np.linspace(0, 1, N)[:, None, None]
    k = 1 - np.clip((y - start) / (1 - start), 0, 1) ** 1.5
    a[..., :3] *= k
    return Image.fromarray(a.clip(0, 255).astype("uint8"))


# ---- A: big portrait with glow
a = glow_bg()
a.alpha_composite(bust)
a = fade_edges(a).convert("RGB")
a.save(f"{OUT}/09_aod_cartethyia_portrait.png")


# ---- B: crest octagon frame
def octagon(size, c, inset=0.0):
    i, d = inset, inset * 0.41
    return [(c + d, i), (size - c - d, i), (size - i, c + d), (size - i, size - c - d),
            (size - c - d, size - i), (c + d, size - i), (i, size - c - d), (i, c + d)]


M = N * K
win = Image.new("L", (M, M), 0)
ImageDraw.Draw(win).polygon(octagon(M, M * 0.16, M * 0.07), fill=255)
win = win.resize((N, N), Image.LANCZOS)
inner = glow_bg(0.75)
b = Image.new("RGBA", (N, N), (0, 0, 0, 255))
inner.putalpha(win)
b.alpha_composite(inner)
frame = Image.new("RGBA", (M, M), (0, 0, 0, 0))
d = ImageDraw.Draw(frame)
for inset, col, w in ((M * 0.07, GOLD + (255,), 7 * K), (M * 0.095, AQUA + (120,), 2 * K)):
    pts = octagon(M, M * 0.16, inset)
    d.line(pts + [pts[0]], fill=col, width=w, joint="curve")
for cy in (M * 0.07, M - M * 0.07):
    h, w = M * 0.032, M * 0.021
    d.polygon([(M / 2, cy - h), (M / 2 + w, cy), (M / 2, cy + h), (M / 2 - w, cy)], fill=GOLD + (255,))
    d.polygon([(M / 2, cy - h / 2.4), (M / 2 + w / 2.4, cy), (M / 2, cy + h / 2.4), (M / 2 - w / 2.4, cy)], fill=ICE + (255,))
b.alpha_composite(frame.resize((N, N), Image.LANCZOS))
# portrait on top: clipped to the window below, free above it so the crown breaks out of the frame
pop = np.zeros((N, N), np.uint8)
pop[: int(N * 0.30)] = 255
clip = Image.fromarray(np.maximum(np.asarray(win), pop))
fig = fade_edges(bust, 0.70)
fig.putalpha(ImageChops.multiply(fig.getchannel("A"), clip))
b.alpha_composite(fig)
b.convert("RGB").save(f"{OUT}/10_aod_cartethyia_crest.png")

sheet = Image.new("RGB", (N * 2 + 30, N), (40, 40, 40))
sheet.paste(Image.open(f"{OUT}/09_aod_cartethyia_portrait.png"), (0, 0))
sheet.paste(Image.open(f"{OUT}/10_aod_cartethyia_crest.png"), (N + 30, 0))
sheet.resize((sheet.width // 2, N // 2)).save(f"{OUT}/../previews/aod_options.jpg", quality=88)
print("written")
