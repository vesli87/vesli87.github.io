#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bild-Pipeline: MAHE-Produktbilder einmalig herunterladen, lokal optimieren
und ein Manifest mit Abmessungen schreiben.

Warum lokal statt Hotlink auf mahe-online.de?
  * Ladezeit & Core Web Vitals (LCP) – die Originale sind bis 4 MB gross
  * Bild-SEO: nur selbst gehostete Bilder können in der Bildersuche ranken
  * Ausfallsicherheit: die Seite funktioniert auch, wenn mahe-online.de blockt

Ausgabe:
  assets/img/p/<key>-400.webp    Karten
  assets/img/p/<key>-1000.webp   Detailseite
  assets/img/manifest.json       { pfad: {key, w, h} }

Kein PNG-Fallback im Repo: WebP wird von allen relevanten Browsern seit 2020
unterstützt (Safari 14+). Sollte ein Browser WebP trotzdem nicht dekodieren,
greift das onerror-Attribut im <img> und lädt das Original von mahe-online.de.
Ein 800-px-PNG-Fallback hätte das Repo um 18 MB aufgebläht (356 kB pro Bild
gegenüber 33 kB als WebP).

Aufruf:  python3 build/images.py [--force]
Benötigt: curl, sips (macOS), cwebp (brew install webp)
"""

import hashlib
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import core  # noqa: E402

CACHE = core.BUILD / "cache" / "img"
OUT = core.ROOT / "assets" / "img" / "p"
MANIFEST = core.ROOT / "assets" / "img" / "manifest.json"

# 1600 und 2000 nur, wenn die Vorlage so breit ist. Sie sind fuer die
# Lupe da: dort wird das Bild bildschirmfuellend gezeigt, und 1000 px
# reichen dafuer auf einem heutigen Monitor nicht.
WEBP_SIZES = [400, 1000, 1600, 2000]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 VES-TECH-Build/1.0"


def key_for(path):
    """'2022/03/Bild-der-Hypers.png' -> 'bild-der-hypers-1f2a3b'"""
    stem = pathlib.PurePosixPath(path).stem
    h = hashlib.md5(path.encode("utf-8")).hexdigest()[:6]
    return f"{core.slugify(stem)}-{h}"


def has(cmd):
    return subprocess.run(["which", cmd], capture_output=True).returncode == 0


def dims(f):
    r = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(f)],
                       capture_output=True, text=True)
    w = re.search(r"pixelWidth:\s*(\d+)", r.stdout)
    h = re.search(r"pixelHeight:\s*(\d+)", r.stdout)
    return (int(w.group(1)), int(h.group(1))) if w and h else (0, 0)


def download(path, dest):
    url = core.REMOTE_IMG + path
    r = subprocess.run(["curl", "-sSL", "--max-time", "60", "-A", UA, "-o", str(dest), url],
                       capture_output=True, text=True)
    return r.returncode == 0 and dest.exists() and dest.stat().st_size > 500


def collect_paths():
    """Alle eindeutigen Original-Bildpfade (Produkte + Frontpanels)."""
    s = {core.full_img(p["img"]) for p in core.P}
    s |= {core.full_img(f["img"]) for f in core.FP.values() if f.get("img")}
    # Geraeteausfuehrungen bringen eigene Bilder mit (data/HL_VAR.json)
    s |= {core.full_img(v["img"]) for lst in core.HL_VAR.values()
          if isinstance(lst, list) for v in lst if v.get("img")}
    # Zusatzbilder der Galerie: sie haengen an keinem Produktfeld, wuerden also
    # bei --force aus dem Manifest fallen und live fehlen.
    s |= {core.full_img(g["img"]) for lst in core.GALLERY.values()
          if isinstance(lst, list) for g in lst if g.get("img")}
    return sorted(s)


def main():
    force = "--force" in sys.argv
    if not has("cwebp"):
        print("!! cwebp fehlt  ->  brew install webp   (WebP wird übersprungen)")
    CACHE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    manifest = {}
    if MANIFEST.exists():
        try:
            manifest = json.loads(MANIFEST.read_text("utf-8"))
        except Exception:
            manifest = {}
    if force:
        # --force baut die Produktbilder neu auf. Die Frontpanels stehen im
        # selben Manifest, kommen aber nicht aus dem Netz, sondern von
        # build/panels.py - sie liessen sich hier gar nicht wiederherstellen.
        # Wurden sie frueher mitgeloescht, suchte die Seite sie anschliessend
        # unter einer mahe-online.de-Adresse, die es nicht gibt: 32 kaputte
        # Panelbilder auf der Live-Seite. Deshalb bleiben lokale Eintraege
        # stehen, auch bei --force.
        manifest = {k: v for k, v in manifest.items() if v.get("local")}

    paths = collect_paths()
    print(f"{len(paths)} Bilder")
    ok = fail = skip = 0

    for i, path in enumerate(paths, 1):
        k = key_for(path)
        src = CACHE / f"{k}{pathlib.PurePosixPath(path).suffix or '.png'}"
        # "fertig" ist ein Bild erst, wenn genau die Stufen dastehen, die zu
        # seiner Breite passen - sonst blieben Bilder nach dem Erweitern der
        # Stufenliste auf den alten zwei Groessen stehen.
        vor = manifest.get(path) or {}
        wv = vor.get("w") or 0
        soll = []
        for nenn in WEBP_SIZES:
            ziel = min(nenn, wv)
            if ziel and ziel not in soll:
                soll.append(ziel)
        done = (vor.get("sizes") == soll
                and all((OUT / f"{k}-{x}.webp").exists() for x in soll))
        if done and path in manifest and not force:
            skip += 1
            continue

        if not src.exists() or force:
            if not download(path, src):
                print(f"  [{i:2}/{len(paths)}] FEHLER Download: {path}")
                fail += 1
                continue

        # Weissen Rand wegschneiden. Viele Herstellerfotos zeigen die Maschine
        # klein in einer grossen weissen Flaeche - auf der Seite wirkt sie dann
        # winzig, obwohl die Datei gross ist. Beim EcoMIG 3000 waren von
        # 3008x2000 nur 1313x1413 Bild.
        trimmer = core.BUILD / "trim"
        if trimmer.exists():
            geschnitten = CACHE / f"{k}-trim.png"
            r = subprocess.run([str(trimmer), str(src), str(geschnitten)],
                               capture_output=True, text=True)
            if r.returncode == 0 and geschnitten.exists():
                src = geschnitten

        w, h = dims(src)
        if not w:
            print(f"  [{i:2}/{len(paths)}] FEHLER unlesbar: {path}")
            fail += 1
            continue

        # WebP in zwei Grössen – niemals hochskalieren
        # Dateiname = tatsaechliche Breite. Ist die Vorlage 862 px breit, gibt es
        # 400 und 862 - nicht nur 400, wie es eine Liste "alle Stufen <= Breite"
        # ergaebe. Genau daran waren 21 Bilder auf 400 px stehengeblieben.
        stufen = []
        for nenn in WEBP_SIZES:
            ziel = min(nenn, w)
            if ziel not in stufen:
                stufen.append(ziel)
        # Qualitaet nach Groesse der Vorlage. Bei einem 242 px breiten
        # Herstellerfoto ist jeder Bildpunkt kostbar - und die Datei ist mit
        # 3 kB ohnehin winzig, ein paar Kilobyte mehr fallen nicht auf. Bei
        # einer 3000 px breiten Vorlage waere dieselbe Qualitaet reine
        # Verschwendung: dort traegt die Aufloesung die Schaerfe.
        #
        # Gemessen am 05.08.2026: 16 der 86 Bilder auf der Website reichen nur
        # fuer einen 1x-Bildschirm, weil MAHE keine groesseren Vorlagen hat.
        # Aus denen wird mit dieser Staffel wenigstens das Letzte herausgeholt.
        def guete(breite):
            # Nur bei wirklich kleinen Vorlagen lohnt die hoehere Guete: dort
            # traegt jeder Bildpunkt, und die Datei bleibt trotzdem winzig.
            # Bei 800 px war der Unterschied zwischen 82 und 88 kaum zu sehen,
            # kostete aber 18 kB pro Datei - gemessen am 05.08.2026.
            return "92" if breite < 600 else "82"

        if has("cwebp"):
            q = guete(w)
            for size in stufen:
                dst = OUT / f"{k}-{size}.webp"
                subprocess.run(["cwebp", "-quiet", "-q", q, "-alpha_q", "90",
                                "-sharp_yuv", "-resize", str(size), "0",
                                str(src), "-o", str(dst)],
                               capture_output=True)

        # Abmessungen der ausgelieferten Grössen (für width/height gegen CLS)
        manifest[path] = {
            "key": k,
            "w": w, "h": h,
            "ratio": round(h / w, 4) if w else 1.0,
            "sizes": stufen,
        }
        ok += 1
        print(f"  [{i:2}/{len(paths)}] {path}  {w}×{h}  -> {k}")

    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), "utf-8")
    total = sum(f.stat().st_size for f in OUT.glob("*") if f.is_file())
    print(f"\nfertig: {ok} neu, {skip} übersprungen, {fail} Fehler")
    print(f"assets/img/p: {len(list(OUT.glob('*')))} Dateien, {total/1024/1024:.1f} MB")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
