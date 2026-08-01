#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wort-für-Wort-Abgleich unserer Inhalte mit mahe-online.de.

    python3 build/verify_mahe.py            # gegen den Cache
    python3 build/verify_mahe.py --fresh    # Seiten und Tabellen neu laden

Geprüft wird beides:

* die Besonderheiten aus data/HL_DEVICE.json und data/PANEL_HL_DEVICE.json
* die technischen Daten, also jede Zelle jeder Tabelle, die eine Produktseite
  zeigt (data/SPECMAP.json → build/mahe_specs.json)

Erlaubt sind nur die bewusst vorgenommenen Korrekturen: Schweizer „ss" statt
„ß" und die Tippfehler von MAHE (Relegung, Syniergie, Reiningen, Funkcion,
Eein, Sprizerfreier, Elektoden, „11,5 KG2", „CV und CW", Einschaultdauer,
Nezabsicherung, Ausgangstrom, „230V, 60/60Hz").

Jede andere Abweichung ist ein Fehler und wird gemeldet. Am Ende steht, an
welchen Stellen wir bewusst von MAHE abweichen — die Liste soll kurz bleiben.
"""

import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import core as C  # noqa: E402

SRC = json.loads((C.BUILD / "mahe_besonderheiten.json").read_text("utf-8"))

# Zuordnung unserer Schlüssel auf die Einträge der Herstellerseite
DEV = {
 "hcs1": "hcs-1-signiergerat :: HCS 1", "mlf100": "mlf100 :: MLF100",
 "minicleaner": "minicleaner :: MiniCleaner",
 "hypercleaner-st": "hypercleaner-st :: HyperCleaner ST",
 "hypercleaner-plus": "hypercleaner-st-plus :: HyperCleaner ST Plus",
 "hypercleaner-speed": "hypercleaner-st-speed :: HyperCleaner ST Speed",
 "hypercleaner-ct200": "hypercleaner-ct-200 :: HyperCleaner CT 200",
 "hypertig-ax": "hypertig-ax :: HyperTIG AX",
 "hypertig-dx": "hypertig-dx :: HyperTIG DX",
 "hypertig-acdc": "hypertig :: HyperTIG AC/DC CWK",
 "plasma-tig": "plasma-tig :: Plasma TIG", "i-1600": "i-1600 :: i-1600",
 "theta-40": "theta-40 :: Theta 40", "theta-60": "theta-60-hsc :: Theta 60 HSC",
 "theta-120": "theta-120-hsc :: Theta 120 HSC", "theta-180": "theta-160 :: Theta 180 HSC",
 "theta-60-aut": "theta-60-aut :: Theta 60 AUT",
 "theta-120-aut": "theta-120-aut :: Theta 120 AUT",
 "delta": "delta :: Delta", "delta-digital": "delta-digital :: Delta digital",
 "delta-digital-ds": "delta-digital-ds :: Delta Digital DS",
 "beta-digital": "beta-digital :: Beta digital 240 Professional",
}
DEV_MULTI = {  # unser Produkt deckt mehrere MAHE-Varianten ab
 "omega-ax": ["omega-ac-dc-2 :: Omega AX pro", "omega-ac-dc-2 :: Omega AX syn"],
 "beta-dx":  ["beta-dx :: Beta DX pro", "beta-dx :: Beta DX syn"],
 "mms":      ["mms :: MMS 2000C", "mms :: MMS 2400/3000 EX"],
}
PANEL = {
 "hypermig_ex": "hypermig :: EX – EcoPuls Front Panel",
 "hypermig_hx": "hypermig :: HX – Hyper Front Panel",
 "hypermig_sx": "hypermig :: SX – Steel Puls Front Panel",
 "omega_pro": "omega-ac-dc-2 :: pro", "omega_syn": "omega-ac-dc-2 :: syn",
 "betadx_pro": "beta-dx :: pro", "betadx_syn": "beta-dx :: syn",
 "betadig_profi": "beta-digital :: Professional", "betadig_syn": "beta-digital :: Synergy",
 "hypertig_ax": "hypertig-ax :: Fronteingabesysteme",
 "hypertig_dx": "hypertig-dx :: Fronteingabesysteme",
 "hypertig_acdc": "hypertig :: Fronteingabesysteme",
 "ct200_panel": "hypercleaner-ct-200 :: Professional",
 "ct200_syn": "hypercleaner-ct-200 :: Synergy",
}

FIX = [("ß", "ss"), ("Relegung", "Regelung"), ("Syniergie-Programm", "Synergieprogramm"),
       ("Synergie Programme", "Synergieprogramm"), ("Reiningen", "Reinigen"),
       ("Funkcion", "Funktion"), ("Hyper Spot", "HyperSpot"),
       ("Fernbedienung Eein / Aus", "Fernbedienung Ein/Aus"),
       ("Fernbedienung Ein / Aus", "Fernbedienung Ein/Aus"),
       ("Sprizerfreier", "Spritzerfreier"), ("MMA Elektoden", "MMA Elektroden"),
       ("nur 11,5 KG2", "nur 11,5 kg"), ("nur 21 KG", "nur 21 kg"),
       ("Umschaltbar CV und CW", "Umschaltbar CV und CC"),
       ("ActiveSpot Schnelle Heftfunktion", "ActiveSpot – schnelle Heftfunktion"),
       ("Galvanisieren.", "Galvanisieren")]
# "Digitalanzeige" bleibt wie bei MAHE - das ist kein Tippfehler,
# sondern deren Schreibweise.


def norm(s):
    for a, b in FIX:
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def expect(keys):
    out = []
    for k in keys:
        for i in SRC[k]["items"]:
            n = norm(i)
            if n not in out:
                out.append(n)
    return out


def specs():
    """Jede Tabellenzelle gegen MAHE. Rueckgabe: (Fehler, bewusste Abweichungen)."""
    bad, deviations = 0, []
    print("\nTECHNISCHE DATEN")
    for pid in sorted(k for k in C.SPECMAP if not k.startswith("_")):
        p = C.BY_ID.get(pid)
        if not p:
            print(f"  UNBEKANNTES PRODUKT  {pid}")
            bad += 1
            continue
        for key in C.SPECMAP[pid]:
            raw = C.MAHE_SPECS.get(key)
            if not raw:
                print(f"  FEHLT bei MAHE  {pid} -> {key}")
                bad += 1
                continue
            cols = [c["key"] for c in raw["columns"]]
            n_dev, n_cell = 0, 0
            for r in raw["rows"]:
                for src, ours, wo in [(r.get("model", ""), C._specK(r.get("model", "")), "Zeile")] + \
                                     [(r.get(c, ""), C._specV(r.get(c, "")), "Wert") for c in cols]:
                    n_cell += 1
                    if src.strip() == ours:
                        continue
                    n_dev += 1
                    rule = ("leer → –" if ours == C.SPEC_EMPTY and src.strip() in ("", "-", "--", "---")
                            else next((f"{a} → {b}" for a, b in C.SPEC_FIX_K + C.SPEC_FIX_V
                                       if a in src), ""))
                    if not rule:
                        print(f"  UNERKLAERT  {pid}/{key} {wo}: {src!r} -> {ours!r}")
                        bad += 1
                    elif rule != "leer → –":
                        deviations.append(f"{pid}/{key}: {rule}")
            print(f"  ok   {pid + ' -> ' + key:44} {len(raw['rows']):>2} Zeilen "
                  f"× {len(cols)} Varianten, {n_cell} Zellen")
    return bad, sorted(set(deviations))


def main():
    if "--fresh" in sys.argv:
        print("Seiten und Tabellen neu laden …")
        for script in ("scrape_mahe.py", "scrape_specs.py"):
            subprocess.run([sys.executable, str(C.BUILD / script), "--fresh"],
                           capture_output=True)
        globals()["SRC"] = json.loads((C.BUILD / "mahe_besonderheiten.json").read_text("utf-8"))
        C.MAHE_SPECS = json.loads((C.BUILD / "mahe_specs.json").read_text("utf-8"))

    ours_dev = json.loads((C.DATA / "HL_DEVICE.json").read_text("utf-8"))
    ours_pan = json.loads((C.DATA / "PANEL_HL_DEVICE.json").read_text("utf-8"))
    bad = 0

    def cmp(label, ours, keys):
        nonlocal bad
        missing = [k for k in keys if k not in SRC]
        if missing:
            print(f"  FEHLT bei MAHE  {label:22} {missing}")
            bad += 1
            return
        soll = expect(keys)
        if ours == soll:
            print(f"  ok   {label:22} {len(soll):>2} Punkte")
            return
        bad += 1
        print(f"  ABWEICHUNG  {label}")
        for x in soll:
            if x not in ours:
                print(f"       fehlt bei uns : {x}")
        for x in ours:
            if x not in soll:
                print(f"       zu viel bei uns: {x}")

    print("GERÄTE")
    for pid, key in sorted(DEV.items()):
        cmp(pid, ours_dev.get(pid, {}).get("de", []), [key])
    for pid, keys in sorted(DEV_MULTI.items()):
        cmp(pid + " (Varianten)", ours_dev.get(pid, {}).get("de", []), keys)
    print("\nFRONTPANELS")
    for pk, key in sorted(PANEL.items()):
        cmp(pk, ours_pan.get(pk, {}).get("de", []), [key])

    n = len(DEV) + len(DEV_MULTI) + len(PANEL)
    print(f"\n{n - bad}/{n} Besonderheiten stimmen wörtlich mit mahe-online.de überein")

    sbad, deviations = specs()
    if deviations:
        print("\nBewusst anders als MAHE:")
        for d in deviations:
            print("  " + d)
    print(f"\n{sbad} Fehler in den technischen Daten")
    sys.exit(1 if bad or sbad else 0)


if __name__ == "__main__":
    main()
