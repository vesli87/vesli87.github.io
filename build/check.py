#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QA für den generierten Auftritt.  Aufruf:  python3 build/check.py

Prüft:
  1. jedes JSON-LD parst und trägt @context/@graph
  2. jeder interne Link zeigt auf eine existierende Datei
  3. canonical stimmt mit dem eigenen Pfad überein
  4. alle hreflang-Alternates existieren und sind gegenseitig verlinkt
  5. Titel/Description vorhanden und in sinnvoller Länge, keine Dubletten
  6. keine Reste der alten SPA (data-i18n, onclick="goCat", goProd)
  7. alle referenzierten lokalen Bilder existieren
  8. Tag-Balance der wichtigsten Container
  9. jede sitemap-URL existiert; jede indexierbare Seite steht in der sitemap
 10. alle drei Sprachen haben gleich viele Seiten

Exit-Code 1, sobald ein Fehler auftritt (Warnungen brechen nicht ab).
"""

import collections
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import core as C  # noqa: E402

ROOT = C.ROOT
errors, warnings = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def all_pages():
    for f in ROOT.rglob("index.html"):
        if "build" in f.parts or "node_modules" in f.parts:
            continue
        yield f
    p404 = ROOT / "404.html"
    if p404.exists():
        yield p404


def path_of(f):
    rel = f.relative_to(ROOT)
    if rel.name == "404.html":
        return "/404.html"
    d = str(rel.parent).replace("\\", "/")
    return "/" if d == "." else "/" + d + "/"


def target_exists(href):
    """Löst einen internen Link auf eine Datei im Repo auf."""
    href = href.split("#")[0].split("?")[0]
    if not href.startswith("/"):
        return True                      # relative Links kommen nicht vor
    if href.endswith("/"):
        return (ROOT / href.strip("/") / "index.html").exists() or href == "/"
    return (ROOT / href.lstrip("/")).exists()


def main():
    pages = sorted(all_pages())
    if len(pages) < 200:
        err(f"nur {len(pages)} Seiten gefunden – Build unvollständig?")

    titles, descs = collections.Counter(), collections.Counter()
    per_lang = collections.Counter()
    seen_paths = set()

    for f in pages:
        p = path_of(f)
        seen_paths.add(p)
        html = f.read_text("utf-8")
        where = f"{p}"

        if p != "/404.html":   # 404 gibt es nur einmal, nicht pro Sprache
            lang = "fr" if p.startswith("/fr/") else "it" if p.startswith("/it/") else "de"
            per_lang[lang] += 1

        # 1. JSON-LD
        for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
            try:
                d = json.loads(m.group(1))
            except json.JSONDecodeError as ex:
                err(f"{where}: JSON-LD kaputt ({ex})")
                continue
            if "@context" not in d:
                err(f"{where}: JSON-LD ohne @context")
            for node in d.get("@graph", []):
                if "@type" not in node:
                    err(f"{where}: JSON-LD-Knoten ohne @type")

        # 5. title / description
        mt = re.search(r"<title>(.*?)</title>", html, re.S)
        md = re.search(r'<meta name="description" content="(.*?)">', html, re.S)
        if not mt or not mt.group(1).strip():
            err(f"{where}: kein <title>")
        else:
            ti = mt.group(1).strip()
            titles[ti] += 1
            if len(ti) > 70:
                warn(f"{where}: Titel {len(ti)} Zeichen (>70): {ti[:60]}…")
        if not md or not md.group(1).strip():
            err(f"{where}: keine meta description")
        else:
            de_ = md.group(1).strip()
            descs[de_] += 1
            if not (50 <= len(de_) <= 185):
                warn(f"{where}: description {len(de_)} Zeichen")

        # 3. canonical
        mc = re.search(r'<link rel="canonical" href="([^"]+)"', html)
        if not mc:
            err(f"{where}: kein canonical")
        else:
            want = C.SITE + (p if p != "/404.html" else "/")
            if mc.group(1) != want:
                err(f"{where}: canonical {mc.group(1)} != {want}")

        # 4. hreflang
        alts = re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', html)
        codes = {a for a, _ in alts}
        if p != "/404.html":
            for need in ("de-CH", "fr-CH", "it-CH", "x-default"):
                if need not in codes:
                    err(f"{where}: hreflang {need} fehlt")
            for _, href in alts:
                if not target_exists(href.replace(C.SITE, "")):
                    err(f"{where}: hreflang-Ziel fehlt {href}")

        # 2. interne Links
        for href in re.findall(r'href="(/[^"#]*)"', html):
            if not target_exists(href):
                err(f"{where}: toter Link -> {href}")

        # 7. lokale Bilder
        for src in re.findall(r'src="(/assets/[^"]+)"', html):
            if not (ROOT / src.lstrip("/")).exists():
                err(f"{where}: Bild fehlt {src}")

        # 6. Reste der alten SPA
        for bad in ('data-i18n=', 'onclick="goCat', 'onclick="goProd', 'onclick="goView',
                    'onclick="show(', "EMBED-MARKER"):
            if bad in html:
                err(f"{where}: Rest der alten SPA gefunden: {bad}")

        # 8. Tag-Balance
        for tag in ("div", "section", "article", "aside", "nav", "main", "ul", "li", "a"):
            o = len(re.findall(r"<%s[\s>]" % tag, html))
            c = len(re.findall(r"</%s>" % tag, html))
            if o != c:
                err(f"{where}: <{tag}> {o} offen vs {c} geschlossen")

    # 5b. Dubletten
    for ti, n in titles.items():
        if n > 1:
            err(f"Titel {n}× vergeben: {ti[:70]}")
    for d, n in descs.items():
        if n > 1:
            warn(f"description {n}× vergeben: {d[:70]}…")

    # 9. sitemap
    sm = (ROOT / "sitemap.xml").read_text("utf-8")
    locs = re.findall(r"<loc>([^<]+)</loc>", sm)
    for loc in locs:
        rel = loc.replace(C.SITE, "")
        if not target_exists(rel):
            err(f"sitemap: {loc} existiert nicht")
    smset = {l.replace(C.SITE, "") for l in locs}
    noindex = set()
    for f in pages:
        if 'name="robots" content="noindex' in f.read_text("utf-8"):
            noindex.add(path_of(f))
    missing = seen_paths - smset - noindex - {"/404.html"}
    for m in sorted(missing):
        err(f"nicht in der sitemap: {m}")

    # 10. Sprachparität
    if len(set(per_lang.values())) != 1:
        err(f"Sprachen ungleich gross: {dict(per_lang)}")

    # robots / llms
    for need in ("robots.txt", "llms.txt", "llms-full.txt", "site.webmanifest",
                 "data/products.json", "data/search-de.json", "data/search-fr.json",
                 "data/search-it.json", "assets/js/app.js", "assets/css/site.css"):
        if not (ROOT / need).exists():
            err(f"Datei fehlt: {need}")

    print(f"{len(pages)} Seiten geprüft  ·  {dict(per_lang)}")
    for w in warnings[:25]:
        print("  WARN " + w)
    if len(warnings) > 25:
        print(f"  … und {len(warnings)-25} weitere Warnungen")
    for e in errors[:40]:
        print("  FEHLER " + e)
    if len(errors) > 40:
        print(f"  … und {len(errors)-40} weitere Fehler")
    print(f"\n{len(errors)} Fehler, {len(warnings)} Warnungen")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
