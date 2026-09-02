#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Favicon- und App-Icon-Erzeugung.

Motiv: das Monogramm VT in Weiss auf dem Orange der Marke (#E0511A).

Vorher stand hier das Schweizer Kreuz aus dem Logo - oranges Feld, weisser
Balken quer und längs. In den Google-Ergebnissen sah das aus wie eine
allgemeine Schweizer Marke und nicht wie diese Firma; genau das hat der
Inhaber am 14.08.2026 beanstandet. Das Kreuz bleibt im Logo im Kopf der Seite,
wo daneben "VES-TECH" steht und es sich von selbst erklärt.

Warum VT und nicht der ganze Schriftzug: Google zeigt das Zeichen rund 16 bis
20 px gross. "VES-TECH" wäre dort ein Fleck. Zwei schwere, schmale Buchstaben
bleiben lesbar - dasselbe Prinzip wie bei VW oder HP.

Die Buchstaben sind als Polygone gezeichnet, nicht gesetzt: Anton liegt nur
als woff2 vor, und fontTools kann das ohne die Brotli-Erweiterung nicht
öffnen. Die Formen folgen den Merkmalen von Anton - sehr fett, schmal, flache
Abschlüsse, kaum Strichkontrast.

PNG und ICO werden ohne externe Bibliothek geschrieben (zlib + struct
genügen), damit der Build auf jedem Rechner ohne Pillow läuft.
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


def _png_bytes(w, h, rgb_at):
    """rgb_at(x, y) -> (r, g, b). Liefert ein 8-Bit-RGB-PNG als Bytes."""
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
    return png


def write_png(path, w, h, rgb_at):
    png = _png_bytes(w, h, rgb_at)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)
    return len(png)


# Das Monogramm auf einem 32er-Raster, wie es auch das SVG benutzt.
# V: zwei schwere Schenkel, unten flach abgeschnitten - Antons Eigenart.
# T: Querbalken und Stamm gleich dick.
V_POLY = [(4.4, 8.0), (7.8, 8.0), (9.9, 19.2), (12.0, 8.0), (15.4, 8.0),
          (11.2, 24.0), (8.6, 24.0)]
T_POLY = [(16.6, 8.0), (27.6, 8.0), (27.6, 11.6), (24.0, 11.6), (24.0, 24.0),
          (20.2, 24.0), (20.2, 11.6), (16.6, 11.6)]


def _im_polygon(px, py, poly):
    """Punkt in Polygon, Ungerade-Regel."""
    drin = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > py) != (y2 > py):
            if px < x1 + (py - y1) * (x2 - x1) / (y2 - y1):
                drin = not drin
    return drin


def monogram_icon(size, ss=4):
    """Pixelfunktion: weisses VT auf orangem Feld.

    ss ist die Ueberabtastung je Achse. Ohne sie haetten die Diagonalen des V
    bei 16 px eine Treppe; mit 4x4 Proben je Pixel sind die Kanten weich und
    das Zeichen bleibt auch klein lesbar.
    """
    k = size / 32.0
    polys = [[(x * k, y * k) for x, y in V_POLY],
             [(x * k, y * k) for x, y in T_POLY]]

    def at(x, y):
        treffer = 0
        for sy in range(ss):
            py = y + (sy + 0.5) / ss
            for sx in range(ss):
                px = x + (sx + 0.5) / ss
                if any(_im_polygon(px, py, pl) for pl in polys):
                    treffer += 1
        if treffer == 0:
            return ORANGE
        if treffer == ss * ss:
            return WHITE
        a = treffer / float(ss * ss)
        return tuple(int(round(o + (w - o) * a)) for o, w in zip(ORANGE, WHITE))
    return at


def write_ico(path, groessen=(16, 32, 48)):
    """Klassische favicon.ico mit mehreren Groessen, PNG-komprimiert.

    Warum ueberhaupt: /favicon.ico ist der Pfad, den Browser und Crawler von
    sich aus anfragen, wenn sie nichts anderes finden - und Google nennt ihn
    ausdruecklich als Rueckfall. Am 14.08.2026 antwortete er mit 404; es gab
    nur eine favicon.png im Wurzelverzeichnis, die niemand anfragt.
    PNG in einer ICO-Huelle verstehen alle heutigen Clients.
    """
    bilder = []
    for s in groessen:
        roh = _png_bytes(s, s, monogram_icon(s))
        bilder.append((s, roh))
    kopf = struct.pack("<HHH", 0, 1, len(bilder))
    versatz = 6 + 16 * len(bilder)
    eintraege, daten = b"", b""
    for s, roh in bilder:
        eintraege += struct.pack("<BBBBHHII", s if s < 256 else 0, s if s < 256 else 0,
                                 0, 0, 1, 32, len(roh), versatz)
        daten += roh
        versatz += len(roh)
    path.write_bytes(kopf + eintraege + daten)
    return len(kopf + eintraege + daten)


def _pfad(poly):
    return "M" + " ".join(f"{x:g},{y:g}" for x, y in poly) + "Z"


FAVICON_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" role="img" aria-label="VES-TECH Swiss">
  <rect width="32" height="32" rx="5" fill="#E0511A"/>
  <path d="{_pfad(V_POLY)}" fill="#fff"/>
  <path d="{_pfad(T_POLY)}" fill="#fff"/>
</svg>
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "favicon.svg").write_text(FAVICON_SVG, "utf-8")
    made = ["favicon.svg"]
    # 96 und 192 sind Vielfache von 48 - genau das verlangt Google fuer das
    # Zeichen in den Suchergebnissen. Die ICO deckt 48 ab; mit einer groesseren
    # PNG-Fassung hat der Abholer die beste Vorlage zur Auswahl.
    for name, size in [("icon-96.png", 96), ("icon-192.png", 192), ("icon-512.png", 512),
                       ("apple-touch-icon.png", 180), ("logo.png", 512),
                       ("og-fallback.png", 512)]:
        write_png(OUT / name, size, size, monogram_icon(size))
        made.append(name)
    # Der Pfad, den Browser und Crawler von sich aus anfragen. Er antwortete
    # bis zum 14.08.2026 mit 404 - es gab nur eine favicon.png, die niemand
    # anfragt. Drei Groessen in einer Huelle: 16 fuer die Registerkarte,
    # 32 fuer die Lesezeichen, 48 weil Google diese Kantenlaenge empfiehlt.
    write_ico(C.ROOT / "favicon.ico")
    made.append("../favicon.ico")
    write_png(C.ROOT / "favicon.png", 48, 48, monogram_icon(48))
    made.append("../favicon.png")
    print("Icons:", ", ".join(made))


if __name__ == "__main__":
    main()
