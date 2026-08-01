#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Technische Daten von mahe-online.de holen.

    python3 build/scrape_specs.py

Die Tabellen stehen nicht im HTML (Ninja Tables, siehe scrape_mahe.py). Im
Markup liegt nur `data-footable_id`; die Daten kommen per AJAX als JSON.

Ergebnis: build/mahe_specs.json

    { "hypertig-ax": {
        "table_id": "12146",
        "columns": ["240", "300", "350"],      # Modellvarianten
        "rows": [ {"model": "Netzabsicherung", "240": "16A", "300": "20A", …}, … ] } }

Die Spaltennamen kommen direkt von MAHE. Welche Seite zu welchem Produkt
gehört, entscheidet die Zuordnung beim Übernehmen — nicht dieses Skript.
"""

import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import core as C  # noqa: E402

CACHE = C.BUILD / "cache" / "mahe"
OUT = C.BUILD / "mahe_specs.json"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
AJAX = ("https://mahe-online.de/wp-admin/admin-ajax.php"
        "?action=wp_ajax_ninja_tables_public_action"
        "&table_id={}&target_action=get-all-data")


def fetch(url):
    return subprocess.run(["curl", "-sSL", "--max-time", "40", "-A", UA, url],
                          capture_output=True, text=True).stdout


def main():
    if not CACHE.is_dir():
        print("Kein Cache – zuerst build/scrape_mahe.py laufen lassen.")
        sys.exit(1)

    out, leer = {}, []
    files = sorted(CACHE.glob("*.html"))
    print(f"{len(files)} Seiten\n")

    for f in files:
        slug = f.stem
        html = f.read_text("utf-8", errors="replace")
        ids = re.findall(r'data-footable_id="(\d+)"', html)
        if not ids:
            leer.append(slug)
            continue
        for tid in dict.fromkeys(ids):
            try:
                data = json.loads(fetch(AJAX.format(tid)))
            except json.JSONDecodeError:
                print(f"  {slug}: Tabelle {tid} lieferte kein JSON")
                continue
            rows = [r["value"] for r in data if isinstance(r, dict) and "value" in r]
            if not rows:
                continue
            cols = []
            for r in rows:
                for k in r:
                    if k not in ("model", "___id___") and k not in cols:
                        cols.append(k)
            key = slug if len(ids) == 1 else f"{slug}#{tid}"
            out[key] = {"table_id": tid, "columns": cols,
                        "rows": [{k: v for k, v in r.items() if k != "___id___"}
                                 for r in rows]}
            print(f"  {key:26} {len(rows):>2} Zeilen × {len(cols)} Varianten: {', '.join(cols)}")

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf-8")
    print(f"\n{len(out)} Tabellen -> {OUT.relative_to(C.ROOT)}")
    if leer:
        print(f"ohne Tabelle: {', '.join(leer)}")


if __name__ == "__main__":
    main()
