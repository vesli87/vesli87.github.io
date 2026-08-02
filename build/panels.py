#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frontpanel-Fotos des Herstellers importieren.

    python3 build/panels.py ~/Downloads/OneDrive_1_1.8.2026

Anders als build/images.py holt dieses Skript nichts aus dem Netz, sondern
übernimmt Dateien, die MAHE direkt geliefert hat. Die Originale liegen mit bis
zu 6377 px Breite vor; ausgeliefert werden 400 px und 1000 px als WebP.

Die Einträge landen im selben assets/img/manifest.json wie die Produktbilder,
mit dem Schlüssel `panels/<Dateiname>` und dem Vermerk `"local": true` — daran
erkennt render.img_tag, dass es keinen Rückfall auf mahe-online.de gibt.
"""

import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import core as C  # noqa: E402

OUT = C.ROOT / "assets" / "img" / "panels"
MANIFEST = C.ROOT / "assets" / "img" / "manifest.json"
# 1600 und 2000 nur, wenn die Vorlage wirklich so breit ist - hochskalieren
# macht Bilder nicht schaerfer, nur groesser. Welche Stufen entstanden sind,
# steht danach im Manifest, damit render.img_tag kein Bild ins srcset
# schreibt, das es nicht gibt.
SIZES = [400, 1000, 1600, 2000]


def dims(f):
    r = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(f)],
                       capture_output=True, text=True)
    w = re.search(r"pixelWidth:\s*(\d+)", r.stdout)
    h = re.search(r"pixelHeight:\s*(\d+)", r.stdout)
    return (int(w.group(1)), int(h.group(1))) if w and h else (0, 0)


def key_for(name):
    return C.slugify(pathlib.PurePosixPath(name).stem)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = pathlib.Path(sys.argv[1]).expanduser()
    if not src.is_dir():
        print(f"Ordner nicht gefunden: {src}")
        sys.exit(1)

    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text("utf-8")) if MANIFEST.exists() else {}

    files = sorted(f for f in src.iterdir()
                   if f.suffix.lower() in (".png", ".jpg", ".jpeg"))
    print(f"{len(files)} Dateien in {src.name}\n")

    for f in files:
        k = key_for(f.name)
        w, h = dims(f)
        if not w:
            print(f"  unlesbar: {f.name}")
            continue
        stufen = [s for s in SIZES if s <= w] or [SIZES[0]]
        for s in stufen:
            dst = OUT / f"{k}-{s}.webp"
            subprocess.run(["cwebp", "-quiet", "-q", "86", "-alpha_q", "90",
                            "-sharp_yuv", "-resize", str(min(s, w)), "0",
                            str(f), "-o", str(dst)],
                           capture_output=True)
        manifest[f"panels/{f.name}"] = {"key": k, "w": w, "h": h,
                                        "ratio": round(h / w, 4), "local": True,
                                        "sizes": stufen}
        print(f"  {f.name:44} {w}×{h}  ->  {k}")

    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), "utf-8")
    total = sum(x.stat().st_size for x in OUT.glob("*.webp"))
    print(f"\nassets/img/panels: {len(list(OUT.glob('*.webp')))} Dateien, "
          f"{total/1024/1024:.1f} MB")


if __name__ == "__main__":
    main()
