#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bedienungsanleitungen und technische Datenblaetter von MAHE je Geraet einsammeln.

MAHE haengt sie als Schaltflaechen unter jede Produktseite. Bisher standen auf
unseren Produktseiten nur der Katalog, das EN-1090-Zertifikat und die
Sicherheitsdatenblaetter - also nichts Geraetespezifisches. Genau die
Anleitungen sind aber das, was Kundschaft nach dem Kauf sucht.

Verlinkt wird auf mahe-online.de, nicht gespiegelt: es sind die Dokumente des
Herstellers, und dort stehen sie immer in der aktuellen Fassung.

Aufruf:
    python3 build/scrape_dls.py            nur anzeigen, was gefunden wird
    python3 build/scrape_dls.py --check    jede PDF-URL einmal anfragen
    python3 build/scrape_dls.py --write    data/DLDEV.json schreiben

Die Pruefung laeuft bewusst nicht im normalen Build mit: sonst haenge der
Deploy an der Erreichbarkeit von mahe-online.de.
"""
import html
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import core as C  # noqa: E402

ROOT = C.ROOT
CACHE = ROOT / "build/cache/mahe"

# Unser Produkt -> MAHE-Seite. Quelle: DEV/DEV_MULTI aus build/verify_mahe.py
# und data/SPECMAP.json; beide sind bereits gepruefte Zuordnungen.
SEITE = {
    "hypermig-x": "hypermig", "ecomig": "d-mig", "mms": "mms",
    "omega-ax": "omega-ac-dc-2", "beta-dx": "beta-dx", "beta-digital": "beta-digital",
    "delta": "delta", "delta-digital": "delta-digital",
    "delta-digital-ds": "delta-digital-ds", "i-1600": "i-1600",
    "hypertig-ax": "hypertig-ax", "hypertig-dx": "hypertig-dx",
    "hypertig-acdc": "hypertig", "plasma-tig": "plasma-tig",
    "theta-40": "theta-40", "theta-60": "theta-60-hsc", "theta-120": "theta-120-hsc",
    "theta-180": "theta-160", "theta-60-aut": "theta-60-aut",
    "theta-120-aut": "theta-120-aut",
    "minicleaner": "minicleaner", "hypercleaner-st": "hypercleaner-st",
    "hypercleaner-plus": "hypercleaner-st-plus",
    "hypercleaner-speed": "hypercleaner-st-speed",
    "hypercleaner-ct200": "hypercleaner-ct-200",
    "hcs1": "hcs-1-signiergerat", "mlf100": "mlf100",
}

# Vom Hersteller kommt nur Deutsch. Die Bezeichnung wird uebersetzt, das
# Dokument bleibt deutsch - das sagt der Untertitel auch.
ART = {
    "anleitung": {"de": "Bedienungsanleitung", "fr": "Mode d'emploi",
                  "it": "Istruzioni per l'uso"},
    "datenblatt": {"de": "Technisches Datenblatt", "fr": "Fiche technique",
                   "it": "Scheda tecnica"},
}
UNTER = {"de": "Herstellerdokument von MAHE · deutsch",
         "fr": "Document du fabricant MAHE · en allemand",
         "it": "Documento del produttore MAHE · in tedesco"}

ANKER = re.compile(r'<a[^>]+href="([^"]+\.pdf)"[^>]*>(.*?)</a>', re.S | re.I)
# Fuss- und Randlinks, die auf jeder Seite stehen
UEBERALL = ("Neue_Panelsysteme", "Mahe_Konformations", "Katalog_2023",
            "Mahe_Katalog_2022", "Angebot_Q4", "HyCleanRapid", "HyClean_RP1",
            "HyCleanPolish", "Signierelektrolyt", "Neutralyt")


def art_und_zusatz(titel):
    """'Technisches Datenblatt HyperMIG X CWK' -> ('datenblatt', 'HyperMIG X CWK')"""
    t = " ".join(titel.split())
    # MAHE schreibt es mal richtig, mal "Bedienunganleitung" (d-mig) - beides fangen
    m = re.match(r"(Bedien\w*anleitung|Betriebsanleitung)\s*(.*)$", t, re.I)
    if m:
        return "anleitung", m.group(2).strip()
    m = re.match(r"Technisches\s+Datenblatt\s*(.*)$", t, re.I)
    if m:
        return "datenblatt", m.group(1).strip()
    return None, t


def sammeln():
    out, ohne = {}, []
    for pid, seite in sorted(SEITE.items()):
        f = CACHE / f"{seite}.html"
        if not f.exists():
            ohne.append((pid, f"Seite {seite}.html nicht im Cache"))
            continue
        h = f.read_text("utf-8", errors="replace")
        eintraege, gesehen = [], set()
        for u, roh in ANKER.findall(h):
            if any(g in u for g in UEBERALL):
                continue
            titel = html.unescape(re.sub(r"<[^>]+>", "", roh)).strip()
            art, zusatz = art_und_zusatz(titel)
            if not art:
                continue
            # http -> https; MAHE liefert beides aus, unsere Seite laeuft auf https
            u = re.sub(r"^http://", "https://", u.strip())
            if u in gesehen:
                continue
            gesehen.add(u)
            eintraege.append({
                "k": "PDF",
                "t": {l: (ART[art][l] + (" " + zusatz if zusatz else ""))
                      for l in ("de", "fr", "it")},
                "s": dict(UNTER),
                "u": u,
                "art": art,
            })
        # Anleitung vor Datenblatt
        eintraege.sort(key=lambda d: (d["art"] != "anleitung",))
        for d in eintraege:
            del d["art"]
        if eintraege:
            out[pid] = eintraege
        else:
            ohne.append((pid, f"keine PDFs auf {seite}.html"))
    return out, ohne


def pruefen(daten):
    """Jede URL einmal anfragen. Ein toter Link im Downloadbereich ist schlimmer
    als kein Link - dann sucht die Kundschaft weiter und findet nichts."""
    urls = sorted({d["u"] for ds in daten.values() for d in ds})
    schlecht = []
    for u in urls:
        r = subprocess.run(["curl", "-sIL", "-o", "/dev/null", "--max-time", "25",
                            "-w", "%{http_code} %{content_type}", u],
                           capture_output=True, text=True)
        code, _, ctype = r.stdout.strip().partition(" ")
        if code != "200" or "pdf" not in ctype.lower():
            schlecht.append((u, r.stdout.strip()))
        print(f"  {code}  {ctype[:24]:24} {urllib.parse.unquote(u.split('/')[-1])}")
    return len(urls), schlecht


if __name__ == "__main__":
    daten, ohne = sammeln()
    n = sum(len(v) for v in daten.values())
    print(f"{n} Dokumente fuer {len(daten)} Geraete\n")
    for pid, ds in sorted(daten.items()):
        print(f"{pid}:")
        for d in ds:
            print(f"   {d['t']['de'][:52]:52} {d['u'].split('/')[-1][:44]}")
    if ohne:
        print("\nohne Dokumente:")
        for pid, grund in ohne:
            print(f"   {pid:20} {grund}")

    if "--check" in sys.argv:
        print("\nLinks pruefen …")
        gesamt, schlecht = pruefen(daten)
        print(f"\n{gesamt} URLs, {len(schlecht)} nicht erreichbar")
        for u, was in schlecht:
            print("   ", was, u)
        if schlecht:
            sys.exit(1)

    if "--write" in sys.argv:
        (ROOT / "data/DLDEV.json").write_text(
            json.dumps({"_kommentar": (
                "Bedienungsanleitungen und technische Datenblaetter je Geraet, "
                "verlinkt auf mahe-online.de. Erzeugt aus dem Seitencache mit "
                "build/scrape_dls.py - nicht von Hand pflegen, sondern das "
                "Skript neu laufen lassen."), **daten},
                ensure_ascii=False, indent=1) + "\n", "utf-8")
        print("\ndata/DLDEV.json geschrieben")
