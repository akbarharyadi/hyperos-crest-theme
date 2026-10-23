"""Build a Cartethyia (Wuthering Waves) HyperOS theme + wallpapers + sounds.

Usage: python build_theme.py <assets_dir> <output_dir>
Reads:  <assets_dir>/{art_orig, audio_dl, font_dl}/ (see ../fetch_assets.py) and, optionally,
        <assets_dir>/mtz_ref/Talos-Endfield.mtz as a source of per-app glyphs for the "Glyph" variant.
Writes: <output_dir>/{Cartethyia-WuWa.mtz, Cartethyia-WuWa-nofont.mtz, [Cartethyia-WuWa-glyph.mtz],
        wallpapers/, sounds/, previews/}
"""
import io
import os
import sys
import zipfile

import numpy as np
import soundfile as sf
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

S, OUT = sys.argv[1], sys.argv[2]
ART, AUD, FONT = f"{S}/art_orig", f"{S}/audio_dl", f"{S}/font_dl/Marcellus-Regular.ttf"
SCREEN = (1280, 2772)

# Cartethyia palette (sampled from official art): navy, royal blue, aqua glow, ice white, gold
NAVY_TOP, NAVY_BOT = (24, 40, 92), (8, 13, 36)
AQUA, ICE, ICE_LOW, GOLD = (120, 205, 255), (240, 247, 255), (165, 222, 255), (216, 178, 106)

for d in ("wallpapers", "sounds", "previews"):
    os.makedirs(f"{OUT}/{d}", exist_ok=True)


def fit_cover(im, size, cx=0.5):
    """Scale to cover `size`, then crop horizontally around relative center cx."""
    w, h = size
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = min(max(round(im.width * cx - w / 2), 0), im.width - w)
    y = (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def bottom_shade(im, start=0.62, strength=0.35):
    """Darken the lower part so the dock and labels stay readable."""
    w, h = im.size
    ramp = np.clip((np.arange(h) / h - start) / (1 - start), 0, 1) * strength
    mask = Image.fromarray((ramp[:, None].repeat(w, 1) * 255).astype("uint8"))
    return Image.composite(Image.new("RGB", im.size, (4, 6, 18)), im, mask)


def remove_logo(im, box):
    """Paint over the top-left WUTHERING WAVES logo using the clean column right of it."""
    a = np.asarray(im).astype(np.float32)
    x0, y0, x1, y1 = box
    ref_r = a[y0:y1, x1 + 6:x1 + 18].mean(axis=1)  # per-row background colour, right side
    ref_l = a[y0:y1, max(x0 - 18, 0):max(x0 - 6, 1)].mean(axis=1)
    t = np.linspace(0, 1, x1 - x0)[None, :, None]
    a[y0:y1, x0:x1] = ref_l[:, None] * (1 - t) + ref_r[:, None] * t
    return Image.fromarray(a.clip(0, 255).astype("uint8"))


# ---------------------------------------------------------------- wallpapers
battle = Image.open(f"{ART}/Cartethyia_2025-06-24.jpg").convert("RGB")      # 3840x2160, dark blue
book = Image.open(f"{ART}/Cartethyia_2025-06-18.jpg").convert("RGB")        # 1152x2048, bright

home = bottom_shade(fit_cover(battle.crop((470, 0, 470 + 997, 2160)), SCREEN))

# locate the dark logo glyphs in the top-left corner of the bright art
corner = np.asarray(book.crop((0, 0, 420, 220)).convert("L"))
ys, xs = np.where(corner < 150)
logo = (max(xs.min() - 8, 0), max(ys.min() - 8, 0), xs.max() + 9, ys.max() + 9)
lock = fit_cover(remove_logo(book, logo), SCREEN)

fleur = fit_cover(battle.crop((2200, 0, 2200 + 997, 2160)), SCREEN)
extras = {
    "02_lock_cartethyia_book.jpg": lock,
    "01_home_cartethyia_sword.jpg": home,
    "03_fleurdelys_closeup.jpg": fleur,
    "04_poster_cartethyia.jpg": fit_cover(Image.open(f"{ART}/Cartethyia_2025-03-24.jpg").convert("RGB"), SCREEN),
    "05_poster_fleurdelys.jpg": fit_cover(Image.open(f"{ART}/Fleurdelys_2025-03-26.jpg").convert("RGB"), SCREEN),
    "06_cartethyia_doves.jpg": fit_cover(Image.open(f"{ART}/Cartethyia_2025-06-19.jpg").convert("RGB"), SCREEN),
}

# AOD / OLED-friendly: cut-out sprite on pure black
sprite = Image.open(f"{ART}/Cartethyia_Full_Sprite.png").convert("RGBA")
s = SCREEN[1] * 0.80 / sprite.height
sprite_s = sprite.resize((round(sprite.width * s), round(sprite.height * s)), Image.LANCZOS)
aod = Image.new("RGBA", SCREEN, (0, 0, 0, 255))
aod.alpha_composite(sprite_s, ((SCREEN[0] - sprite_s.width) // 2, SCREEN[1] - sprite_s.height - 120))
extras["07_aod_cartethyia_black.png"] = aod.convert("RGB")

splash = Image.open(f"{ART}/Cartethyia_Splash_Art.png").convert("RGBA")
bg = Image.new("RGBA", SCREEN)
grad = np.linspace(0, 1, SCREEN[1])[:, None, None]
bg = Image.fromarray(((np.array(NAVY_TOP) * (1 - grad) + np.array(NAVY_BOT) * grad).repeat(SCREEN[0], 1)).astype("uint8")).convert("RGBA")
sp = splash.resize((1280, 1280), Image.LANCZOS)
bg.alpha_composite(sp, (0, (SCREEN[1] - 1280) // 2 - 120))
extras["08_splash_on_navy.jpg"] = bg.convert("RGB")

for name, im in extras.items():
    p = f"{OUT}/wallpapers/{name}"
    im.save(p, quality=95) if name.endswith(".jpg") else im.save(p)


# ---------------------------------------------------------------- icons
N, K = 351, 4                       # final size, supersampling factor
C = 16                              # chamfer (percent of icon) for the crest-like octagon mask
MASK_PATH = f"M {C} 0 L {100-C} 0 L 100 {C} L 100 {100-C} L {100-C} 100 L {C} 100 L 0 {100-C} L 0 {C} Z"


def octagon(inset, size):
    c = size * C / 100
    i = inset
    return [(c + i * 0.41, i), (size - c - i * 0.41, i), (size - i, c + i * 0.41), (size - i, size - c - i * 0.41),
            (size - c - i * 0.41, size - i), (c + i * 0.41, size - i), (i, size - c - i * 0.41), (i, c + i * 0.41)]


def make_background():
    M = N * K
    g = np.linspace(0, 1, M)[:, None, None]
    base = (np.array(NAVY_TOP) * (1 - g) + np.array(NAVY_BOT) * g).repeat(M, 1)
    yy, xx = np.mgrid[0:M, 0:M]
    r = np.sqrt((xx - M / 2) ** 2 + (yy - M * 0.18) ** 2) / (M * 0.62)
    glow = np.clip(1 - r, 0, 1) ** 2 * 0.30
    base = base * (1 - glow[..., None]) + np.array(AQUA) * glow[..., None]
    im = Image.fromarray(base.astype("uint8")).convert("RGBA")
    # translucent strokes go on their own layer: ImageDraw replaces pixels instead of blending
    over = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    # Aero "wind" arcs, very faint, kept in the bottom-left corner away from the glyph
    for k, a in ((0, 60), (1, 38)):
        off = k * 0.07 * M
        d.arc([-0.30 * M - off, 0.62 * M + off, 0.55 * M - off, 1.45 * M + off], 275, 345, fill=AQUA + (a,), width=2 * K)
    # gold crest border + aqua hairline
    d.line(octagon(14 * K, M) + [octagon(14 * K, M)[0]], fill=GOLD + (235,), width=3 * K, joint="curve")
    d.line(octagon(22 * K, M) + [octagon(22 * K, M)[0]], fill=AQUA + (90,), width=1 * K, joint="curve")
    # diamond gems top and bottom centre
    for cy in (14 * K, M - 14 * K):
        h, w = 9 * K, 6 * K
        d.polygon([(M / 2, cy - h), (M / 2 + w, cy), (M / 2, cy + h), (M / 2 - w, cy)], fill=GOLD + (255,))
        d.polygon([(M / 2, cy - h / 2.4), (M / 2 + w / 2.4, cy), (M / 2, cy + h / 2.4), (M / 2 - w / 2.4, cy)], fill=ICE + (255,))
    im.alpha_composite(over)
    return im.resize((N, N), Image.LANCZOS)


def recolor_glyph(fg):
    alpha = fg.getchannel("A")
    bbox = alpha.getbbox() or (0, 0, N, N)
    g = np.zeros((N, 1, 1))
    g[:, 0, 0] = np.clip((np.arange(N) - bbox[1]) / max(bbox[3] - bbox[1], 1), 0, 1)
    fill = (np.array(ICE) * (1 - g) + np.array(ICE_LOW) * g).repeat(N, 1)
    glyph = Image.fromarray(fill.astype("uint8")).convert("RGBA")
    glyph.putalpha(alpha)
    glow_a = alpha.filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * 0.55))
    glow = Image.new("RGBA", (N, N), AQUA + (0,))
    glow.putalpha(glow_a)
    out = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    out.alpha_composite(glow)
    out.alpha_composite(glyph)
    return out


REF = f"{S}/mtz_ref/Talos-Endfield.mtz"     # optional: per-app glyphs for the Glyph variant
HAVE_GLYPHS = os.path.exists(REF)
ref_icons = zipfile.ZipFile(io.BytesIO(zipfile.ZipFile(REF).read("icons"))) if HAVE_GLYPHS else None
pkgs = sorted({n.split("/")[2] for n in ref_icons.namelist() if n.startswith("res/drawable-xxhdpi/")}) if HAVE_GLYPHS else []
bg_png = io.BytesIO()
background = make_background()
background.save(bg_png, "PNG")

icons_buf = io.BytesIO()
composed = {}
with zipfile.ZipFile(icons_buf, "w", zipfile.ZIP_DEFLATED) as zi:
    zi.writestr("transform_config.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<IconTransform>
    <Config name="SupportLayerIcon" value="true" />
    <Config name="UseDynamicIcon" value="false" />
    <Config name="ConfigIconMask" value="{MASK_PATH}" />
</IconTransform>
""")
    for p in pkgs:
        fg = Image.open(io.BytesIO(ref_icons.read(f"res/drawable-xxhdpi/{p}/1.png"))).convert("RGBA")
        new_fg = recolor_glyph(fg)
        b = io.BytesIO()
        new_fg.save(b, "PNG")
        zi.writestr(f"res/drawable-xxhdpi/{p}/0.png", bg_png.getvalue())
        zi.writestr(f"res/drawable-xxhdpi/{p}/1.png", b.getvalue())
        c = background.copy()
        c.alpha_composite(new_fg)
        composed[p] = c


# Colour-frame icon pack: HyperOS keeps each app's ORIGINAL icon and frames it.
# miui IconCustomizer.composeIcon() (SupportLayerIcon=false, non-full ConfigIconMask):
#   original icon -> cut by icon_mask (DST_IN) -> icon_background (tinted by the icon's
#   average colour, so not used) -> icon_pattern (drawn as-is: our navy plate) ->
#   cut icon -> icon_border on top. All files are rescaled to customizer_icon_size (67dp).
F = 432                                  # frame canvas size, rescaled on the phone
INNER = 0.115                            # inset of the colour window (navy rim width)


def make_color_frame():
    M = F * K
    yy, xx = np.mgrid[0:M, 0:M]
    g = (yy / M)[..., None]
    base = np.array(NAVY_TOP) * (1 - g) + np.array(NAVY_BOT) * g
    r = np.sqrt((xx - M / 2) ** 2 + (yy - M * 0.15) ** 2) / (M * 0.62)
    glow = (np.clip(1 - r, 0, 1) ** 2 * 0.30)[..., None]
    base = base * (1 - glow) + np.array(AQUA) * glow
    plate = Image.fromarray(base.astype("uint8")).convert("RGBA")
    shape = Image.new("L", (M, M), 0)
    ImageDraw.Draw(shape).polygon(octagon(M * 0.01, M), fill=255)
    plate.putalpha(shape)
    over = Image.new("RGBA", (M, M), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for k, a in ((0, 70), (1, 45)):
        off = k * 0.06 * M
        d.arc([-0.30 * M - off, 0.66 * M + off, 0.52 * M - off, 1.40 * M + off], 280, 345, fill=AQUA + (a,), width=2 * K)
    plate.alpha_composite(over)
    plate.putalpha(ImageChops.multiply(plate.getchannel("A"), shape))

    mask = Image.new("L", (M, M), 0)
    ImageDraw.Draw(mask).polygon(octagon(M * INNER, M), fill=255)

    border = Image.new("RGBA", (M, M), (0, 0, 0, 0))
    d = ImageDraw.Draw(border)
    outer = octagon(M * 0.045, M)
    d.line(outer + [outer[0]], fill=GOLD + (245,), width=round(M * 0.022), joint="curve")
    inner = octagon(M * INNER, M)
    d.line(inner + [inner[0]], fill=AQUA + (150,), width=round(M * 0.008), joint="curve")
    for cy in (M * 0.045, M - M * 0.045):
        h, w = M * 0.045, M * 0.030
        d.polygon([(M / 2, cy - h), (M / 2 + w, cy), (M / 2, cy + h), (M / 2 - w, cy)], fill=GOLD + (255,))
        d.polygon([(M / 2, cy - h / 2.4), (M / 2 + w / 2.4, cy), (M / 2, cy + h / 2.4), (M / 2 - w / 2.4, cy)], fill=ICE + (255,))

    def down(im):
        return im.resize((F, F), Image.LANCZOS)

    return down(plate), down(mask), down(border)


frame_pattern, frame_mask, frame_border = make_color_frame()
mask_rgba = Image.new("RGBA", (F, F), (255, 255, 255, 0))
mask_rgba.putalpha(frame_mask)
color_icons_buf = io.BytesIO()
with zipfile.ZipFile(color_icons_buf, "w", zipfile.ZIP_DEFLATED) as zi:
    # inset path so isFullMask stays false (bounds must not contain (50, 0))
    zi.writestr("transform_config.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<IconTransform>
    <Config name="SupportLayerIcon" value="false" />
    <Config name="UseDynamicIcon" value="false" />
    <Config name="ConfigIconMask" value="M {C+2} 2 L {98-C} 2 L 98 {C+2} L 98 {98-C} L {98-C} 98 L {C+2} 98 L 2 {98-C} L 2 {C+2} Z" />
</IconTransform>
""")
    for name, im in (("icon_pattern.png", frame_pattern), ("icon_mask.png", mask_rgba), ("icon_border.png", frame_border)):
        b = io.BytesIO()
        im.save(b, "PNG")
        zi.writestr(f"res/drawable-xxhdpi/{name}", b.getvalue())


def framed_preview(fg_rgba, fill):
    """Approximate the phone's composition for previews: plate + coloured window + glyph + border."""
    out = frame_pattern.copy()
    win = Image.new("RGBA", (F, F), fill + (255,))
    win.putalpha(frame_mask)
    out.alpha_composite(win)
    g = fg_rgba.resize((F, F), Image.LANCZOS)
    white = Image.new("RGBA", (F, F), (255, 255, 255, 0))
    white.putalpha(g.getchannel("A"))
    out.alpha_composite(white)
    out.alpha_composite(frame_border)
    return out


BRAND = {"com.kurogame.wutheringwaves.global": ((40, 48, 70), "W"), "com.whatsapp": ((37, 211, 102), "W"),
         "com.android.chrome": ((66, 133, 244), "C"), "com.android.camera": ((60, 60, 66), "C"),
         "com.google.android.youtube": ((255, 0, 0), "Y"), "com.android.settings": ((110, 118, 130), "S"),
         "com.google.android.apps.maps": ((52, 168, 83), "M"), "com.android.vending": ((1, 135, 95), "P"),
         "com.twitter.android": ((15, 15, 15), "X"), "com.instagram.android": ((225, 48, 108), "I"),
         "com.discord": ((88, 101, 242), "D"), "com.google.android.gm": ((234, 67, 53), "G")}


def preview_glyph(pkg, letter):
    """Glyph for preview icons: the reference glyph when available, otherwise a Marcellus letter."""
    if HAVE_GLYPHS and pkg in composed:
        return Image.open(io.BytesIO(ref_icons.read(f"res/drawable-xxhdpi/{pkg}/1.png"))).convert("RGBA")
    g = Image.new("RGBA", (F, F), (0, 0, 0, 0))
    ImageDraw.Draw(g).text((F / 2, F / 2), letter, font=ImageFont.truetype(FONT, int(F * 0.42)),
                           fill=(255, 255, 255, 255), anchor="mm")
    return g


color_composed = {p: framed_preview(preview_glyph(p, letter), c) for p, (c, letter) in BRAND.items()}


def masked(icon, size):
    m = Image.new("L", (N * K, N * K), 0)
    ImageDraw.Draw(m).polygon(octagon(0, N * K), fill=255)
    m = m.resize((N, N), Image.LANCZOS)
    out = icon.copy()
    out.putalpha(ImageChops.multiply(icon.getchannel("A"), m))
    return out.resize((size, size), Image.LANCZOS)


# ---------------------------------------------------------------- previews
PW, PH = 540, round(540 * SCREEN[1] / SCREEN[0])
font_big, font_mid, font_small = (ImageFont.truetype(FONT, s) for s in (118, 34, 20))

lockp = lock.resize((PW, PH), Image.LANCZOS).convert("RGBA")
d = ImageDraw.Draw(lockp)
d.text((40, 70), "10:24", font=font_big, fill=(28, 38, 80, 255))
d.text((44, 205), "Friday, 23 October", font=font_mid, fill=(40, 52, 100, 255))

homep = home.resize((PW, PH), Image.LANCZOS).convert("RGBA")
d = ImageDraw.Draw(homep)
d.text((34, 120), "CARTETHYIA", font=ImageFont.truetype(FONT, 64), fill=ICE + (255,))
d.text((38, 196), "WUTHERING WAVES  //  AERO", font=font_small, fill=GOLD + (255,))
show = ["com.kurogame.wutheringwaves.global", "com.whatsapp", "com.android.chrome", "com.android.camera",
        "com.google.android.youtube", "com.android.settings", "com.google.android.apps.maps", "com.android.vending",
        "com.twitter.android", "com.instagram.android", "com.discord", "com.google.android.gm"]
show = [p for p in show if p in color_composed]
for i, p in enumerate(show):
    x, y = 30 + (i % 4) * 124, PH - 430 + (i // 4) * 130
    homep.alpha_composite(color_composed[p].resize((104, 104), Image.LANCZOS), (x, y))

cover = Image.new("RGB", (PW * 2 + 12, PH), (6, 9, 24))
cover.paste(lockp.convert("RGB"), (0, 0))
cover.paste(homep.convert("RGB"), (PW + 12, 0))
cover = cover.resize((PW, round(PH * PW / (PW * 2 + 12))), Image.LANCZOS)

previews = {"preview_cover_0.jpg": cover, "preview_lockscreen_0.jpg": lockp.convert("RGB"), "preview_icons_0.jpg": homep.convert("RGB")}
for n, im in previews.items():
    im.save(f"{OUT}/previews/{n}", quality=90)


# ---------------------------------------------------------------- mtz
def jpg(im, q=95):
    b = io.BytesIO()
    im.save(b, "JPEG", quality=q)
    return b.getvalue()


DESC = """<?xml version="1.0" encoding="utf-8"?>
<theme>
  <version>1</version>
  <osVersion>3</osVersion>
  <uiVersion>15</uiVersion>
  <author>WuWa Fan</author>
  <designer>WuWa Fan</designer>
  <title>Cartethyia // Wuthering Waves{suffix}</title>
  <description>Cartethyia theme: official Kuro Games art wallpapers, {icons}{font}.</description>
  <authors>
    <author locale="en_US">WuWa Fan</author>
  </authors>
  <designers>
    <designer locale="en_US">WuWa Fan</designer>
  </designers>
  <titles>
    <title locale="en_US">Cartethyia // Wuthering Waves{suffix}</title>
  </titles>
</theme>
"""
COLOR_DESC = "original app icons in navy and gold crest frames"
GLYPH_DESC = "navy and gold crest glyph icons with aqua Aero glow"
VARIANTS = (("Cartethyia-WuWa.mtz", True, color_icons_buf, COLOR_DESC, " - Color"),
            ("Cartethyia-WuWa-nofont.mtz", False, color_icons_buf, COLOR_DESC, " - Color, no font"))
if HAVE_GLYPHS:
    VARIANTS += (("Cartethyia-WuWa-glyph.mtz", True, icons_buf, GLYPH_DESC, " - Glyph"),)
for fname, with_font, icons, icon_desc, suffix in VARIANTS:
    with zipfile.ZipFile(f"{OUT}/{fname}", "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("description.xml", DESC.format(icons=icon_desc, font=", Marcellus system font" if with_font else "",
                                                  suffix=suffix))
        if with_font:
            z.write(FONT, "fonts/Roboto-Regular.ttf")
        z.writestr("wallpaper/default_wallpaper.jpg", jpg(home))
        z.writestr("wallpaper/default_lock_wallpaper.jpg", jpg(lock))
        z.writestr("icons", icons.getvalue())
        for n, im in previews.items():
            z.writestr(f"preview/{n}", jpg(im, 88))


# ---------------------------------------------------------------- sounds
def load(name):
    a, sr = sf.read(f"{AUD}/{name}", always_2d=True)
    a = a.mean(axis=1)
    nz = np.where(np.abs(a) > 0.01)[0]
    a = a[max(nz[0] - int(0.02 * sr), 0): nz[-1] + int(0.08 * sr)]
    f = int(0.01 * sr)
    a[:f] *= np.linspace(0, 1, f)
    a[-f:] *= np.linspace(1, 0, f)
    return a, sr


def build(parts, out_name):
    sr, chunks = 48000, []
    for part in parts:
        if isinstance(part, float):
            chunks.append(np.zeros(int(part * sr)))
        else:
            a, sr = load(part)
            chunks.append(a)
    a = np.concatenate(chunks)
    a = a / max(np.abs(a).max(), 1e-6) * 0.89  # peak -1 dBFS
    sf.write(f"{OUT}/sounds/{out_name}", a, sr, subtype="PCM_16")
    return len(a) / sr


for lang, pre in (("en", ""), ("ja", "JA_")):
    print("sound", lang, "ringtone", round(build([f"Cartethyia_{pre}Greeting.ogg", 1.5], f"cartethyia_ringtone_{lang}.wav"), 2), "s",
          "| notif", round(build([f"Cartethyia_{pre}Join_Team_II.ogg"], f"cartethyia_notification_{lang}.wav"), 2), "s",
          "| alarm", round(build([f"Cartethyia_{pre}Join_Team_I.ogg", 0.6, f"Cartethyia_{pre}Join_Team_III.ogg", 1.2],
                                  f"cartethyia_alarm_{lang}.wav"), 2), "s")

print("logo box removed:", logo)
print("icons:", len(pkgs))
for f in sorted(os.listdir(OUT)):
    p = f"{OUT}/{f}"
    print(f"{os.path.getsize(p) / 1e6:7.2f} MB  {f}" if os.path.isfile(p) else f"   dir     {f}/ ({len(os.listdir(p))} files)")
