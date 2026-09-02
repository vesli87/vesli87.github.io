#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VES-TECH Swiss — Site-Build.

    python3 build/build.py

Erzeugt aus data/*.json den kompletten statischen Auftritt:
  * ~250 vorgerenderte HTML-Seiten (DE/FR/IT)
  * sitemap.xml mit hreflang-Alternates
  * robots.txt (inkl. ausdrücklicher Freigabe für KI-Crawler → AEO)
  * llms.txt / llms-full.txt  (Answer-Engine-Optimierung)
  * data/products.json        (maschinenlesbarer Katalog)
  * data/search-<lang>.json   (Suchindex für das Frontend)
  * site.webmanifest, CNAME

Alles ist idempotent: der Build kann jederzeit neu laufen.
"""

import datetime
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import core as C      # noqa: E402
import pages as PG    # noqa: E402
import render as R    # noqa: E402

OUT = C.ROOT
TODAY = datetime.date.today().isoformat()

# Verzeichnisse, die der Build vollständig verwaltet (werden vorher geleert)
MANAGED_DIRS = ["produkte", "fr", "it", "verfahren", "downloads", "kontakt",
                "faq", "suche", "impressum", "datenschutz", "service", "ueber-uns"]

written = []


def write(path, content):
    """Schreibt eine Seite. '/x/y/' -> x/y/index.html"""
    if path.endswith("/"):
        f = OUT / path.strip("/") / "index.html" if path != "/" else OUT / "index.html"
    else:
        f = OUT / path.lstrip("/")
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(content, "utf-8")
    written.append(path)
    return f


# --------------------------------------------------------------------------
# Suchindex + maschinenlesbarer Katalog
# --------------------------------------------------------------------------

SYNONYMS = {
    # Verfahren – wie Kundschaft wirklich sucht
    "wig": ["tig", "wolfram", "argon"],
    "tig": ["wig"],
    "mig": ["mag", "schutzgas", "mig/mag", "co2"],
    "mag": ["mig"],
    "mma": ["elektrode", "elektroden", "stabelektrode", "e-hand", "hand"],
    "plasma": ["schneiden", "schneider", "trennen", "cut"],
    # Werkstoffe
    "alu": ["aluminium", "alu"],
    "aluminium": ["alu"],
    "inox": ["chromstahl", "edelstahl", "vа", "va", "rostfrei", "v2a", "v4a"],
    "chromstahl": ["inox", "edelstahl"],
    "edelstahl": ["inox", "chromstahl"],
    "stahl": ["baustahl", "eisen"],
    # Zubehör
    "wagen": ["fahrwagen", "trolley", "chariot", "carrello"],
    "fahrwagen": ["wagen", "trolley"],
    "kuehler": ["wasserkuehlung", "kuehlung", "wk", "wasser"],
    "wasserkuehlung": ["kuehler", "wk", "wasser"],
    "brenner": ["torch", "torche", "torcia", "schlauchpaket"],
    "fernbedienung": ["remote", "fernregler", "pedal", "fusspedal"],
    "drahtvorschub": ["dvs", "dvl", "koffer", "vorschub"],
    # Reinigung
    "reinigen": ["reinigung", "cleaner", "beizen", "anlauffarben", "putzen"],
    "cleaner": ["reinigen", "reinigung"],
    "elektrolyt": ["elektrolyte", "fluessigkeit", "r1", "rp1", "p1", "n1", "m1"],
    "signieren": ["beschriften", "markieren", "gravieren"],
    "polieren": ["glaenzen", "politur"],
    # französisch / italienisch
    "soudage": ["schweissen", "saldatura"],
    "nettoyage": ["reinigung", "pulizia"],
    "saldatura": ["schweissen", "soudage"],
    "pulizia": ["reinigung", "nettoyage"],
    "accessoires": ["zubehoer", "accessori"],
    "accessori": ["zubehoer", "accessoires"],
}


def norm(s):
    """Muss exakt der JS-Normalisierung in app.js entsprechen."""
    s = (s or "").lower()
    s = (s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
           .replace("ß", "ss").replace("à", "a").replace("â", "a").replace("é", "e")
           .replace("è", "e").replace("ê", "e").replace("î", "i").replace("ï", "i")
           .replace("ô", "o").replace("ù", "u").replace("û", "u").replace("ç", "c")
           .replace("’", " ").replace("'", " "))
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def search_index(lang):
    prods = []
    for p in C.P:
        cat = C.CAT_BY_ID[p["cat"]]
        m = R.MANIFEST.get(C.full_img(p["img"]))
        specs_txt = " ".join(f"{C.trK(lang, k)} {C.trV(lang, v)}"
                             for k, v in C.specRest(p).items())
        for t in C.specTables(lang, p):
            specs_txt += " " + " ".join(" ".join(r) for r in t["rows"])
            specs_txt += " " + " ".join(t["cols"])
        hl = C.highlightsOf(lang, p) or []
        feats = [C.featLabel(lang, k) for k in C.featOf(p)]
        mats = [C.matLabel(lang, m_) for m_ in C.matOf(p)]
        prods.append({
            "i": p["id"],
            "n": C.pName(lang, p),
            "d": C.pDesc(lang, p),
            "v": " · ".join(C.verfahrenOf(lang, p)),
            "c": C.catT(lang, cat),
            "s": C.subT(lang, p["sub"]),
            "u": C.u_prod(lang, p),
            "g": (f"/assets/img/{R.img_folder(m)}/{m['key']}-{R.img_step(m, 400)}.webp" if m
                  else C.REMOTE_IMG + C.full_img(p["img"])),
            # Suchtext nach Gewicht getrennt: Name / Typ / Rest
            "t1": norm(f"{C.pName(lang, p)} {p['name']} {p['id']}"),
            "t2": norm(f"{C.vtT(lang, p['vt'])} {C.subT(lang, p['sub'])} {C.catT(lang, cat)} {' '.join(mats)} {' '.join(feats)}"),
            "t3": norm(f"{C.pDesc(lang, p)} {specs_txt} {' '.join(hl)}"),
        })
    cats = []
    for c in C.CATS:
        cats.append({"n": C.catT(lang, c), "d": C.catD(lang, c), "u": C.u_cat(lang, c["id"]),
                     "t1": norm(C.catT(lang, c)), "t3": norm(C.catD(lang, c))})
        for s in c["subs"]:
            cats.append({"n": f"{C.subT(lang, s)} · {C.catT(lang, c)}", "d": "",
                         "u": C.u_sub(lang, c["id"], s),
                         "t1": norm(C.subT(lang, s)), "t3": norm(C.catT(lang, c))})
    procs = [{"n": pr["n"].get(lang) or pr["n"]["de"],
              "d": pr["d"].get(lang) or pr["d"]["de"],
              "u": C.u_page(lang, "processes"),
              "t1": norm(pr["n"].get(lang) or pr["n"]["de"]),
              "t3": norm(pr["d"].get(lang) or pr["d"]["de"])} for pr in C.PROC]
    dls = [{"n": d["t"].get(lang) or d["t"]["de"], "d": d["s"].get(lang) or d["s"]["de"],
            "u": d["u"], "t1": norm(d["t"].get(lang) or d["t"]["de"]),
            "t3": norm(d["s"].get(lang) or d["s"]["de"])} for d in C.DLS]

    # Vokabular für "Meinten Sie …"
    vocab = set()
    for it in prods + cats + procs + dls:
        for f in ("t1", "t2", "t3"):
            for w in it.get(f, "").split():
                if len(w) >= 3:
                    vocab.add(w)

    return {
        "lang": lang, "generated": TODAY,
        "products": prods, "cats": cats, "procs": procs, "dls": dls,
        "syn": {norm(k): [norm(x) for x in v] for k, v in SYNONYMS.items()},
        "vocab": sorted(vocab),
        "popular": ["HyperMIG", "WIG AC/DC", "Theta", "Cleaner", "Fahrwagen", "Plasma"],
    }


def products_json():
    """Öffentlicher, maschinenlesbarer Katalog – für Partner und KI-Crawler."""
    out = []
    for p in C.P:
        cat = C.CAT_BY_ID[p["cat"]]
        out.append({
            "id": p["id"],
            "sku": p["id"].upper(),
            "name": f"{C.BRAND} {p['name']}",
            "brand": C.BRAND,
            "type": {l: C.vtT(l, p["vt"]) for l in C.LANGS},
            "category": {l: C.catT(l, cat) for l in C.LANGS},
            "subcategory": {l: C.subT(l, p["sub"]) for l in C.LANGS},
            "description": {l: C.pDesc(l, p) for l in C.LANGS},
            "highlights": {l: C.highlightsOf(l, p) or [] for l in C.LANGS},
            "options": {l: [{"name": o["t"], "note": o.get("s", "")}
                            for o in C.optionsOf(l, p)] for l in C.LANGS},
            "specs": {l: {C.trK(l, k): C.trV(l, v) for k, v in C.specRest(p).items()}
                      for l in C.LANGS},
            # Technische Daten wie beim Hersteller: Spalten = Modellvarianten
            "techdata": {l: [{"title": t["title"], "note": t["note"],
                              "columns": t["cols"],
                              "rows": [{"label": r[0],
                                        "values": dict(zip(t["cols"], r[1:]))}
                                       for r in t["rows"]]}
                             for t in C.specTables(l, p)] for l in C.LANGS},
            "materials": [C.matLabel("de", m) for m in C.matOf(p)],
            "price": {"model": "on-request", "currency": "CHF",
                      "note": {l: C.t(l, "poa") for l in C.LANGS}},
            # Nicht "InStock". Diese Datei ist der Katalog fuer Antwort-
            # maschinen - was hier steht, geben sie weiter. "InStock" ist ein
            # Begriff aus schema.org und heisst: liegt am Lager. VES-TECH
            # bestellt bei MAHE, sobald eine Anfrage kommt; auf jeder
            # Produktseite steht deshalb "Verfuegbarkeit: Auf Anfrage". Die
            # Datei behauptete das Gegenteil, in derselben Form wie ein Haendler
            # mit vollem Lager. Jetzt sagt sie dasselbe wie die Seite.
            "availability": {"model": "on-request",
                             "note": {l: C.t(l, "avail_val") for l in C.LANGS}},
            "image": R.img_abs(p["img"], 1000),
            "url": {l: C.abs_url(C.u_prod(l, p)) for l in C.LANGS},
        })
    return {
        "@context": "https://schema.org",
        "generated": TODAY,
        "seller": {"name": C.COMPANY["name"], "url": C.SITE + "/",
                   "email": C.COMPANY["email"], "telephone": C.COMPANY["phone"],
                   "address": f"{C.COMPANY['street']}, {C.COMPANY['zip']} {C.COMPANY['city']}, "
                              f"{C.COMPANY['country_name']}"},
        "license": "Produktdaten und Bilder: MAHE GmbH. Wiedergabe durch VES-TECH Swiss als Schweizer Partner.",
        "count": len(out),
        "products": out,
    }


# --------------------------------------------------------------------------
# sitemap / robots / llms
# --------------------------------------------------------------------------

# Adressen, die es einmal gab und heute nicht mehr.
#
# Am 04.08.2026 verschwanden fuenf Seiten je Sprache aus der Sitemap, ohne dass
# an ihre Stelle etwas trat. Google hatte sieben davon bereits gecrawlt und
# meldet sie seither unter "Nicht gefunden (404)". Eine 404 ist kein Beinbruch,
# aber sie verschenkt: wer dort landet, ist weg, und was die Seite an Ansehen
# gesammelt hatte, verfaellt.
#
# GitHub Pages kennt keine serverseitige Umleitung. Der Weg, den Google fuer
# statische Angebote ausdruecklich nennt, ist eine Seite mit meta-refresh auf
# 0 Sekunden und einem canonical auf das Ziel; sie wird wie eine dauerhafte
# Umleitung gewertet. Kein noindex - das wuerde verhindern, dass die Adresse
# mit dem Ziel zusammengefuehrt wird.
#
# Das Ziel ist jeweils die Seite, auf der die Auskunft heute steht - nicht
# blind die Startseite. Eine Umleitung auf etwas Unpassendes wertet Google als
# "soft 404" und behandelt sie wie den Fehler, den sie ersetzen sollte.
WEGGEFALLEN = [
    ({"de": "/produkte/zubehoer/s25/",
      "fr": "/fr/produits/accessoires/s25/",
      "it": "/it/prodotti/accessori/s25/"},
     lambda l: C.u_sub(l, "zubehoer", "Plasmabrenner"),
     "Der S 25 ist fest in der Theta 40 verbaut; die Plasmabrenner stehen jetzt zusammen"),

    ({"de": "/produkte/zubehoer/massekabel-16/",
      "fr": "/fr/produits/accessoires/massekabel-16/",
      "it": "/it/prodotti/accessori/massekabel-16/"},
     lambda l: C.u_prod(l, C.BY_ID["massekabel"]),
     "Die 16-mm2-Ausfuehrung steht bei den Massekabeln"),

    ({"de": "/produkte/zubehoer/montagesatz-mlf100/",
      "fr": "/fr/produits/accessoires/montagesatz-mlf100/",
      "it": "/it/prodotti/accessori/montagesatz-mlf100/"},
     lambda l: C.u_prod(l, C.BY_ID["mlf100"]),
     "Der Montagesatz gehoert zum Lieferumfang des MLF 100 und steht dort"),

    ({"de": "/produkte/zubehoer/reinigungspinselstaender/",
      "fr": "/fr/produits/accessoires/reinigungspinselstaender/",
      "it": "/it/prodotti/accessori/reinigungspinselstaender/"},
     lambda l: C.u_prod(l, C.BY_ID["mlf100"]),
     "Der Pinselstaender gehoert zum Lieferumfang des MLF 100"),

    ({"de": "/produkte/zubehoer/cleaner-zubehoer/",
      "fr": "/fr/produits/accessoires/accessoires-nettoyage/",
      "it": "/it/prodotti/accessori/accessori-pulizia/"},
     lambda l: C.u_cat(l, "reinigung"),
     "Die Unterkategorie ist aufgeloest; die Geraete stehen bei der Reinigungstechnik"),
]


def umleitungen():
    """Schreibt fuer jede weggefallene Adresse eine Umleitungsseite."""
    n = 0
    for alte, ziel, grund in WEGGEFALLEN:
        for lang, pfad in alte.items():
            z = C.abs_url(ziel(lang))
            html = (f'<!doctype html>\n<html lang="{C.EX[lang]["hreflang"]}">\n<head>\n'
                    f'<meta charset="utf-8">\n'
                    f'<meta name="vt-umleitung" content="{z}">\n'
                    f'<meta http-equiv="refresh" content="0; url={z}">\n'
                    f'<link rel="canonical" href="{z}">\n'
                    f'<title>{C.t(lang, "redirect_title")}</title>\n'
                    # Kein noindex: die Adresse soll mit dem Ziel zusammengefuehrt
                    # werden, nicht verschwinden. meta-refresh und canonical sagen
                    # Google, wohin; ein noindex daneben wuerde dem widersprechen.
                    f'</head>\n<body>\n'
                    f'<p>{C.t(lang, "redirect_text")} <a href="{z}">{z}</a></p>\n'
                    f'<!-- {grund} -->\n</body>\n</html>\n')
            write(pfad, html)
            n += 1
    return n


# Wann sich eine Seite wirklich zuletzt geaendert hat.
#
# Bis zum 14.08.2026 trug jede der 339 Adressen in der Sitemap das Datum des
# letzten Builds - also taeglich dasselbe, fuer alle. Eine Suchmaschine lernt
# daraus schnell, dass die Angabe nichts bedeutet, und ignoriert sie. Genau
# dann faellt der einzige Hinweis weg, mit dem sich sagen laesst, welche von
# 339 Adressen sich lohnt: bei "Gefunden - zurzeit nicht indexiert" (am
# 14.08.2026 waren das 199 Seiten) entscheidet der Crawler selbst, und ohne
# Anhaltspunkt entscheidet er gegen die meisten.
#
# Jetzt merkt sich der Build je Adresse den Inhalt und das Datum. Aendert sich
# der Inhalt, wird das Datum neu gesetzt; sonst bleibt es stehen. Der Stand
# liegt in build/lastmod.json und gehoert ins Repository - sonst faengt jeder
# Rechner und jeder CI-Lauf wieder bei heute an.
#
# Zwei Feinheiten:
#   * Die ?v=-Anhaengsel an CSS und JS werden vor dem Vergleich entfernt. Sonst
#     galten nach jeder Stiländerung alle 339 Seiten als geaendert.
#   * Beim ersten Lauf gibt es noch keinen Stand. Statt alles auf heute zu
#     setzen, kommt das Datum dann aus der Versionsgeschichte - das letzte Mal,
#     als die erzeugte Datei sich wirklich geaendert hat.
LASTMOD_DATEI = C.BUILD / "lastmod.json"
_VERSIONSANHANG = re.compile(r"\?v=[0-9a-f]{6,}")


def _inhaltskennung(pfad):
    f = OUT / (pfad.strip("/") + "/index.html" if pfad.endswith("/") else pfad.lstrip("/"))
    if pfad == "/":
        f = OUT / "index.html"
    if not f.exists():
        return None
    roh = _VERSIONSANHANG.sub("", f.read_text("utf-8"))
    return hashlib.sha256(roh.encode("utf-8")).hexdigest()[:16]


def _datum_aus_git(pfad):
    f = OUT / (pfad.strip("/") + "/index.html" if pfad.endswith("/") else pfad.lstrip("/"))
    if pfad == "/":
        f = OUT / "index.html"
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%ad", "--date=short", "--", str(f)],
                           capture_output=True, text=True, cwd=str(C.ROOT), timeout=20)
        d = r.stdout.strip()
        return d if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) else TODAY
    except Exception:
        return TODAY


def lastmod_pflegen(pfade):
    """Liefert {pfad: datum} und schreibt den Stand fort."""
    alt = {}
    if LASTMOD_DATEI.exists():
        try:
            alt = json.loads(LASTMOD_DATEI.read_text("utf-8"))
        except Exception:
            alt = {}
    erststart = not alt
    neu, geaendert = {}, 0
    for pfad in pfade:
        kennung = _inhaltskennung(pfad)
        if kennung is None:
            neu[pfad] = {"h": "", "d": TODAY}
            continue
        vorher = alt.get(pfad)
        if vorher and vorher.get("h") == kennung:
            neu[pfad] = vorher                      # unveraendert: Datum bleibt
        elif vorher:
            neu[pfad] = {"h": kennung, "d": TODAY}  # wirklich geaendert
            geaendert += 1
        else:
            datum = _datum_aus_git(pfad) if erststart else TODAY
            neu[pfad] = {"h": kennung, "d": datum}
            geaendert += 0 if erststart else 1
    LASTMOD_DATEI.write_text(json.dumps(neu, ensure_ascii=False, indent=1,
                                        sort_keys=True) + "\n", "utf-8")
    return {k: v["d"] for k, v in neu.items()}, geaendert, erststart


def sitemap(entries, daten):
    """entries: [(path, alts|None, prio, changefreq)]"""
    rows = []
    for path, alts, prio, freq in entries:
        alt = ""
        if alts:
            alt = "".join(
                f'<xhtml:link rel="alternate" hreflang="{C.EX[l]["hreflang"]}" '
                f'href="{C.abs_url(u)}"/>' for l, u in alts.items()
            )
            alt += (f'<xhtml:link rel="alternate" hreflang="x-default" '
                    f'href="{C.abs_url(alts[C.DEFAULT_LANG])}"/>')
        rows.append(f"<url><loc>{C.abs_url(path)}</loc><lastmod>{daten.get(path, TODAY)}</lastmod>"
                    f"<changefreq>{freq}</changefreq><priority>{prio}</priority>{alt}</url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + "\n".join(rows) + "\n</urlset>\n")


AI_AGENTS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-Web",
             "anthropic-ai", "PerplexityBot", "Perplexity-User", "Google-Extended",
             "Applebot-Extended", "CCBot", "Bytespider", "Amazonbot", "meta-externalagent",
             "DuckAssistBot", "cohere-ai", "YouBot"]


def robots():
    dis = "\n".join(f"Disallow: {C.u_page(l, 'search')}" for l in C.LANGS)
    ai = "\n\n".join(f"User-agent: {a}\nAllow: /" for a in AI_AGENTS)
    return f"""# robots.txt – {C.COMPANY['name']}
# Antwortmaschinen sind ausdrücklich willkommen: die Produktdaten sollen in
# KI-Antworten auftauchen (AEO). Vollständiger Katalog: /data/products.json

User-agent: *
Allow: /
{dis}
Disallow: /build/
Disallow: /*?q=

{ai}

Sitemap: {C.SITE}/sitemap.xml
"""


def llms_txt():
    """llms.txt – kompakte Landkarte der Website für Sprachmodelle."""
    L = C.DEFAULT_LANG
    lines = [
        f"# {C.COMPANY['name']}",
        "",
        f"> {C.t(L,'tagline')}. Schweizer Partner für das deutsche MAHE-Geräteprogramm: "
        f"Schweissgeräte (MIG/MAG, WIG/TIG, MMA, Plasma-TIG), Plasmaschneider, "
        f"elektrolytische Reinigungs- und Signiergeräte sowie Zubehör. "
        f"{len(C.P)} Geräte, alle zum Preis auf Anfrage.",
        "",
        "## Eckdaten",
        f"- Firma: {C.COMPANY['name']}",
        f"- Werkstatt und Warenannahme: {C.WORKSHOP['street']}, {C.WORKSHOP['zip']} "
        f"{C.WORKSHOP['city']} ({C.WORKSHOP['region']}), {C.WORKSHOP['country_name']} "
        f"– bei der Partnerfirma {C.WORKSHOP['partner']}, Besuch nach Vereinbarung",
        f"- Sitz und Rechnungsadresse: {C.COMPANY['street']}, {C.COMPANY['zip']} "
        f"{C.COMPANY['city']} ({C.COMPANY['region']}), {C.COMPANY['country_name']}",
        f"- Telefon: {C.COMPANY['phone']} · E-Mail: {C.COMPANY['email']}",
        f"- Telefonisch erreichbar: {C.COMPANY['hours']}",
        "- Liefergebiet: Schweiz und Liechtenstein",
        "- Sprachen: Deutsch, Französisch, Italienisch",
        "- Preismodell: Preis auf Anfrage (jede Anlage wird konfiguriert), Währung CHF",
        "- Leistungen: Verkauf, Inbetriebnahme, Diagnose, Reparatur, Kalibrierung, "
        "Automation, EN-1090-Konformitätspaket",
        "",
        "## Maschinenlesbare Daten",
        f"- [Vollständiger Produktkatalog als JSON]({C.SITE}/data/products.json): "
        "alle Geräte mit Spezifikationen in DE/FR/IT",
        f"- [Volltext für Sprachmodelle]({C.SITE}/llms-full.txt): alle Produktbeschreibungen "
        "und technischen Daten als Fliesstext",
        f"- [Sitemap]({C.SITE}/sitemap.xml)",
        "",
        "## Kategorien",
    ]
    for c in C.CATS:
        n = len(C.products_of(c["id"]))
        lines.append(f"- [{C.catT(L,c)}]({C.abs_url(C.u_cat(L, c['id']))}): {C.catD(L,c)} "
                     f"({n} Geräte: {', '.join(C.subT(L,s) for s in c['subs'])})")
    lines += ["", "## Geräte"]
    for c in C.CATS:
        lines.append(f"### {C.catT(L,c)}")
        for p in C.products_of(c["id"]):
            lines.append(f"- [{C.BRAND} {p['name']}]({C.abs_url(C.u_prod(L, p))}): "
                         f"{C.pDesc(L,p)} ({C.vtT(L, p['vt'])})")
        lines.append("")
    lines += ["## Verfahren"]
    for pr in C.PROC:
        lines.append(f"- {pr['n']['de']}: {pr['d']['de']}")
    lines += ["", "## Häufige Fragen"]
    for q in C.EX[L]["faq"]:
        lines.append(f"- [{q['q']}]({C.abs_url(C.u_page(L,'faq'))})")
    lines += ["", "## Weitere Sprachen",
              f"- Français: {C.abs_url(C.u_home('fr'))}",
              f"- Italiano: {C.abs_url(C.u_home('it'))}", ""]
    return "\n".join(lines)


def llms_full():
    """llms-full.txt – der komplette zitierfähige Inhalt in einer Datei."""
    L = C.DEFAULT_LANG
    out = [f"# {C.COMPANY['name']} — vollständiger Produkt- und Wissensauszug",
           f"Stand: {TODAY}. Quelle: {C.SITE}",
           "",
           f"{C.COMPANY['name']} in {C.WORKSHOP['city']} ({C.WORKSHOP['region']}, "
           f"{C.WORKSHOP['country_name']}) ist der Schweizer Partner für das MAHE-Geräteprogramm. "
           f"Werkstatt und Warenannahme: {C.WORKSHOP['street']}, {C.WORKSHOP['zip']} "
           f"{C.WORKSHOP['city']}, bei der Partnerfirma {C.WORKSHOP['partner']}, Besuch nach "
           f"Vereinbarung. Sitz und Rechnungsadresse: {C.COMPANY['street']}, "
           f"{C.COMPANY['zip']} {C.COMPANY['city']}. "
           f"Telefon {C.COMPANY['phone']}, E-Mail {C.COMPANY['email']}, "
           f"telefonisch erreichbar {C.COMPANY['hours']}. Alle Geräte werden zum Preis auf Anfrage "
           f"angeboten, weil jede Anlage nach Werkstoff, Blechdicke, Kühlung und Zubehör "
           f"konfiguriert wird.",
           "", "---", ""]
    for c in C.CATS:
        out += [f"## {C.catT(L,c)}", C.catD(L, c), ""]
        for p in C.products_of(c["id"]):
            out.append(f"### {C.BRAND} {p['name']}")
            out.append(f"URL: {C.abs_url(C.u_prod(L, p))}")
            out.append(f"Kategorie: {C.catT(L,c)} / {C.subT(L, p['sub'])} · Typ: {C.vtT(L, p['vt'])} "
                       f"· Art.-Nr.: {p['id'].upper()} · Preis: auf Anfrage (CHF)")
            out.append(C.pDesc(L, p))
            hl = C.highlightsOf(L, p)
            if hl:
                out.append("Besonderheiten: " + "; ".join(hl) + ".")
            opt = C.optionsOf(L, p)
            if opt:
                out.append("Optionen: " + "; ".join(
                    o["t"] + (f" ({o['s']})" if o.get("s") else "") for o in opt) + ".")
            rest = C.specRest(p)
            if rest:
                out.append("Ausstattung: " + "; ".join(
                    f"{C.trK(L,k)}: {C.trV(L,v)}" for k, v in rest.items()) + ".")
            # Als Markdown-Tabelle – die lesen Sprachmodelle spaltenrichtig,
            # eine Aufzaehlung wuerde die Varianten vermischen.
            for t in C.specTables(L, p):
                head = f" – {t['title']}" if t["title"] else ""
                out += ["", f"Technische Daten{head}:", "",
                        "| " + C.t(L, "spec_model") + " | " + " | ".join(t["cols"]) + " |",
                        "|" + " --- |" * (len(t["cols"]) + 1)]
                out += ["| " + " | ".join(r) + " |" for r in t["rows"]]
                if t["note"]:
                    out.append(f"*: {t['note']}")
                out.append("")
            mats = C.matOf(p)
            if mats:
                out.append("Werkstoffe: " + ", ".join(C.matLabel(L, m) for m in mats) + ".")
            acc = C.relatedAcc(p)
            if acc:
                out.append("Passendes Zubehör: " + ", ".join(C.BY_ID[a]["name"] for a in acc) + ".")
            out.append("")
    out += ["---", "", "## Schweissverfahren von MAHE", ""]
    for pr in C.PROC:
        out.append(f"### {pr['n']['de']}")
        out.append(pr["d"]["de"])
        out.append("")
    out += ["---", "", "## Häufige Fragen und Antworten", ""]
    for q in C.EX[L]["faq"]:
        out.append(f"### {q['q']}")
        out.append(q["a"])
        out.append("")
    return "\n".join(out)


def webmanifest():
    return json.dumps({
        "name": C.COMPANY["name"] + " — MAHE Schweisstechnik",
        "short_name": "VES-TECH",
        "description": C.t("de", "home_desc"),
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#ECEAE5",
        "theme_color": "#E0511A",
        "lang": "de-CH",
        "icons": [
            {"src": "/assets/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/assets/icons/icon-512.png", "sizes": "512x512", "type": "image/png",
             "purpose": "any"},
            {"src": "/assets/icons/favicon.svg", "sizes": "any", "type": "image/svg+xml"},
        ],
    }, ensure_ascii=False, indent=1)


# --------------------------------------------------------------------------
# Hauptlauf
# --------------------------------------------------------------------------

def main():
    for d in MANAGED_DIRS:
        p = OUT / d
        if p.exists():
            shutil.rmtree(p)

    entries = []   # für die sitemap

    for lang in C.LANGS:
        u, h = PG.page_home(lang);      write(u, h); entries.append((u, C.alternates("home"), "1.0", "weekly"))
        u, h = PG.page_products(lang);  write(u, h); entries.append((u, C.alternates("products"), "0.9", "weekly"))
        # Produkt-URLs vorab, um Zusammenstoesse mit Unterkategorien zu erkennen.
        prod_urls = {C.u_prod(lang, p) for p in C.P}
        for c in C.CATS:
            u, h = PG.page_cat(lang, c)
            write(u, h); entries.append((u, C.alternates("cat", cat_id=c["id"]), "0.8", "weekly"))
            for s in c["subs"]:
                u, h = PG.page_cat(lang, c, s)
                # Die Unterkategorie "Plasma TIG" ergibt denselben Slug wie das
                # Produkt "plasma-tig" - beide wollten /produkte/schweissgeraete/
                # plasma-tig/. Geschrieben wurde zuletzt das Produkt, die
                # Kategorieseite ging verloren, und die URL stand zweimal in der
                # sitemap. Die Unterkategorie enthaelt genau dieses eine Geraet;
                # die Produktseite zeigt also ohnehin alles, was es dazu gibt.
                # Deshalb faellt hier die Kategorieseite aus, statt die
                # Produkt-URL zu aendern - die ist verlinkt und indexiert.
                if u in prod_urls:
                    continue
                write(u, h)
                entries.append((u, C.alternates("sub", cat_id=c["id"], sub=s), "0.7", "monthly"))
        for p in C.P:
            u, h = PG.page_product(lang, p)
            write(u, h); entries.append((u, C.alternates("prod", p=p), "0.8", "monthly"))
        for fn, key, prio in [(PG.page_processes, "processes", "0.6"),
                              (PG.page_downloads, "downloads", "0.5"),
                              (PG.page_contact, "contact", "0.7"),
                              (PG.page_faq, "faq", "0.7"),
                              # Wer steht dahinter: bei einem Einzelunternehmen
                              # eine der wichtigsten Seiten ueberhaupt, und sie
                              # fehlte bis zum 14.08.2026.
                              (PG.page_about, "about", "0.7")]:
            u, h = fn(lang)
            write(u, h); entries.append((u, C.alternates("page", key=key), prio, "monthly"))
        # Servicebereich: Uebersicht und drei Unterseiten. Hohe Prioritaet -
        # das ist die Leistung, die es nur hier gibt, und bisher hatte sie
        # keine eigene Seite.
        u, h = PG.page_service(lang)
        write(u, h); entries.append((u, C.alternates("service"), "0.8", "monthly"))
        for skey in C.SERVICE_KEYS:
            u, h = PG.page_service(lang, skey)
            write(u, h)
            entries.append((u, C.alternates("service", key=skey), "0.8", "monthly"))
        u, h = PG.page_search(lang); write(u, h)                       # noindex → nicht in sitemap
        for kind in ("imprint", "privacy", "terms"):
            u, h = PG.page_legal(lang, kind)
            write(u, h)
            if "noindex" not in PG.LEGAL[kind][2]:
                entries.append((u, C.alternates("page", key=kind), "0.3", "yearly"))

        (C.DATA / f"search-{lang}.json").write_text(
            json.dumps(search_index(lang), ensure_ascii=False, separators=(",", ":")), "utf-8")

    u, h = PG.page_404(); write(u, h)

    stand, geaendert, erst = lastmod_pflegen([e[0] for e in entries])
    write("/sitemap.xml", sitemap(entries, stand))
    if erst:
        print(f"\u2713 sitemap: lastmod je Seite, erstmalig aus der Versionsgeschichte")
    else:
        print(f"\u2713 sitemap: lastmod je Seite, {geaendert} Seiten heute geaendert")
    write("/robots.txt", robots())
    write("/llms.txt", llms_txt())
    write("/llms-full.txt", llms_full())
    write("/site.webmanifest", webmanifest())
    cname = OUT / "CNAME"
    if C.EMIT_CNAME:
        write("/CNAME", C.CUSTOM_DOMAIN + "\n")
    elif cname.exists():
        cname.unlink()          # sonst zeigt Pages weiter auf die tote Domain
    write("/.nojekyll", "")
    if C.INDEXNOW_KEY:
        write(f"/{C.INDEXNOW_KEY}.txt", C.INDEXNOW_KEY)
    if C.GOOGLE_VERIFY_FILE:
        write("/" + C.GOOGLE_VERIFY_FILE,
              "google-site-verification: " + C.GOOGLE_VERIFY_FILE + "\n")
    n_um = umleitungen()
    print(f"\u2713 {n_um} Umleitungen fuer weggefallene Adressen")
    (C.DATA / "products.json").write_text(
        json.dumps(products_json(), ensure_ascii=False, indent=1), "utf-8")

    html_pages = [p for p in written if p.endswith("/") or p.endswith(".html")]
    print(f"✓ {len(html_pages)} HTML-Seiten, {len(entries)} in der sitemap")
    print(f"✓ Suchindex: {', '.join('search-%s.json' % l for l in C.LANGS)}")
    print(f"✓ data/products.json  ({len(C.P)} Produkte × {len(C.LANGS)} Sprachen)")
    # security.txt nach RFC 9116. Der Standardweg, eine Sicherheitsmeldung
    # anzunehmen: wer eine Luecke findet, sucht genau dort. Ohne die Datei
    # landet ein Hinweis im besten Fall im Kontaktformular, im schlechteren
    # gar nicht. Das Ablaufdatum ist Pflicht und darf laut RFC hoechstens ein
    # Jahr in der Zukunft liegen - deshalb wird es bei jedem Build neu
    # gesetzt und kann nicht veralten.
    ablauf = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
    sec = (f"Contact: mailto:{C.COMPANY['email']}\n"
           f"Contact: tel:{C.COMPANY['phone_href']}\n"
           f"Expires: {ablauf}T00:00:00.000Z\n"
           "Preferred-Languages: de, en, cs\n"
           f"Canonical: {C.SITE}/.well-known/security.txt\n"
           f"Policy: {C.SITE}/{C.SEG['de']['imprint']}/\n")
    write("/.well-known/security.txt", sec)
    print(f"✓ .well-known/security.txt  (gueltig bis {ablauf})")

    print(f"✓ llms.txt / llms-full.txt / robots.txt / sitemap.xml")

    # Ohne Schluessel geht keine Anfrage ueber den Formulardienst. Die Seite
    # bleibt bedienbar - app.js oeffnet stattdessen einen Kasten mit dem
    # fertigen Text und der Adresse -, aber der Besucher braucht dann ein
    # eingerichtetes Mailprogramm. Am 12.08.2026 nachgemessen: mit Schluessel
    # geht ein POST an api.web3forms.com/submit mit allen Feldern raus, ohne
    # Schluessel greift der Rueckfall. Es fehlt also wirklich nur der Wert.
    #
    # Kein Fehler, sondern ein Hinweis: der Build soll deswegen nicht
    # abbrechen. Aber er soll es bei jedem Lauf sagen, hier und im Protokoll
    # von GitHub Actions - sonst faellt es niemandem mehr auf.
    if not C.web3forms_key():
        print("\n! Kein Web3Forms-Schluessel gesetzt: die Formulare fallen auf "
              "mailto zurueck.\n"
              "  Schluessel holen auf https://web3forms.com (Adresse eingeben, "
              "er kommt per Mail),\n"
              "  dann entweder\n"
              "      gh secret set WEB3FORMS_KEY        (fuer den Deploy)\n"
              "  oder build/config.local.json anlegen:  "
              '{"web3forms_key": "…"}   (nur lokal, nicht im Git)')


if __name__ == "__main__":
    main()
