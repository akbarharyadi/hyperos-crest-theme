#!/usr/bin/env bash
# Build cartethyia-widget.apk without Gradle: aapt2 -> javac -> d8 -> zipalign -> apksigner.
# Usage: ./build.sh   (needs Android SDK build-tools 36 + platform android-36, JDK 17)
set -euo pipefail
cd "$(dirname "$0")"

SDK=${ANDROID_HOME:-/c/Android/android-sdk}
BT=$SDK/build-tools/36.0.0
JAR=$SDK/platforms/android-36/android.jar
OUT=build
rm -rf "$OUT" && mkdir -p "$OUT/gen" "$OUT/classes" "$OUT/dex"

"$BT/aapt2.exe" compile --dir res -o "$OUT/res.zip"
"$BT/aapt2.exe" link -I "$JAR" --manifest AndroidManifest.xml --java "$OUT/gen" \
    -o "$OUT/unsigned.apk" "$OUT/res.zip"

javac -source 11 -target 11 -nowarn -classpath "$JAR" -d "$OUT/classes" \
    $(find src "$OUT/gen" -name '*.java')
"$BT/d8.bat" --release --lib "$JAR" --min-api 26 --output "$OUT/dex" $(find "$OUT/classes" -name '*.class')
python -I -c "import sys, zipfile; zipfile.ZipFile(sys.argv[1], 'a', zipfile.ZIP_DEFLATED).write(sys.argv[2], 'classes.dex')" \
    "$OUT/unsigned.apk" "$OUT/dex/classes.dex"

"$BT/zipalign.exe" -f -p 4 "$OUT/unsigned.apk" "$OUT/aligned.apk"
KS=$OUT/../debug.keystore
[ -f "$KS" ] || keytool -genkeypair -keystore "$KS" -storepass android -keypass android -alias debug \
    -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Cartethyia Widget" >/dev/null
"$BT/apksigner.bat" sign --ks "$KS" --ks-pass pass:android --key-pass pass:android \
    --out cartethyia-widget.apk "$OUT/aligned.apk"
echo "built $(pwd)/cartethyia-widget.apk"
