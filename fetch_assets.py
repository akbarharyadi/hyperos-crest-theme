"""Download the third-party assets the build needs into ./assets (never committed).

Usage: python fetch_assets.py [assets_dir]

- Official Wuthering Waves art and Cartethyia voice lines, (c) Kuro Games, fetched from the
  Wuthering Waves Fandom wiki for personal, non-commercial use only.
- Marcellus font (SIL Open Font License 1.1) from the google/fonts repository.
Only the Python standard library is used.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
WIKI_API = "https://wutheringwaves.fandom.com/api.php"
UA = {"User-Agent": "cartethyia-hyperos-theme/1.0 (fan project; personal use)"}

ART = ["Cartethyia_2025-06-24.jpg", "Cartethyia_2025-06-18.jpg", "Cartethyia_2025-06-19.jpg",
       "Cartethyia_2025-03-24.jpg", "Fleurdelys_2025-03-26.jpg", "Cartethyia_Full_Sprite.png",
       "Cartethyia_Splash_Art.png", "Cartethyia_Convene_Still.png"]
VOICE = [f"Cartethyia_{lang}{line}.ogg" for lang in ("", "JA_")
         for line in ("Greeting", "Join_Team_I", "Join_Team_II", "Join_Team_III")]
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/marcellus/Marcellus-Regular.ttf"
FONT_LICENSE_URL = "https://github.com/google/fonts/raw/main/ofl/marcellus/OFL.txt"


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def wiki_urls(files):
    query = urllib.parse.urlencode({"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url",
                                    "titles": "|".join(f"File:{f}" for f in files)})
    pages = json.loads(get(f"{WIKI_API}?{query}"))["query"]["pages"].values()
    return {p["title"][5:].replace(" ", "_"): p["imageinfo"][0]["url"] for p in pages if "imageinfo" in p}


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    print(f"  {len(data) / 1e6:6.2f} MB  {os.path.relpath(path, OUT)}")


def fetch(files, folder, original=False):
    urls = wiki_urls(files)
    for name in files:
        dest = os.path.join(OUT, folder, name)
        if os.path.exists(dest):
            continue
        if name not in urls:
            sys.exit(f"missing on wiki: {name}")
        url = urls[name]
        if original:   # the wiki serves WebP by default; ask for the uploaded file
            url += ("&" if "?" in url else "?") + "format=original"
        save(dest, get(url))


print(f"assets -> {OUT}")
fetch(ART, "art_orig", original=True)
fetch(VOICE, "audio_dl")
for url, name in ((FONT_URL, "Marcellus-Regular.ttf"), (FONT_LICENSE_URL, "OFL.txt")):
    dest = os.path.join(OUT, "font_dl", name)
    if not os.path.exists(dest):
        save(dest, get(url))
print("done")
