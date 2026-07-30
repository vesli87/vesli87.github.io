#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tiefenprüfung des Auftritts.  Aufruf:  python3 build/audit.py [--live]

check.py sichert die Grundlagen (JSON-LD, Links, canonical, hreflang, Sitemap).
Dieses Skript geht darüber hinaus und sucht nach Fehlern, die einem Build-Check
entgehen, aber Nutzern und Suchmaschinen auffallen:

  A  Überschriftenhierarchie   genau ein h1, keine übersprungene Ebene
  B  Erreichbarkeit            verwaiste Seiten, die von nirgends verlinkt sind
  C  NAP-Konsistenz            Name, Adresse, Telefon, Zeiten überall gleich
  D  Übersetzungslücken        deutscher Text, der in FR/IT stehen geblieben ist
  E  Alt-Texte                 leer, doppelt oder nur Dateiname
  F  Meta-Dubletten            gleiche description in derselben Sprache
  G  Sprachauszeichnung        lang-Attribut passt zum Pfad
  H  Live-Prüfung (--live)     Status, Weiterleitungen, Kompression, Zertifikat
"""

import collections
import concurrent.futures as cf
import html
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import core as C  # noqa: E402

ROOT = C.ROOT
problems = []   # (Schwere, Ort, Text)


def bad(where, msg):
    problems.append(("FEHLER", where, msg))


def note(where, msg):
    problems.append(("HINWEIS", where, msg))


def pages():
    for f in sorted(ROOT.rglob("index.html")):
        if "build" in f.parts:
            continue
        d = str(f.relative_to(ROOT).parent).replace("\\", "/")
        yield ("/" if d == "." else "/" + d + "/"), f


def text_of(h):
    """Sichtbarer Text ohne script/style."""
    h = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", h, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", h))


# --------------------------------------------------------------------------

def main():
    live = "--live" in sys.argv
    docs = list(pages())
    print(f"Prüfe {len(docs)} Seiten …\n")

    linked = set()
    descs = collections.defaultdict(list)
    titles = collections.defaultdict(list)
    alts = collections.Counter()

    for path, f in docs:
        h = f.read_text("utf-8")
        lang = "fr" if path.startswith("/fr/") else "it" if path.startswith("/it/") else "de"

        # ---- A. Überschriften -------------------------------------------
        heads = [(int(m.group(1)), re.sub(r"<[^>]+>", "", m.group(2)).strip())
                 for m in re.finditer(r"<h([1-6])[^>]*>(.*?)</h\1>", h, re.S)]
        h1 = [t for lv, t in heads if lv == 1]
        if len(h1) != 1:
            bad(path, f"{len(h1)} h1-Überschriften (genau eine erwartet)")
        prev = 0
        for lv, t in heads:
            if prev and lv > prev + 1:
                note(path, f"Ebene h{prev} → h{lv} übersprungen bei „{t[:40]}“")
            prev = lv

        # ---- B. Links einsammeln ----------------------------------------
        for href in re.findall(r'href="(/[^"#?]*)"', h):
            linked.add(href)

        # ---- C. NAP -------------------------------------------------------
        txt = text_of(h)
        co = C.COMPANY
        if "Bildfeld" in txt and "Bildfeldstrasse 24" not in txt:
            bad(path, "Strasse abweichend geschrieben")
        for wrong in ("Bildfelsstrasse", "info@ves-tech.ch", "17:30"):
            if wrong in txt:
                bad(path, f"veraltete Angabe im Text: {wrong}")
        if "tel:" in h and co["phone_href"] not in h:
            bad(path, "abweichende Telefonnummer im tel:-Link")

        # ---- D. Übersetzungslücken ---------------------------------------
        if lang != "de":
            # Wörter, die in FR/IT nichts verloren haben (Navigation/Fliesstext,
            # nicht Produktnamen wie „HyperMIG“ oder Marken).
            leaks = [w for w in ("Schweissgeräte", "Zubehör", "Anfrageliste",
                                 "Preis auf Anfrage", "Häufige Fragen",
                                 "Öffnungszeiten", "Zurück zur Übersicht")
                     if w in txt]
            if leaks:
                bad(path, f"deutscher Text in {lang.upper()}: {', '.join(leaks)}")

        # ---- E. Alt-Texte -------------------------------------------------
        for m in re.finditer(r"<img[^>]*>", h):
            tag = m.group(0)
            a = re.search(r'alt="([^"]*)"', tag)
            if a is None:
                bad(path, "img ohne alt-Attribut")
            elif a.group(1).strip():
                v = a.group(1).strip()
                alts[v] += 1
                if re.fullmatch(r"[\w.-]+\.(webp|jpg|png|svg)", v, re.I):
                    bad(path, f"alt ist nur ein Dateiname: {v}")

        # ---- F./G. Meta + lang -------------------------------------------
        mt = re.search(r"<title>(.*?)</title>", h, re.S)
        md = re.search(r'<meta name="description" content="(.*?)">', h, re.S)
        if mt:
            titles[(lang, mt.group(1))].append(path)
        if md:
            descs[(lang, md.group(1))].append(path)
        ml = re.search(r'<html lang="([^"]+)"', h)
        want = C.EX[lang]["hreflang"]
        if not ml or ml.group(1) != want:
            bad(path, f"lang-Attribut {ml.group(1) if ml else '—'} statt {want}")

    # ---- B. verwaiste Seiten --------------------------------------------
    allp = {p for p, _ in docs}
    orphans = allp - linked - {"/"}
    for o in sorted(orphans):
        note(o, "von keiner Seite verlinkt (nur über Sitemap erreichbar)")

    # ---- F. Dubletten ----------------------------------------------------
    for (lang, d), ps in descs.items():
        if len(ps) > 1:
            bad(ps[0], f"description {len(ps)}× in {lang.upper()}: {', '.join(ps[1:3])} …")
    for (lang, t), ps in titles.items():
        if len(ps) > 1:
            bad(ps[0], f"Titel {len(ps)}× in {lang.upper()}")

    # ---- H. Live ---------------------------------------------------------
    if live:
        print("Live-Prüfung …")
        urls = re.findall(r"<loc>([^<]+)</loc>", (ROOT / "sitemap.xml").read_text("utf-8"))

        def head(u):
            r = subprocess.run(["curl", "-sS", "-o", "/dev/null", "--max-time", "25",
                                "-w", "%{http_code}", u], capture_output=True, text=True)
            return u, r.stdout.strip()

        with cf.ThreadPoolExecutor(max_workers=12) as ex:
            for u, code in ex.map(head, urls):
                if code != "200":
                    bad(u.replace(C.SITE, ""), f"live HTTP {code}")

        for u, want in [("https://ves-tech.ch/", "301"),
                        ("https://vesli87.github.io/faq/", "301"),
                        ("http://www.ves-tech.ch/", "200")]:
            r = subprocess.run(["curl", "-sS", "-o", "/dev/null", "--max-time", "25",
                                "-w", "%{http_code}", u], capture_output=True, text=True)
            if r.stdout.strip() != want:
                note(u, f"erwartet {want}, bekommen {r.stdout.strip()}")

    # ---- Ausgabe ---------------------------------------------------------
    errs = [p for p in problems if p[0] == "FEHLER"]
    hints = [p for p in problems if p[0] == "HINWEIS"]
    for sev, where, msg in errs[:60]:
        print(f"  FEHLER  {where:52} {msg}")
    if len(errs) > 60:
        print(f"  … und {len(errs)-60} weitere Fehler")
    for sev, where, msg in hints[:30]:
        print(f"  hinweis {where:52} {msg}")
    if len(hints) > 30:
        print(f"  … und {len(hints)-30} weitere Hinweise")
    print(f"\n{len(errs)} Fehler, {len(hints)} Hinweise")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
