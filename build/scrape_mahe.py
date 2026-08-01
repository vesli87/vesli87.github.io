#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Besonderheiten von mahe-online.de holen und mit unseren Daten vergleichen.

    python3 build/scrape_mahe.py            # holen + vergleichen
    python3 build/scrape_mahe.py --report   # nur vergleichen (Cache nutzen)

Hintergrund: Unsere HL-Texte sind nach Gerätefamilie gruppiert (alle WIG AC/DC
teilen sich eine Liste). MAHE führt sie je Gerät und Variante — die Omega AX pro
hat zehn Punkte, die Omega AX syn fünf, und beide unterscheiden sich deutlich
von unserem Familientext.

Das Skript legt build/cache/mahe/<slug>.html ab und schreibt die extrahierten
Listen nach build/mahe_besonderheiten.json. Übernommen wird nichts automatisch:
die Zuordnung Gerät → Liste passiert von Hand, damit kein Text am falschen
Produkt landet.

Technische Daten (noch offen)
-----------------------------
Die Spezifikationstabellen stehen NICHT im HTML. MAHE nutzt das Plugin
Ninja Tables; im Markup liegt nur das <table>-Geruest mit
data-footable_id="<id>", die Daten kommen per AJAX nach:

    https://mahe-online.de/wp-admin/admin-ajax.php
        ?action=wp_ajax_ninja_tables_public_action
        &table_id=<id>&target_action=get-all-data

Antwort ist JSON, eine Zeile je Merkmal, mit einer Spalte je Modellvariante:

    {"value": {"model": "Netzabsicherung", "240": "16A", "300": "20A", "350": "20A"}}

Uebernehmen laesst sich das erst, wenn `specs` in data/P.json von einem flachen
Schluessel-Wert-Paar auf eine Tabelle mit Variantenspalten umgestellt ist. Das
betrifft spec_html, das JSON-LD (additionalProperty), den Suchindex,
products.json und llms-full.txt.
"""

import json
import pathlib
import re
import subprocess
import sys
import html as htmlmod

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import core as C  # noqa: E402

CACHE = C.BUILD / "cache" / "mahe"
OUT = C.BUILD / "mahe_besonderheiten.json"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

SITEMAP = "https://mahe-online.de/wp-sitemap-posts-page-1.xml"

# Seiten ohne Geräte – die brauchen wir nicht
SKIP = ("about-us", "kontakt", "faq", "company-history", "impressum", "datenschutz",
        "agb", "partner", "login", "gutschein", "en-1090", "service-produkte",
        "verfahren", "downloads", "karriere", "jobs")


def fetch(url, dest=None):
    cmd = ["curl", "-sSL", "--max-time", "40", "-A", UA, url]
    if dest:
        cmd += ["-o", str(dest)]
        return subprocess.run(cmd, capture_output=True).returncode == 0
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def strip(s):
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", htmlmod.unescape(s)).strip()


def extract(html):
    """[(Gerätename, [Besonderheiten…])] – der Name ist die letzte Überschrift
    vor dem Besonderheiten-Block."""
    out = []
    for m in re.finditer(r"Besonderheiten", html):
        before = html[:m.start()]
        heads = re.findall(r"<h[1-4][^>]*>(.*?)</h[1-4]>", before, re.S)
        name = strip(heads[-1]) if heads else ""
        after = html[m.end():m.end() + 6000]
        ul = re.search(r"<ul[^>]*>(.*?)</ul>", after, re.S)
        if not ul:
            continue
        items = [strip(li) for li in re.findall(r"<li[^>]*>(.*?)</li>", ul.group(1), re.S)]
        items = [i for i in items if i and len(i) > 3]
        if name and items:
            out.append((name, items))
    return out


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    report_only = "--report" in sys.argv

    urls = [u for u in re.findall(r"<loc>([^<]+)</loc>", fetch(SITEMAP))
            if not any(s in u for s in SKIP)]
    print(f"{len(urls)} Seiten\n")

    found = {}
    for u in urls:
        slug = u.rstrip("/").split("/")[-1] or "home"
        f = CACHE / f"{slug}.html"
        if not f.exists() and not report_only:
            fetch(u, f)
        if not f.exists():
            continue
        for name, items in extract(f.read_text("utf-8", errors="replace")):
            found.setdefault(f"{slug} :: {name}", {"url": u, "items": items})

    OUT.write_text(json.dumps(found, ensure_ascii=False, indent=1), "utf-8")
    print(f"{len(found)} Geräte mit Besonderheiten -> {OUT.relative_to(C.ROOT)}\n")

    # Gegenüberstellung: was zeigen wir heute?
    print(f"{'MAHE (Gerät)':38} {'Punkte':>6}   unsere Familie / Punkte")
    print("-" * 82)
    for name, d in sorted(found.items()):
        ours = ""
        for p in C.P:
            if p["name"].lower().replace(" ", "") in name.lower().replace(" ", "") or \
               name.lower().replace(" ", "") in p["name"].lower().replace(" ", ""):
                hl = C.highlightsOf("de", p)
                ours = f"{p['id']} / {len(hl) if hl else 0}"
                break
        print(f"{name[:38]:38} {len(d['items']):>6}   {ours or '— kein Treffer'}")


if __name__ == "__main__":
    main()
