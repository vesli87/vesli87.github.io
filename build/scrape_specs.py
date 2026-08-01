#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Technische Daten von mahe-online.de holen.

    python3 build/scrape_specs.py

Die Tabellen stehen nicht im HTML. MAHE nutzt Ninja Tables; im Markup liegt nur
das leere <table> mit `data-footable_id`. Zwei Quellen ergeben zusammen die
Tabelle, die der Besucher sieht:

1. Die Spalten stecken in einem <script src="data:text/javascript;base64,…">
   als `window['ninja_table_instance_N'] = { … "columns": [ … ] }`.
   Wichtig: der Spaltenschluessel ist nicht die Spaltenueberschrift. Bei der
   HyperTIG AX heisst die erste Variantenspalte intern "240", angezeigt wird
   aber "250" — wer nur die AJAX-Daten nimmt, schreibt die falsche Modellnummer
   an die Spalte.
2. Die Zeilen kommen per AJAX als JSON:

       https://mahe-online.de/wp-admin/admin-ajax.php
           ?action=wp_ajax_ninja_tables_public_action
           &table_id=<id>&target_action=get-all-data

   Antwort: {"value": {"model": "Netzabsicherung", "240": "16A", …}}

Die AJAX-Antwort enthaelt auch Spalten, die MAHE gar nicht anzeigt — Reste
frueherer Baureihen, meist leer. Uebernommen wird nur, was in der Konfiguration
als `visible` steht.

Ergebnis: build/mahe_specs.json

    { "hypertig-ax": {
        "table_id": "12146",
        "title": "HyperTIG AX",
        "columns": [{"key": "240", "title": "250"}, …],
        "rows": [{"model": "Netzabsicherung", "240": "16A", …}, …] } }

Welche Seite zu welchem Produkt gehoert, entscheidet die Zuordnung in
data/SPECTAB.json — nicht dieses Skript.
"""

import base64
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import core as C  # noqa: E402

CACHE = C.BUILD / "cache" / "mahe"
OUT = C.BUILD / "mahe_specs.json"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
AJAX = ("https://mahe-online.de/wp-admin/admin-ajax.php"
        "?action=wp_ajax_ninja_tables_public_action"
        "&table_id={}&target_action=get-all-data")

INSTANCE = re.compile(r"window\[['\"]ninja_table_instance_\d+['\"]\]\s*=\s*(\{.*\})\s*;?\s*$",
                      re.S)


def fetch(url):
    return subprocess.run(["curl", "-sSL", "--max-time", "40", "-A", UA, url],
                          capture_output=True, text=True).stdout


def configs(html):
    """Alle Ninja-Tables-Konfigurationen einer Seite, in Reihenfolge der Seite."""
    out = []
    for src in re.findall(r'<script[^>]+src=["\'](data:text/javascript;base64,[^"\']+)["\']',
                          html):
        b64 = urllib.parse.unquote(src.split(",", 1)[1])
        try:
            code = base64.b64decode(b64 + "=" * (-len(b64) % 4)).decode("utf-8", "replace")
        except Exception:
            continue
        m = INSTANCE.search(code.strip())
        if not m:
            continue
        try:
            out.append(json.loads(m.group(1)))
        except json.JSONDecodeError:
            pass
    return out


def main():
    if not CACHE.is_dir():
        print("Kein Cache – zuerst build/scrape_mahe.py laufen lassen.")
        sys.exit(1)

    out, leer, warn = {}, [], []
    files = sorted(CACHE.glob("*.html"))
    print(f"{len(files)} Seiten\n")

    for f in files:
        slug = f.stem
        html = f.read_text("utf-8", errors="replace")
        cfgs = configs(html)
        if not cfgs:
            if "data-footable_id" in html:
                warn.append(f"{slug}: Tabelle im Markup, aber keine Konfiguration")
            else:
                leer.append(slug)
            continue

        for cfg in cfgs:
            tid = str(cfg.get("table_id") or "")
            cols = [{"key": c["key"], "title": str(c.get("title", c["key"])).strip()}
                    for c in cfg.get("columns", [])
                    if c.get("visible") and c.get("key") != "model"]
            if not tid or not cols:
                continue
            try:
                data = json.loads(fetch(AJAX.format(tid)))
            except json.JSONDecodeError:
                warn.append(f"{slug}: Tabelle {tid} lieferte kein JSON")
                continue
            rows = []
            for r in data:
                if not (isinstance(r, dict) and "value" in r):
                    continue
                v = r["value"]
                row = {"model": str(v.get("model", "")).strip()}
                for c in cols:
                    row[c["key"]] = str(v.get(c["key"], "")).strip()
                if row["model"]:
                    rows.append(row)
            if not rows:
                continue

            # Spalte ohne einen einzigen Wert waere eine leere Tabellenspalte
            for c in cols:
                if not any(r[c["key"]] for r in rows):
                    warn.append(f"{slug}/{tid}: Spalte '{c['title']}' ist ueberall leer")

            key = slug if len(cfgs) == 1 else f"{slug}#{tid}"
            out[key] = {"table_id": tid, "title": str(cfg.get("title", "")).strip(),
                        "columns": cols, "rows": rows}
            titles = ", ".join(c["title"] for c in cols)
            print(f"  {key:26} {len(rows):>2} Zeilen × {len(cols)}: {titles}")

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf-8")
    print(f"\n{len(out)} Tabellen -> {OUT.relative_to(C.ROOT)}")
    if warn:
        print("\nHinweise:")
        for w in warn:
            print("  " + w)
    if leer:
        print(f"\nohne Tabelle: {', '.join(leer)}")


if __name__ == "__main__":
    main()
