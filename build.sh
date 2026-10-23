#!/usr/bin/env bash
# One-shot build: fetch assets -> theme (.mtz, wallpapers, sounds) -> AOD images -> widget APK.
# Output goes to ./out (never committed). Usage: ./build.sh
set -euo pipefail
cd "$(dirname "$0")"
PY=${PYTHON:-python}

"$PY" fetch_assets.py assets
"$PY" cartethyia-theme/build_theme.py assets out/theme
"$PY" cartethyia-theme/make_aod.py assets/art_orig out/theme/wallpapers

mkdir -p cartethyia-widget/res/drawable-nodpi cartethyia-widget/res/font
cp assets/font_dl/Marcellus-Regular.ttf cartethyia-widget/res/font/marcellus.ttf
"$PY" cartethyia-widget/make_art.py assets/art_orig assets/font_dl/Marcellus-Regular.ttf cartethyia-widget/res
bash cartethyia-widget/build.sh
cp cartethyia-widget/cartethyia-widget.apk out/
echo "all outputs in $(pwd)/out"
