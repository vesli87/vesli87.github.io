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
import html
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
        # Umleitungsseiten sind keine Seiten im Sinne dieser Pruefung: sie haben
        # absichtlich kein canonical auf sich selbst, keine hreflang-Gruppe und
        # kein JSON-LD. Sie stehen an Adressen, die es einmal gab, und schicken
        # weiter. Erkennbar an der Markierung, die build.py::umleitungen setzt.
        if '<meta name="vt-umleitung"' in f.read_text("utf-8")[:400]:
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


def gedankenstriche():
    """Regel 3a: kein Gedankenstrich im sichtbaren Text.

    Der Inhaber hat sie am 03.09.2026 entschieden und dafuer sogar das
    Herobild retuschieren lassen. Trotzdem standen am 10.09.2026 wieder 144
    Gedankenstriche auf 129 der 377 Seiten - allein der Hinweis "Passt zu"
    brachte drei davon auf je 37 Seiten. Eine Regel, die niemand nachmisst,
    haelt keine zwei Wochen.

    Erlaubt bleibt der Bis-Strich zwischen Messwerten, Zeiten und Verweisen
    ("10 - 420 A", "Mo-Do", "Ziff. 2-4 UWG") - dort ist der Strich kein
    Satzzeichen, sondern Teil der Angabe.
    """
    ged = re.compile(r"(?<=\S)\s[\u2013\u2014]\s(?=\S)")
    bis = re.compile(r"\d\s*[\u2013\u2014]\s*\d"
                     r"|\d\s*(?:Hz|kHz|A|V|W|mm|kg|mm\u00b2|\u00b0C)\s*[\u2013\u2014]\s*\d")
    for f in all_pages():
        roh = f.read_text("utf-8")
        ohne = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", roh, flags=re.S)
        text = html.unescape(re.sub(r"<[^>]+>", " ", ohne))
        for m in ged.finditer(bis.sub(" ", text)):
            i = m.start()
            stelle = " ".join(text[max(0, i - 40):i + 40].split())
            err(f"{path_of(f)}: Gedankenstrich im sichtbaren Text (Regel 3a) - "
                f"…{stelle}…")


def bildverweise():
    """Jeder Bildverweis auf die eigene Domain muss eine Datei treffen.

    check.py prueft seit jeher die <img>-Tags. Bilder stehen aber auch dort,
    wo kein <img> ist: in og:image und twitter:image, als Product.image im
    JSON-LD, als data-img an der Anfrageliste, als "image" in products.json
    und als "g" in den drei Suchindizes. Diese Stellen bauen ihre Adresse
    ueber render.img_abs, nicht ueber img_tag.

    Am 10.09.2026 gingen genau sie kaputt: die Rubrik Occasion brachte einen
    dritten Bildordner, img_tag wurde nachgezogen, img_folder nicht. 50
    Adressen zeigten auf assets/img/panels/plasmafix-… , alle live 404 - und
    kein Pruefer merkte es, weil auf den Seiten selbst die <img>-Tags stimmten.
    """
    def aufloesen(u):
        if "ves-tech.ch/assets/img/" in u:
            u = u.split("ves-tech.ch")[-1]
        if not u.startswith("/assets/img/"):
            return None
        return C.ROOT / u.split("?")[0].lstrip("/")

    def pruef(u, wo):
        f = aufloesen(u)
        if f is not None and not f.exists():
            err(f"{wo}: Bildverweis zeigt ins Leere - {u}")

    for f in all_pages():
        t = f.read_text("utf-8")
        wo = path_of(f)
        for m in re.finditer(
                r'(?:property|name)="(?:og:image|twitter:image)" content="([^"]+)"', t):
            pruef(m.group(1), wo)
        for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', t, re.S):
            for u in re.findall(r'"(https://www\.ves-tech\.ch/assets/img/[^"]+)"', m.group(1)):
                pruef(u, wo)
        for u in re.findall(r'data-img="([^"]+)"', t):
            pruef(u, wo)

    pj = C.ROOT / "data/products.json"
    if pj.exists():
        for e in (json.loads(pj.read_text("utf-8")).get("products") or []):
            for k in ("image", "g"):
                if e.get(k):
                    pruef(e[k], "data/products.json")
    for l in C.LANGS:
        sf = C.ROOT / f"data/search-{l}.json"
        if not sf.exists():
            continue
        for e in json.loads(sf.read_text("utf-8")):
            if isinstance(e, dict) and e.get("g"):
                pruef(e["g"], f"data/search-{l}.json")


def fremdmarken():
    """Auf der Seite eines Fremdfabrikats darf die eigene Hausmarke nicht stehen.

    Der Generator war bis zum 10.09.2026 reiner MAHE-Katalog und setzte "MAHE"
    an 16 Stellen vor jeden Produktnamen - fuenfzehn davon im Quelltext, die
    sechzehnte im Einleitungssatz in build/i18n_extra.json. Mit der Rubrik
    Occasion kamen gebrauchte Oerlikon-Anlagen dazu; beim ersten Bauen stand
    auf jeder ihrer Seiten "PlasmaFix 51 von MAHE".

    Das ist keine Formsache. Wer ein Fremdfabrikat unter der Marke anbietet,
    deren Programm er sonst fuehrt, taeuscht ueber die betriebliche Herkunft
    der Ware - UWG Art. 3 Abs. 1 lit. b. Kopf, Menue und Fusszeile bleiben
    aussen vor: dass VES-TECH das MAHE-Programm fuehrt, gehoert dorthin.
    """
    import re as _re

    def _pruefe(url, marke, wo):
        f = C.ROOT / url.strip("/") / "index.html"
        if not f.exists():
            err(f"{wo}: Seite fehlt - {f}")
            return
        t = f.read_text("utf-8")
        i = t.find('<div class="detail">')
        if i < 0:
            i = t.find('<div class="cbar">')
        j = t.find("<footer")
        kern = t[i:j] if i >= 0 and j > i else t
        if C.BRAND in kern:
            err(f"{url}: '{C.BRAND}' steht im Inhalt einer {marke}-Seite")
        # Der ganze <head>, nicht drei ausgesuchte Felder. Geprueft wurde
        # zuerst nur title/description/og:title - og:description,
        # twitter:description und das JSON-LD blieben aussen vor, obwohl
        # dieselbe Vorlage sie fuellt.
        kopf = t[:t.find("</head>")] if "</head>" in t else t
        for feld, muster in (
                ("title", r"<title>(.*?)</title>"),
                ("description", r'<meta name="description" content="([^"]*)"'),
                ("og:title", r'<meta property="og:title" content="([^"]*)"'),
                ("og:description", r'<meta property="og:description" content="([^"]*)"'),
                ("twitter:title", r'<meta name="twitter:title" content="([^"]*)"'),
                ("twitter:description", r'<meta name="twitter:description" content="([^"]*)"')):
            m = _re.search(muster, kopf, _re.S)
            if m and m.group(1) and C.BRAND in m.group(1):
                err(f"{url}: '{C.BRAND}' steht im {feld} einer {marke}-Seite")
        # JSON-LD: jeder Knoten ausser Organization/LocalBusiness/Store und
        # WebSite - dort gehoert MAHE hin, das ist die Marke des Haendlers.
        for m in _re.finditer(r'<script type="application/ld\+json">(.*?)</script>', t, _re.S):
            try:
                d = json.loads(m.group(1))
            except Exception:
                continue
            for knoten in (d.get("@graph") or [d]):
                typ = knoten.get("@type")
                typen = typ if isinstance(typ, list) else [typ]
                if {"Organization", "LocalBusiness", "Store", "WebSite"} & set(typen):
                    continue
                if C.BRAND in json.dumps(knoten, ensure_ascii=False):
                    err(f"{url}: '{C.BRAND}' im JSON-LD-Knoten "
                        f"{'/'.join(str(x) for x in typen)} einer {marke}-Seite")

    # Kategorie- und Unterkategorieseiten, die kein MAHE fuehren
    for c in C.CATS:
        marke = C.catBrand(c["id"]) or "fremde"
        if marke == C.BRAND:
            continue
        for lang in C.LANGS:
            _pruefe(C.u_cat(lang, c["id"]), marke, c["id"])
            for s in c["subs"]:
                _pruefe(C.u_sub(lang, c["id"], s), marke, f'{c["id"]}/{s}')

    # Die erzeugten Datendateien mitpruefen. Sie sind kein Beiwerk: Antwort-
    # maschinen lesen products.json und llms.txt direkt, robots.txt verweist
    # ausdruecklich darauf. Beim ersten Bauen der Rubrik Occasion stand dort
    # "MAHE PlasmaFix 51" und "brand": "MAHE" - im HTML war da laengst alles
    # richtig, weil dieser Waechter nur Seiten ansah.
    fremd = [x for x in C.P if C.pBrand(x) != C.BRAND]
    if fremd:
        import json as _json
        namen = {x["name"] for x in fremd}
        pj = C.ROOT / "data/products.json"
        if pj.exists():
            for eintrag in (_json.loads(pj.read_text("utf-8")).get("products") or []):
                s = _json.dumps(eintrag, ensure_ascii=False)
                if any(n in s for n in namen) and C.BRAND in s:
                    err(f"data/products.json: '{C.BRAND}' bei einem Fremdfabrikat "
                        f"({eintrag.get('name')})")
        for l in C.LANGS:
            sf = C.ROOT / f"data/search-{l}.json"
            if not sf.exists():
                continue
            for e in _json.loads(sf.read_text("utf-8")):
                s = _json.dumps(e, ensure_ascii=False)
                if any(n in s for n in namen) and C.BRAND in s:
                    err(f"data/search-{l}.json: '{C.BRAND}' bei einem Fremdfabrikat")
        for datei in ("llms.txt", "llms-full.txt"):
            f = C.ROOT / datei
            if not f.exists():
                continue
            for zeile in f.read_text("utf-8").splitlines():
                if any(n in zeile for n in namen) and C.BRAND in zeile:
                    err(f"{datei}: '{C.BRAND}' bei einem Fremdfabrikat - {zeile.strip()[:70]}")

    for p in C.P:
        marke = C.pBrand(p)
        if marke == C.BRAND:
            continue
        for lang in C.LANGS:
            _pruefe(C.u_prod(lang, p), marke, p["id"])


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


# Gesammelte hreflang-Gruppen; nach dem Durchlauf gegeneinander geprueft.
hreflang_gruppen = {}


def main():
    pages = sorted(all_pages())
    if len(pages) < 200:
        err(f"nur {len(pages)} Seiten gefunden – Build unvollständig?")

    referenzen()
    fremdmarken()
    bildverweise()
    gedankenstriche()
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
        if p == "/404.html":
            # Die Fehlerseite traegt bewusst weder canonical noch hreflang:
            # sie wird fuer jede unbekannte Adresse ausgeliefert und wuerde
            # sonst von jeder vertippten Adresse behaupten, sie sei die
            # Startseite - im Widerspruch zum noindex daneben.
            if mc:
                err(f"{where}: hat ein canonical, sollte keines haben")
        elif not mc:
            err(f"{where}: kein canonical")
        else:
            want = C.SITE + p
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
            # Fuer die Gegenprobe nach dem Durchlauf merken. Suchmaschinen
            # werten eine Sprachgruppe nur aus, wenn jede Seite sich selbst
            # nennt und alle einander nennen; fehlt eine Richtung, verwirft
            # Google die Gruppe stillschweigend. Der Ahrefs-Bericht vom
            # 13.08.2026 meldete genau diese Klasse - dort war es eine
            # Drosselung waehrend eines Deploys, aber ein echter Fehler waere
            # bisher nur von aussen aufgefallen.
            hreflang_gruppen[C.SITE + p] = {c: h for c, h in alts if c != "x-default"}

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

    # Gegenprobe: Selbstverweis und Wechselseitigkeit
    for url, gruppe in hreflang_gruppen.items():
        if url not in gruppe.values():
            err(f"{url}: nennt sich selbst nicht im hreflang")
        for code, ziel in gruppe.items():
            andere = hreflang_gruppen.get(ziel)
            if andere is None:
                err(f"{url}: hreflang {code} -> {ziel} ist keine indexierbare Seite")
            elif url not in andere.values():
                err(f"{url}: hreflang {code} -> {ziel} kommt nicht zurueck")

    print(f"{len(pages)} Seiten geprüft  ·  {dict(per_lang)}")
    print(f"hreflang: {len(hreflang_gruppen)} Gruppen, Selbstverweis und "
          f"Wechselseitigkeit geprüft")
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
