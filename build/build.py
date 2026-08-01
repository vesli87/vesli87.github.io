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
import json
import pathlib
import re
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import core as C      # noqa: E402
import pages as PG    # noqa: E402
import render as R    # noqa: E402

OUT = C.ROOT
TODAY = datetime.date.today().isoformat()

# Verzeichnisse, die der Build vollständig verwaltet (werden vorher geleert)
MANAGED_DIRS = ["produkte", "fr", "it", "verfahren", "downloads", "kontakt",
                "faq", "suche", "impressum", "datenschutz"]

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
        feats = [C.featLabel(lang, k) for k in C.deriveFeat(p)]
        mats = [C.matLabel(lang, m_) for m_ in C.matOf(p)]
        prods.append({
            "i": p["id"],
            "n": p["name"],
            "d": C.pDesc(lang, p),
            "v": p["vt"],
            "c": C.catT(lang, cat),
            "s": C.subT(lang, p["sub"]),
            "u": C.u_prod(lang, p),
            "g": f"/assets/img/p/{m['key']}-400.webp" if m else C.REMOTE_IMG + C.full_img(p["img"]),
            # Suchtext nach Gewicht getrennt: Name / Typ / Rest
            "t1": norm(f"{p['name']} {p['id']}"),
            "t2": norm(f"{p['vt']} {C.subT(lang, p['sub'])} {C.catT(lang, cat)} {' '.join(mats)} {' '.join(feats)}"),
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
            "type": p["vt"],
            "category": {l: C.catT(l, cat) for l in C.LANGS},
            "subcategory": {l: C.subT(l, p["sub"]) for l in C.LANGS},
            "description": {l: C.pDesc(l, p) for l in C.LANGS},
            "highlights": {l: C.highlightsOf(l, p) or [] for l in C.LANGS},
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
            "availability": "InStock",
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

def sitemap(entries):
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
        rows.append(f"<url><loc>{C.abs_url(path)}</loc><lastmod>{TODAY}</lastmod>"
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
        f"- Firma: {C.COMPANY['name']}, {C.COMPANY['street']}, {C.COMPANY['zip']} "
        f"{C.COMPANY['city']} ({C.COMPANY['region']}), {C.COMPANY['country_name']}",
        f"- Telefon: {C.COMPANY['phone']} · E-Mail: {C.COMPANY['email']}",
        f"- Öffnungszeiten: {C.COMPANY['hours']}",
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
                         f"{C.pDesc(L,p)} ({p['vt']})")
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
           f"{C.COMPANY['name']} in {C.COMPANY['city']} ({C.COMPANY['region']}, "
           f"{C.COMPANY['country_name']}) ist der Schweizer Partner für das MAHE-Geräteprogramm. "
           f"Adresse: {C.COMPANY['street']}, {C.COMPANY['zip']} {C.COMPANY['city']}. "
           f"Telefon {C.COMPANY['phone']}, E-Mail {C.COMPANY['email']}, "
           f"Öffnungszeiten {C.COMPANY['hours']}. Alle Geräte werden zum Preis auf Anfrage "
           f"angeboten, weil jede Anlage nach Werkstoff, Blechdicke, Kühlung und Zubehör "
           f"konfiguriert wird.",
           "", "---", ""]
    for c in C.CATS:
        out += [f"## {C.catT(L,c)}", C.catD(L, c), ""]
        for p in C.products_of(c["id"]):
            out.append(f"### {C.BRAND} {p['name']}")
            out.append(f"URL: {C.abs_url(C.u_prod(L, p))}")
            out.append(f"Kategorie: {C.catT(L,c)} / {C.subT(L, p['sub'])} · Typ: {p['vt']} "
                       f"· Art.-Nr.: {p['id'].upper()} · Preis: auf Anfrage (CHF)")
            out.append(C.pDesc(L, p))
            hl = C.highlightsOf(L, p)
            if hl:
                out.append("Besonderheiten: " + "; ".join(hl) + ".")
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
        for c in C.CATS:
            u, h = PG.page_cat(lang, c)
            write(u, h); entries.append((u, C.alternates("cat", cat_id=c["id"]), "0.8", "weekly"))
            for s in c["subs"]:
                u, h = PG.page_cat(lang, c, s)
                write(u, h)
                entries.append((u, C.alternates("sub", cat_id=c["id"], sub=s), "0.7", "monthly"))
        for p in C.P:
            u, h = PG.page_product(lang, p)
            write(u, h); entries.append((u, C.alternates("prod", p=p), "0.8", "monthly"))
        for fn, key, prio in [(PG.page_processes, "processes", "0.6"),
                              (PG.page_downloads, "downloads", "0.5"),
                              (PG.page_contact, "contact", "0.7"),
                              (PG.page_faq, "faq", "0.7")]:
            u, h = fn(lang)
            write(u, h); entries.append((u, C.alternates("page", key=key), prio, "monthly"))
        u, h = PG.page_search(lang); write(u, h)                       # noindex → nicht in sitemap
        for kind in ("imprint", "privacy"):
            u, h = PG.page_legal(lang, kind); write(u, h)              # noindex

        (C.DATA / f"search-{lang}.json").write_text(
            json.dumps(search_index(lang), ensure_ascii=False, separators=(",", ":")), "utf-8")

    u, h = PG.page_404(); write(u, h)

    write("/sitemap.xml", sitemap(entries))
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
    (C.DATA / "products.json").write_text(
        json.dumps(products_json(), ensure_ascii=False, indent=1), "utf-8")

    html_pages = [p for p in written if p.endswith("/") or p.endswith(".html")]
    print(f"✓ {len(html_pages)} HTML-Seiten, {len(entries)} in der sitemap")
    print(f"✓ Suchindex: {', '.join('search-%s.json' % l for l in C.LANGS)}")
    print(f"✓ data/products.json  ({len(C.P)} Produkte × {len(C.LANGS)} Sprachen)")
    print(f"✓ llms.txt / llms-full.txt / robots.txt / sitemap.xml")


if __name__ == "__main__":
    main()
