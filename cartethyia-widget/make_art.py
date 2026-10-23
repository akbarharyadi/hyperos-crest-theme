"""Render the Cartethyia widget artwork (background banner + launcher preview).

Usage: python make_art.py <art_dir> <font.ttf> <res_dir>
Reads Cartethyia_2025-06-24.jpg (official Kuro Games art) from <art_dir>.
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ART, FONT, RES = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = 1200, 650                      # 4x2 home cells are ~1204x652 px on this phone
K = 3                                 # supersampling for the frame
NAVY = (8, 13, 36)
GOLD, AQUA, ICE = (216, 178, 106), (120, 205, 255), (240, 247, 255)


def chamfer(w, h, c, inset=0.0):
    i = inset
    d = i * 0.41
    return [(c + d, i), (w - c - d, i), (w - i, c + d), (w - i, h - c - d),
            (w - c - d, h - i), (c + d, h - i), (i, h - c - d), (i, c + d)]


# Fleurdelys (right side of the battle art) on the right of the banner; the home wallpaper
# already shows Cartethyia from the left side of the same art, so the widget complements it
src = Image.open(f"{ART}/Cartethyia_2025-06-24.jpg").convert("RGB")
crop = src.crop((1800, 300, 3400, 300 + round(1600 * H / W)))
art = crop.resize((W, H), Image.LANCZOS)

# dark navy fade on the left so the clock stays readable
a = np.asarray(art).astype(np.float32)
x = np.linspace(0, 1, W)[None, :, None]
fade = np.clip(1 - x / 0.62, 0, 1) ** 1.3 * 0.88
a = a * (1 - fade) + np.array(NAVY) * fade
y = np.linspace(0, 1, H)[:, None, None]
a = a * (1 - np.clip((y - 0.7) / 0.3, 0, 1) * 0.35)
banner = Image.fromarray(a.clip(0, 255).astype("uint8")).convert("RGBA")

# chamfered shape + gold crest border, drawn supersampled on separate layers
M = (W * K, H * K)
C = 46 * K
shape = Image.new("L", M, 0)
ImageDraw.Draw(shape).polygon(chamfer(*M, C, 6 * K), fill=255)
frame = Image.new("RGBA", M, (0, 0, 0, 0))
d = ImageDraw.Draw(frame)
outer = chamfer(*M, C, 12 * K)
d.line(outer + [outer[0]], fill=GOLD + (245,), width=4 * K, joint="curve")
inner = chamfer(*M, C - 8 * K, 22 * K)
d.line(inner + [inner[0]], fill=AQUA + (110,), width=1 * K, joint="curve")
for cx, cy in ((M[0] / 2, 12 * K), (M[0] / 2, M[1] - 12 * K)):
    h, w = 15 * K, 10 * K
    d.polygon([(cx, cy - h), (cx + w, cy), (cx, cy + h), (cx - w, cy)], fill=GOLD + (255,))
    d.polygon([(cx, cy - h / 2.4), (cx + w / 2.4, cy), (cx, cy + h / 2.4), (cx - w / 2.4, cy)], fill=ICE + (255,))
shape = shape.resize((W, H), Image.LANCZOS)
frame = frame.resize((W, H), Image.LANCZOS)

banner.putalpha(shape)
banner.alpha_composite(frame)
banner.save(f"{RES}/drawable-nodpi/widget_art.png", optimize=True)

# launcher preview: banner + sample text in the widget's font
prev = banner.copy()
d = ImageDraw.Draw(prev)
d.text((70, 150), "19:24", font=ImageFont.truetype(FONT, 190), fill=ICE + (255,))
d.text((78, 380), "Jumat, 23 Okt", font=ImageFont.truetype(FONT, 50), fill=GOLD + (255,))
d.text((80, 470), "CARTETHYIA  //  AERO", font=ImageFont.truetype(FONT, 30), fill=AQUA + (255,))
prev.resize((600, 325), Image.LANCZOS).save(f"{RES}/drawable-nodpi/widget_preview.png", optimize=True)

# app icon (shown in Settings > Apps only; the app has no launcher entry)
face = src.crop((2620, 470, 3140, 990)).resize((192, 192), Image.LANCZOS).convert("RGBA")
m = Image.new("L", (192 * K, 192 * K), 0)
ImageDraw.Draw(m).polygon(chamfer(192 * K, 192 * K, 30 * K), fill=255)
face.putalpha(m.resize((192, 192), Image.LANCZOS))
ring = Image.new("RGBA", (192 * K, 192 * K), (0, 0, 0, 0))
ImageDraw.Draw(ring).line(chamfer(192 * K, 192 * K, 30 * K, 4 * K) + [chamfer(192 * K, 192 * K, 30 * K, 4 * K)[0]],
                          fill=GOLD + (255,), width=6 * K, joint="curve")
face.alpha_composite(ring.resize((192, 192), Image.LANCZOS))
face.save(f"{RES}/drawable-nodpi/app_icon.png", optimize=True)
print("art written", banner.size)
