#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Favicon- und App-Icon-Erzeugung.

Motiv wie das Logo im Header: oranges Quadrat (#E0511A) mit weissem Kreuz –
die Proportionen stammen aus .logo .flag in site.css.

PNG wird ohne externe Bibliothek geschrieben (zlib + struct genügen), damit der
Build auf jedem Rechner ohne Pillow läuft.
"""

import pathlib
import struct
import sys
import zlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import core as C  # noqa: E402

OUT = C.ROOT / "assets" / "icons"
ORANGE = (224, 81, 26)     # #E0511A
WHITE = (255, 255, 255)
INK = (20, 20, 22)


def write_png(path, w, h, rgb_at):
    """rgb_at(x, y) -> (r, g, b). Schreibt ein 8-Bit-RGB-PNG."""
    raw = bytearray()
    for y in range(h):
        raw.append(0)                       # Filter: None
        for x in range(w):
            raw += bytes(rgb_at(x, y))
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", comp)
           + chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)
    return len(png)


def cross_icon(size, pad=0.0):
    """Erzeugt die Pixelfunktion: oranges Feld, weisses Kreuz."""
    inner = size * (1 - 2 * pad)
    off = size * pad
    arm = inner * (13 / 28.0)      # Armlänge wie im CSS-Logo
    thick = inner * (4 / 28.0)
    cx = cy = size / 2.0
    hx1, hx2 = cx - arm / 2, cx + arm / 2      # horizontaler Balken
    hy1, hy2 = cy - thick / 2, cy + thick / 2
    vx1, vx2 = cx - thick / 2, cx + thick / 2  # vertikaler Balken
    vy1, vy2 = cy - arm / 2, cy + arm / 2

    def at(x, y):
        if x < off or y < off or x >= off + inner or y >= off + inner:
            return WHITE
        if (hx1 <= x < hx2 and hy1 <= y < hy2) or (vx1 <= x < vx2 and vy1 <= y < vy2):
            return WHITE
        return ORANGE
    return at


FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" role="img" aria-label="VES-TECH Swiss">
  <rect width="32" height="32" rx="5" fill="#E0511A"/>
  <rect x="8.6" y="13.7" width="14.8" height="4.6" rx="1" fill="#fff"/>
  <rect x="13.7" y="8.6" width="4.6" height="14.8" rx="1" fill="#fff"/>
</svg>
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "favicon.svg").write_text(FAVICON_SVG, "utf-8")
    made = ["favicon.svg"]
    for name, size in [("icon-192.png", 192), ("icon-512.png", 512),
                       ("apple-touch-icon.png", 180), ("logo.png", 512),
                       ("og-fallback.png", 512)]:
        write_png(OUT / name, size, size, cross_icon(size))
        made.append(name)
    # klassisches favicon.ico-Ersatzformat für alte Clients
    write_png(C.ROOT / "favicon.png", 48, 48, cross_icon(48))
    made.append("../favicon.png")
    print("Icons:", ", ".join(made))


if __name__ == "__main__":
    main()
