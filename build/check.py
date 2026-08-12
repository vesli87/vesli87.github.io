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


# Pflichtfelder je Schema-Typ. Fehlen sie, verliert Google die Rich Results und
# Antwortmaschinen können die Angaben nicht zuordnen.
LD_REQUIRED = {
    # Product ohne "offers": seit dem 05.08.2026 gibt es hier keinen
    # Offer-Knoten mehr. Er trug priceCurrency ohne price, und eine Waehrung
    # ohne Betrag ist kein Angebot - jeder Validator meldete das fehlende
    # Pflichtfeld, auf 231 Seiten. Siehe render.py::ld_product.
    "Product":        ["name", "description", "image", "brand", "sku", "url"],
    "Offer":          ["availability", "priceCurrency", "url"],
    "FAQPage":        ["mainEntity"],
    "BreadcrumbList": ["itemListElement"],
    "ItemList":       ["itemListElement", "numberOfItems"],
    "Organization":   ["name", "url", "address", "telephone", "email"],
    "WebSite":        ["url", "name", "potentialAction"],
    "WebPage":        ["url", "name", "inLanguage"],
}


def check_ld_node(where, node, types, ids):
    """Pflichtfelder, aufgelöste @id-Verweise und ein paar inhaltliche Fallen."""
    for ty in types:
        for field in LD_REQUIRED.get(ty, []):
            if field not in node or node[field] in (None, "", [], {}):
                err(f"{where}: JSON-LD {ty} ohne '{field}'")

    # Verweise wie {"@id": ".../#organization"} müssen im selben Graph landen
    def refs(v):
        if isinstance(v, dict):
            if set(v.keys()) == {"@id"} and v["@id"] not in ids:
                err(f"{where}: JSON-LD verweist auf unbekanntes @id {v['@id']}")
            for x in v.values():
                refs(x)
        elif isinstance(v, list):
            for x in v:
                refs(x)
    refs({k: v for k, v in node.items() if k != "@id"})

    if "Product" in types:
        # "Preis auf Anfrage": es darf kein Preis behauptet werden – weder 0
        # noch leer. Und es darf gar kein Offer geben: ohne price ist er
        # unvollstaendig, mit price waere er gelogen.
        if "offers" in node:
            err(f"{where}: Product hat wieder ein offers – ohne Preis ist das ein "
                f"unvollstaendiger Offer, mit Preis ein falscher")
        if "price" in node:
            err(f"{where}: Product hat ein price-Feld – die Website führt keine Preise")
        if not str(node.get("sku", "")).strip():
            err(f"{where}: Product ohne sku")
        if isinstance(node.get("image"), list) and not node["image"]:
            err(f"{where}: Product mit leerer image-Liste")
        for prop in node.get("additionalProperty", []):
            if not prop.get("name") or not prop.get("value"):
                err(f"{where}: PropertyValue ohne name/value")

    if "FAQPage" in types:
        for q in node.get("mainEntity", []):
            a = (q.get("acceptedAnswer") or {}).get("text", "")
            if not q.get("name", "").strip() or not a.strip():
                err(f"{where}: FAQ-Eintrag ohne Frage oder Antwort")
            elif len(a) < 80:
                warn(f"{where}: FAQ-Antwort sehr kurz ({len(a)} Zeichen) – "
                     f"Antwortmaschinen zitieren lieber vollständige Absätze")

    if "BreadcrumbList" in types:
        pos = [i.get("position") for i in node.get("itemListElement", [])]
        if pos != list(range(1, len(pos) + 1)):
            err(f"{where}: BreadcrumbList mit luecken­hafter position-Folge {pos}")


def referenzen():
    """Kundenstimmen: keine ohne schriftliche Freigabe, keine ohne Firma.

    Eine Referenz namentlich zu nennen ist eine Bearbeitung von Personendaten
    (revDSG); ohne Zustimmung hat sie auf der Seite nichts verloren. Und eine
    erfundene Stimme waere eine irrefuehrende Angabe nach UWG Art. 3 Abs. 1
    lit. b. Dieser Waechter kann das Erfinden nicht verhindern - er stellt
    aber sicher, dass jeder Eintrag die Freigabe ausdruecklich behauptet.
    """
    for i, r in enumerate(C.REF.get("refs", [])):
        wo = f"data/REF.json[{i}]"
        if not r.get("firma"):
            err(f"{wo}: Referenz ohne Firma")
        if not r.get("freigabe"):
            err(f"{wo}: Referenz ohne 'freigabe': true - wird nicht ausgegeben")
        txt = r.get("text") or {}
        if not txt.get("de"):
            err(f"{wo}: Referenz ohne deutschen Text")
        for l in ("fr", "it"):
            if not txt.get(l):
                warn(f"{wo}: Referenz ohne {l.upper()}-Fassung")
        g = r.get("geraet")
        if g and g not in C.BY_ID:
            err(f"{wo}: Referenz nennt unbekanntes Geraet {g!r}")


def reihenfolge():
    """data/P.json muss nach Kategorie und Unterkategorie gruppiert bleiben.

    Die Seite "Alle Geräte" zeigt die Liste in genau dieser Reihenfolge. Wer ein
    Produkt hinten anhaengt, schiebt es dort ans Ende der ganzen Liste - so
    standen die beiden Schneidtische hinter dem letzten Verschleissteil, und
    das Zubehoer lag zwischendrin. Diese Pruefung faengt das beim naechsten
    Mal ab, bevor es jemand auf der Website sieht.
    """
    kat = {c["id"]: i for i, c in enumerate(C.CATS)}
    sub = {(c["id"], s): j for c in C.CATS for j, s in enumerate(c["subs"])}
    schluessel = []
    for p in C.P:
        k = (p["cat"], p["sub"])
        if k not in sub:
            err(f'data/P.json: {p["id"]} hat die Unterkategorie „{p["sub"]}“, '
                f'die in CATS.json unter {p["cat"]} nicht vorkommt')
            return
        schluessel.append((kat[p["cat"]], sub[k], p["id"]))
    for (a, b, ida), (c_, d, idb) in zip(schluessel, schluessel[1:]):
        if (a, b) > (c_, d):
            err(f"data/P.json ist nicht nach Kategorie/Unterkategorie sortiert: "
                f"{idb} steht hinter {ida}, gehoert aber davor")
            return


def main():
    pages = sorted(all_pages())
    if len(pages) < 200:
        err(f"nur {len(pages)} Seiten gefunden – Build unvollständig?")

    referenzen()
    reihenfolge()

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

        # 1. JSON-LD — parst, hat @context, und die Knoten sind inhaltlich brauchbar
        for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
            try:
                d = json.loads(m.group(1))
            except json.JSONDecodeError as ex:
                err(f"{where}: JSON-LD kaputt ({ex})")
                continue
            if "@context" not in d:
                err(f"{where}: JSON-LD ohne @context")
            graph = d.get("@graph", [])
            ids = {n["@id"] for n in graph if isinstance(n, dict) and "@id" in n}
            for node in graph:
                if "@type" not in node:
                    err(f"{where}: JSON-LD-Knoten ohne @type")
                    continue
                types = node["@type"] if isinstance(node["@type"], list) else [node["@type"]]
                check_ld_node(where, node, types, ids)

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

        # 7. lokale Assets (Bilder, CSS, JS) – ?v=<hash> vorher abschneiden
        for src in re.findall(r'(?:src|href)="(/assets/[^"]+)"', html):
            if not (ROOT / src.split("?")[0].lstrip("/")).exists():
                err(f"{where}: Asset fehlt {src}")

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
    # Doppelte URLs. Sie entstehen nicht durch Tippfehler, sondern wenn zwei
    # Seitenarten denselben Pfad beanspruchen - so geschehen bei der
    # Unterkategorie "Plasma TIG" und dem Produkt "plasma-tig". Geschrieben
    # wird dann nur die zuletzt erzeugte Seite, die andere ist still
    # verschwunden. Genau das soll hier auffallen.
    for loc, n in collections.Counter(locs).items():
        if n > 1:
            err(f"sitemap: {loc} steht {n}× drin - zwei Seiten mit derselben URL?")
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

    # 11. Technische Daten: jede Zeile der MAHE-Tabellen braucht fr und it,
    #     sonst steht auf der französischen Seite plötzlich Deutsch.
    for key in C.SPECMAP:
        if key.startswith("_"):
            continue
        if key not in C.BY_ID:
            err(f"SPECMAP: Produkt {key} gibt es nicht")
        for tab in C.SPECMAP[key]:
            if tab not in C.MAHE_SPECS:
                err(f"SPECMAP {key}: Tabelle '{tab}' fehlt in build/mahe_specs.json")
    for p in C.P:
        for lab in C.specRowsDE(p):
            tr = C.SPECROW.get(lab)
            if not tr:
                err(f"SPECROW: '{lab}' fehlt ({p['id']})")
            else:
                for l in C.LANGS:
                    if l != C.DEFAULT_LANG and not tr.get(l):
                        err(f"SPECROW '{lab}': Übersetzung {l} fehlt")

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
