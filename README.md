# Cartethyia // Wuthering Waves — HyperOS theme & clock widget

A fan-made makeover for Xiaomi phones on **HyperOS 3** (built and tested on a Xiaomi 15T Pro),
themed on Cartethyia / Fleurdelys from *Wuthering Waves*:

- **HyperOS theme (`.mtz`)** — home and lock wallpapers, Marcellus system font, and icon frames that
  keep every app's **original colourful icon** inside a navy plate with a gold crest border.
- **Cartethyia Clock widget** — a 4×2 home-screen widget (live time and date in Marcellus over
  Fleurdelys art, gold chamfered frame); tapping it opens the game.
- **Always-on-display images** — square portraits sized for HyperOS's "custom image" AOD style.
- **Sounds** — ringtone, notification and alarm cut from Cartethyia's voice lines (EN and JA).

> **Fan project, not affiliated with or endorsed by Kuro Games.** This repository contains **no**
> Kuro Games content. `fetch_assets.py` downloads the official art and voice lines from the
> Wuthering Waves wiki onto *your* machine at build time, for personal, non-commercial use.
> Kuro's [derivative works guidelines](https://wutheringwaves.kurogames.com/p/en/produce.html)
> exclude software and commercial works, so **don't sell or redistribute the built files**.

## Build

Requirements: Python 3.10+, JDK 17, Android SDK build-tools 36 + platform `android-36`
(`ANDROID_HOME`, defaults to `/c/Android/android-sdk`), and bash (Git Bash on Windows).

```bash
pip install -r requirements.txt
./build.sh            # fetch assets -> out/theme/*.mtz, wallpapers, sounds -> out/cartethyia-widget.apk
```

| Output | What it is |
|---|---|
| `out/theme/Cartethyia-WuWa.mtz` | colour icons + wallpapers + Marcellus font |
| `out/theme/Cartethyia-WuWa-nofont.mtz` | same, keeps the system font |
| `out/theme/wallpapers/` | 1280×2772 wallpapers, `09/10_aod_*` square AOD images |
| `out/theme/sounds/` | `cartethyia_{ringtone,notification,alarm}_{en,ja}.wav` |
| `out/cartethyia-widget.apk` | the clock widget (debug-signed) |

## Install on the phone

**Theme.** Stock Themes **3.0.6.x and newer refuse third-party `.mtz` files**. What worked:
[HyperOS MTZ Studio](https://github.com/GloriousApps/HyperOS-MTZ-Studio) with
[Shizuku](https://github.com/RikkaApps/Shizuku) running, and the Themes app at **3.0.5.6-global**
(MTZ Studio provides a checksum- and signature-verified copy; Android only accepts it if it is
Xiaomi-signed). Then: MTZ Studio → Import MTZ → Library → *Terapkan/Apply* → pick the file.
Give every theme a unique title — MTZ Studio's library crashes on duplicates.

**Widget.**

```bash
adb install out/cartethyia-widget.apk
adb shell appops set dev.wuwafan.cartethyia 10017 allow     # HyperOS "home screen shortcuts" permission
adb shell am start -n dev.wuwafan.cartethyia/.PinActivity   # asks the launcher to place it
```

or long-press the home screen → Widgets → *Cartethyia Clock*.

**Sounds.** Copy the `.wav` files to `Ringtones/`, `Notifications/` and `Alarms/` on the phone and pick
them in Settings → Sound & vibration.

**Lock-screen depth effect.** Settings → Personalisasi → tap the lock-screen preview → Wallpaper →
pick `02_lock_cartethyia_book.jpg` from the gallery; *Kedalaman* (depth) switches on once HyperOS has
cut out the subject, putting her crown in front of the clock.

**AOD.** Settings → Personalisasi → Always-on display → *Gambar kustom* → `10_aod_cartethyia_crest.png`.
The AOD frame is square, so full-screen images look tiny.

## How the colour icons work

Found by decompiling `miui.content.res.IconCustomizer` (`miui-framework.jar`):

- With `SupportLayerIcon=true` HyperOS uses per-app layered drawings from the theme; with it
  **`false`** and no per-app files it composes each app's *own* icon with the theme's frame images.
- `ConfigIconMask` must **not** touch the point (50,0) of its 100×100 box, otherwise the mask counts
  as a "full mask" and the frame images are ignored (`transform_config.xml` uses an inset octagon).
- Composition order: icon → cut by `icon_mask.png` → `icon_background.png` (tinted by the icon's
  average colour, so it is not used) → `icon_pattern.png` (drawn as-is: the navy plate) → icon →
  `icon_border.png` (gold frame). All are rescaled to `customizer_icon_size` (67dp).

## Credits

- Wuthering Waves, Cartethyia, artwork and voice lines © Kuro Games — fetched from the
  [Wuthering Waves Wiki](https://wutheringwaves.fandom.com/wiki/Cartethyia), not included here.
- [Marcellus](https://fonts.google.com/specimen/Marcellus) by Astigmatic — SIL Open Font License 1.1.

## License

Code and original frame designs: [MIT](LICENSE). Third-party assets keep their own terms.
