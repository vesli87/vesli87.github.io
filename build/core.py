#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VES-TECH Swiss — Kern des Site-Generators.

Enthält:
  * Konfiguration (Domain, Firma, Sprachen, URL-Schema)
  * Laden der Daten aus data/*.json (Single Source of Truth)
  * i18n-Helfer (t, catT, subT, pDesc, trK, trV)
  * die aus dem alten JS portierte Fachlogik
    (deriveFeat, matOf, highlightsOf, fpAssign, relatedAcc …)
  * URL-Bau für DE/FR/IT

Kein externes Paket nötig – läuft mit der system-Python 3.9.
"""

import json
import os
import pathlib
import re
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BUILD = ROOT / "build"

# --------------------------------------------------------------------------
# Konfiguration
# --------------------------------------------------------------------------

SITE = "https://www.ves-tech.ch"          # kanonische Domain (ohne Slash am Ende)

# Eigene Domain: erst einschalten, wenn ihr DNS auf GitHub Pages zeigt.
# Liegt CNAME im Repository, stellt GitHub Pages die Auslieferung auf diese
# Domain um – die Vorschau unter <user>.github.io antwortet dann mit 404.
# Sobald www.ves-tech.ch registriert ist und auf vesli87.github.io. zeigt:
#   1. SITE oben auf "https://www.ves-tech.ch" setzen
#   2. EMIT_CNAME = True
#   3. python3 build/build.py && python3 build/check.py && git push
# GitHub Pages leitet danach github.io per 301 auf die eigene Domain um.
CUSTOM_DOMAIN = "www.ves-tech.ch"
EMIT_CNAME = True
LANGS = ["de", "fr", "it"]
DEFAULT_LANG = "de"

COMPANY = {
    "name": "VES-TECH Swiss",
    "legal_name": "VES-TECH Swiss",
    "street": "Bildfeldstrasse 24",
    "zip": "9552",
    "city": "Bronschhofen",
    "region": "SG",
    "region_name": "St. Gallen",
    "country": "CH",
    "country_name": "Schweiz",
    "phone": "+41 76 710 91 39",
    "phone_href": "+41767109139",
    "email": "vestechswiss@gmail.com",
    # Einzelunternehmen: das Geschaeft laeuft auf den Namen des Inhabers.
    # Er gehoert deshalb nicht nur ins Impressum, sondern ueberall dorthin,
    # wo die Firma als Anbieterin auftritt (UWG Art. 3 Abs. 1 lit. s).
    "owner": "Martin Veselovsky",
    "hours": "Mo-Do 07:30-17:00 · Fr 07:30-11:30",
    # Muss mit dem Google Business Profile uebereinstimmen - Google gleicht
    # Oeffnungszeiten zwischen Website und Profil ab.
    "hours_schema": [
        {"days": ["Monday", "Tuesday", "Wednesday", "Thursday"],
         "opens": "07:30", "closes": "17:00"},
        {"days": ["Friday"], "opens": "07:30", "closes": "11:30"},
    ],
    "lat": 47.4906,      # Bronschhofen (SG), Näherung für LocalBusiness
    "lon": 9.0205,
    "founding_area": ["CH", "LI"],
}

# Die Werkstatt sitzt nicht an der Firmenadresse. Bildfeldstrasse ist die
# Rechnungsadresse; gearbeitet wird bei der Partnerfirma in Herisau. Beides
# gehoert auf die Seite - wer ein Geraet bringt, faehrt sonst falsch.
WORKSHOP = {
    "partner": "Schweisstechnik Scherrer AG",
    # Mit www: ohne leitet die Partnerseite per 301 dorthin um. Ein Link auf
    # eine Weiterleitung kostet einen Umweg und wird von Pruefwerkzeugen
    # gemeldet - hier steht deshalb gleich das Ziel.
    "partner_url": "https://www.schweisstechnik-scherrer.ch/",
    "street": "St. Gallerstrasse 49",
    "zip": "9100",
    "city": "Herisau",
    "region": "AR",
    "region_name": "Appenzell Ausserrhoden",
    "country_name": "Schweiz",
    "lat": 47.3861,     # Herisau (AR), Naeherung fuer LocalBusiness
    "lon": 9.2792,
}

# Welche Folien das Band auf der Startseite zeigt, in dieser Reihenfolge.
#
# Eine einzelne Folie ist kein Karussell: dann entfallen die Punkte darunter,
# das Umschalten und der Zeitgeber. Zwei oder mehr, und alles kommt zurueck -
# ohne dass am Markup etwas geaendert werden muesste.
#
# Verlauf: Am 05.08.2026 war die MPT-Folie kurz heraus, weil das damals
# gelieferte Bild mit 1672 px zu klein war und auf feinen Bildschirmen weich
# wirkte. Mit der Fassung 3344 x 1882 px ist sie wieder drin - jetzt entsteht
# auch die 2048er Stufe, und damit reicht es fuer die doppelte Punktdichte.
HERO_SLIDES = ["hero", "hero-mpt"]

# Kartenverweis auf die Werkstatt. Steht als hasMap im LocalBusiness.
MAP_URL = ("https://www.google.com/maps/search/?api=1&query="
           + WORKSHOP["street"].replace(" ", "+") + ",+"
           + WORKSHOP["zip"] + "+" + WORKSHOP["city"])

# sameAs verknuepft die Website mit denselben Profilen anderswo. Genau das
# braucht Google, um zu erkennen, dass Unternehmensprofil, Verzeichniseintrag
# und Website dieselbe Firma sind - der wichtigste Hebel fuer die lokale
# Sichtbarkeit in der Schweiz.
#
# Die Liste bleibt leer, bis die Profile wirklich bestehen. Ein erfundener
# Verweis waere schlimmer als keiner: Google prueft, ob dort dieselbe Firma
# mit derselben Adresse steht.
#
# Sobald angelegt, hier eintragen (in dieser Reihenfolge sinnvoll):
#   1. Google-Unternehmensprofil  (maps.app.goo.gl/... oder die Maps-URL)
#   2. local.ch     3. search.ch     4. moneyhouse.ch
#   5. svs.ch-Firmenmitglieder     6. LinkedIn
# Danach: python3 build/build.py && push. Der Knoten erscheint automatisch.
SAMEAS = []

# Verifizierung der Webmaster-Tools. Beide Dienste bieten eine Meta-Tag-Methode;
# bei einer <user>.github.io-Adresse ist das der einzige gangbare Weg, weil die
# DNS-Verifizierung eine eigene Domain voraussetzt.
#   Google:  Search Console -> Property "URL-Präfix" -> HTML-Tag -> content-Wert
#   Bing:    Webmaster Tools -> Meta-Tag -> content-Wert
# Nach dem Eintragen: python3 build/build.py && push. Das Tag steht dann auf jeder
# Seite; Search Console prüft die Startseite.
# IndexNow: meldet neue und geänderte Seiten sofort an Bing, Yandex, Seznam und
# Naver, statt auf den nächsten Crawl zu warten. Google unterstützt IndexNow
# nicht – dort führt der Weg über die Search Console.
# Der Schlüssel muss unter https://<host>/<key>.txt erreichbar sein; build.py
# legt die Datei automatisch an.
INDEXNOW_KEY = "266e3b91b00779fe333528ec8a2dc352"

# Search Console, Variante "HTML-Datei": Google erwartet unter /<name>.html eine
# Datei mit genau einer Zeile. Der Build erzeugt sie, damit sie kein spaeterer
# Deploy verliert - Google prueft sie dauerhaft, nicht nur einmal.
GOOGLE_VERIFY_FILE = "googlefd8076c76b8bacd3.html"

# Alternative zur Datei: Meta-Tag auf jeder Seite. Nur eines von beidem noetig.
GOOGLE_SITE_VERIFICATION = ""
BING_SITE_VERIFICATION = ""

BRAND = "MAHE"
BRAND_URL = "https://mahe-online.de/"
REMOTE_IMG = "https://mahe-online.de/wp-content/uploads/"

# Web3Forms-Key: wird aus build/config.local.json oder aus der Umgebung gelesen.
# Ohne Key fallen die Formulare automatisch auf mailto: zurück.
def web3forms_key():
    p = BUILD / "config.local.json"
    if p.exists():
        try:
            return (json.loads(p.read_text("utf-8")).get("web3forms_key") or "").strip()
        except Exception:
            pass
    return (os.environ.get("WEB3FORMS_KEY") or "").strip()


# --------------------------------------------------------------------------
# Daten laden
# --------------------------------------------------------------------------

def _load(name):
    return json.loads((DATA / f"{name}.json").read_text("utf-8"))

P         = _load("P")           # 52 Produkte
CATS      = _load("CATS")        # 4 Kategorien
PK        = _load("PK")          # Kategorie-Icons
UI        = _load("UI")          # 88 UI-Keys × de/fr/it
CATTR     = _load("CATTR")
SUBTR     = _load("SUBTR")
VTTR      = _load("VTTR")      # Geraetetypen (Feld vt) je Sprache
PDESC     = _load("PDESC")
PNAME     = _load("PNAME")     # Gattungsnamen je Sprache
SPECK     = _load("SPECK")
SPECV     = _load("SPECV")
PROC      = _load("PROC")        # 7 Verfahren
DLS       = _load("DLS")         # 7 Download-PDFs
FEAT      = _load("FEAT")        # 19 Verfahrens-Icons
HL        = _load("HL")
HL_CLEAN  = _load("HL_CLEAN")
FP        = _load("FP")
FPGRP     = _load("FPGRP")
HL_VAR    = _load("HL_VAR")    # Geraetevarianten mit eigenem Bild und eigener Liste     # Panels nach Geraetevariante, wie bei MAHE
SYM       = _load("SYM")       # Symbole je Geraet, aus dem MAHE-Katalog 2023
ACC       = _load("ACC")       # passendes Zubehoer je Produkt, von MAHE
MAT_LABEL = _load("MAT_LABEL")
HL_DEVICE = _load("HL_DEVICE")        # je Geraet,  woertlich von mahe-online.de
OPT       = _load("OPT")         # Optionen je Geraet, aus der MAHE-Preisliste
DLDEV     = _load("DLDEV")       # Anleitungen/Datenblaetter je Geraet bei MAHE
GALLERY   = _load("GALLERY")     # Zusatzbilder unter dem Hauptbild
PANEL_HL_DEVICE = _load("PANEL_HL_DEVICE")  # je Frontpanel, ebenso
PANEL_SVG_SMALL = _load("PANEL_SVG")
SPECMAP   = _load("SPECMAP")     # Produkt -> Tabelle(n) bei MAHE
SPECROW   = _load("SPECROW")     # Zeilenbeschriftung -> fr/it
SPECNOTE  = _load("SPECNOTE")    # Fussnote unter der Tabelle
REF       = _load("REF")         # echte Kundenstimmen, siehe data/REF.json

# Die technischen Daten kommen so, wie MAHE sie zeigt, aus build/mahe_specs.json
# (geholt mit build/scrape_specs.py, geprueft mit build/verify_mahe.py).
MAHE_SPECS = json.loads((BUILD / "mahe_specs.json").read_text("utf-8"))

EX = json.loads((BUILD / "i18n_extra.json").read_text("utf-8"))

BY_ID = {p["id"]: p for p in P}
CAT_BY_ID = {c["id"]: c for c in CATS}


# --------------------------------------------------------------------------
# i18n
# --------------------------------------------------------------------------

def t(lang, key, **fmt):
    """UI-String in der gewünschten Sprache; Fallback DE, dann Key."""
    v = EX.get(lang, {}).get(key)
    if v is None:
        v = UI.get(lang, {}).get(key)
    if v is None:
        v = EX.get(DEFAULT_LANG, {}).get(key)
    if v is None:
        v = UI[DEFAULT_LANG].get(key, key)
    if fmt and isinstance(v, str):
        try:
            return v.format(**fmt)
        except (KeyError, IndexError):
            return v
    return v


def catT(lang, c):
    if lang != "de" and c["id"] in CATTR:
        return CATTR[c["id"]]["t"][lang]
    return c["t"]


def catD(lang, c):
    if lang != "de" and c["id"] in CATTR:
        return CATTR[c["id"]]["d"][lang]
    return c["d"]


def subT(lang, name):
    if lang != "de" and name in SUBTR:
        return SUBTR[name][lang]
    return name


def vtT(lang, vt):
    """Der Geraetetyp (Feld vt) in der Sprache der Seite.

    Bis zum 12.08.2026 wurde vt ueberall roh ausgegeben. Es steht sichtbar auf
    jeder Zubehoerkarte, in der meta description jeder Produktseite, im
    Einleitungssatz, im Suchindex, in products.json und in llms.txt - auf 114
    der 154 franzoesischen und italienischen Produktseiten stand dadurch ein
    deutsches Wort, bis hinein ins Google-Snippet.

    Uebersetzungen in data/VTTR.json. Was dort fehlt, bleibt unveraendert
    stehen; check.py meldet fehlende Eintraege.
    """
    if lang != "de" and vt in VTTR:
        return VTTR[vt][lang]
    return vt


def pDesc(lang, p):
    if lang != "de" and p["id"] in PDESC:
        return PDESC[p["id"]][lang]
    return p["desc"]


def pName(lang, p):
    """Produktname in der Sprache der Seite.

    Typenbezeichnungen wie MF155 oder PSHB 65 sind ueberall gleich – sie stehen
    nicht in PNAME. Gattungsbegriffe wie „Drahtvorschubrollen" schon: sonst
    steht auf der franzoesischen Seite ein deutscher Titel ueber einem
    franzoesischen Text.
    """
    if lang != DEFAULT_LANG and p["id"] in PNAME:
        return PNAME[p["id"]][lang]
    return p["name"]


def trK(lang, k):
    if lang != "de" and k in SPECK:
        return SPECK[k][lang]
    return k


def trV(lang, v):
    if lang == "de":
        return v
    if v in SPECV:
        return SPECV[v][lang]
    if v.startswith("bis "):
        return ("jusqu’à " if lang == "fr" else "fino a ") + v[4:]
    return v


# --------------------------------------------------------------------------
# Technische Daten – die Tabelle von mahe-online.de
# --------------------------------------------------------------------------
#
# Uebernommen wird der Inhalt woertlich. Korrigiert wird nur, was auch bei den
# Besonderheiten korrigiert wird: Schweizer „ss" statt „ß" und die Tippfehler
# von MAHE. build/verify_mahe.py haelt beide Listen gegen die Herstellerseite.

SPEC_FIX_K = [("Einschaultdauer", "Einschaltdauer"),
              ("Nezabsicherung", "Netzabsicherung"),
              ("Ausgangstrom", "Ausgangsstrom"),
              ("Ausgangspannungsbereich", "Ausgangsspannungsbereich"),
              ("Eingangsleistung max", "Eingangsleistung max."),
              ("Maße", "Masse"), ("ß", "ss")]
SPEC_FIX_V = [("230V, 60/60Hz", "230V, 50/60Hz"),   # 60/60 Hz gibt es nicht
              ("50/60 Hz", "50/60Hz"),
              ("12.5kg", "12,5kg"), ("13.5kg", "13,5kg")]
SPEC_EMPTY = "–"   # MAHE schreibt "-" oder "---" fuer „gibt es nicht"


def _specK(s):
    s = " ".join(str(s).split())
    for a, b in SPEC_FIX_K:
        s = s.replace(a, b)
    return s


def _specV(s):
    s = " ".join(str(s).split())
    if s in ("", "-", "--", "---", "—"):
        return SPEC_EMPTY
    for a, b in SPEC_FIX_V:
        s = s.replace(a, b)
    return s


def specTables(lang, p):
    """Technische Daten des Produkts als Tabellen mit einer Spalte je Variante.

    [{"title": "Beta digital SYN", "cols": ["200","240","300"],
      "rows": [["Netzspannung", "230V, 50/60Hz", …], …], "note": "…"}]
    """
    out = []
    for key in SPECMAP.get(p["id"], []):
        t = MAHE_SPECS.get(key)
        if not t:
            continue
        keys = [c["key"] for c in t["columns"]]
        rows = []
        for r in t["rows"]:
            k = _specK(r.get("model", ""))
            lab = SPECROW.get(k, {}).get(lang, k) if lang != DEFAULT_LANG else k
            rows.append([lab] + [_specV(r.get(c, "")) for c in keys])
        note = SPECNOTE.get(key) or {}
        out.append({"title": t.get("title", ""),
                    "cols": [c["title"] for c in t["columns"]],
                    "rows": rows,
                    "note": note.get(lang) or note.get(DEFAULT_LANG, "")})
    return out


def specRowsDE(p):
    """Alle deutschen Zeilenbeschriftungen des Produkts – fuer Suche und Filter."""
    out = []
    for key in SPECMAP.get(p["id"], []):
        for r in MAHE_SPECS.get(key, {}).get("rows", []):
            k = _specK(r.get("model", ""))
            if k and k not in out:
                out.append(k)
    return out


def specRest(p):
    """Die kurze Merkmalsliste aus P.json ohne das, was die Tabelle schon zeigt.

    „Netz" faellt weg, weil die Tabelle „Netzspannung" hat; „Kuehlung" oder
    „Antrieb" bleiben, die stehen bei MAHE nirgends in der Tabelle.
    """
    tab = [k.lower() for k in specRowsDE(p)]
    if not tab:
        return p["specs"]
    return {k: v for k, v in p["specs"].items()
            if not any(t.startswith(k.lower()) or k.lower().startswith(t)
                       or t.endswith(k.lower()) for t in tab)}


# --------------------------------------------------------------------------
# Fachlogik (1:1 aus dem alten JS portiert)
# --------------------------------------------------------------------------

def symbolsOf(p):
    """Symbole des Geraets, gruppiert wie im MAHE-Katalog.

    [("mig", ["mis", "puls", …]), ("wig", ["lift"]), ("elektrode", [ … ])]

    Vorher stand hier deriveFeat: eine Reihe regulaerer Ausdruecke ueber Name,
    Typ, Merkmalsliste und Besonderheiten. Das Verfahren hat mehr erfunden als
    getroffen. Ein Befestigungssatz bekam WIG/TIG, weil in „Befestigungssatz"
    die Zeichenfolge „tig" steckt. Der Delta Digital DS bekam Wasserkuehlung,
    weil er unter Wasser schweisst. Ein Fahrwagen bekam ein Digitaldisplay,
    weil in seiner Kompatibilitaetsliste „Beta digital" steht. Und wer
    Doppelpuls konnte, bekam wegen eines elif nie das Puls-Symbol.

    Jetzt steht in data/SYM.json, was der Hersteller in seinem Katalog zeigt.
    """
    e = SYM.get(p["id"])
    if not e:
        return []
    return [(g, [k for k in ids if k in FEAT])
            for g, ids in e["gruppen"].items() if any(k in FEAT for k in ids)]


def verfahrenOf(lang, p):
    """Was das Geraet kann - fuer das Etikett auf Karte und Detailseite.

    Frueher stand dort ein einzelnes, von Hand gesetztes Wort. Bei der Beta
    digital war das "WIG", obwohl sie auch Elektroden schweisst; bei der
    HyperMIG X "MIG/MAG", obwohl sie zusaetzlich WIG Lift Arc und MMA kann.
    Wer nur auf die Karte schaut, sah damit weniger, als die Maschine leistet.

    Abgeleitet wird die Liste aus den Katalogsymbolen (data/SYM.json), also aus
    dem, was der Hersteller dem Geraet ausdruecklich zuschreibt.
    """
    e = SYM.get(p["id"]) or {}
    if e.get("etikett"):
        return e["etikett"]          # wo die Ableitung zu grob waere
    grp = dict(symbolsOf(p))
    # Beherrscht das Geraet nur eine Disziplin, bleibt das von Hand gesetzte
    # Wort stehen - es ist genauer als die Gruppe. Der HCS 1 signiert, das P1
    # poliert, das N1 neutralisiert; "Reinigen" waere fuer alle drei zu grob.
    # Erst ab zwei Disziplinen zaehlt die Vollstaendigkeit mehr als die Nuance.
    if len(grp) < 2:
        return [vtT(lang, p["vt"])]
    out = []
    if "mig" in grp:
        out.append(t(lang, "v_mig"))
    # Lift Arc allein macht noch keine WIG-Maschine. Die i-1600 und die Delta
    # 1800 koennen den Lichtbogen per Lift zuenden - das ist eine Zusatz-
    # funktion, kein zweites Verfahren. "WIG DC" auf der Karte verspricht dem
    # Kunden eine WIG-Anlage. Erst mit HF-Zuendung, Pulsen oder AC/DC zaehlt
    # WIG als eigene Disziplin; das Symbol Lift Arc steht weiterhin am Geraet.
    if "wig" in grp and set(grp["wig"]) - {"lift"}:
        out.append(t(lang, "v_wig_ac" if "acdc" in grp["wig"] else "v_wig_dc"))
    if "elektrode" in grp:
        out.append(t(lang, "v_mma"))
    if "plasma" in grp:
        out.append(t(lang, "v_plasma"))
    if "reinigen" in grp:
        out.append(t(lang, "v_clean"))
    return out or [vtT(lang, p["vt"])]


def featOf(p):
    """Alle Symbole eines Geraets als flache Liste – fuer Suche und Filter."""
    return [k for _, ids in symbolsOf(p) for k in ids]


def featLabel(lang, k):
    f = FEAT.get(k)
    return (f.get(lang) or f.get("de")) if f else k


def isWater(p):
    return bool(re.search(r"wasser|cwk|wwk",
                          p["name"] + " " + " ".join(p["specs"].values()), re.I))


def relatedAcc(p):
    """Passendes Zubehoer – aus data/ACC.json, nicht geraten.

    Frueher stand hier eine Faustregel je Geraetefamilie („MIG/MAG bekommt
    Fahrwagen, Flaschenhalter, Kuehler"). Sie traf selten das, was der
    Hersteller zum Geraet auffuehrt: bei der EcoMIG fehlten beide Brenner, die
    Kabel und die Vorschubrollen, dafuer stand ein Kuehlgeraet da, das MAHE
    dort gar nicht nennt. ACC.json bildet den Tab „Zubehoer" der jeweiligen
    MAHE-Geraeteseite ab.
    """
    return [i for i in ACC.get(p["id"], []) if i in BY_ID]


def hlVariants(lang, p):
    """Ausfuehrungen eines Geraets, jede mit Bild und eigenen Besonderheiten.

    Die EcoMIG buendelt drei Maschinen. MAHE stellt sie nebeneinander, und die
    Listen unterscheiden sich: die Analog kennt weder Synergiesteuerung noch
    digitale Anzeigen, die 2000 Digital weder Intervallschweissen noch
    Elektrode und WIG. Eine gemeinsame Liste waere fuer zwei der drei falsch.
    """
    return [(v["n"], v["img"], v.get(lang) or v["de"]) for v in HL_VAR.get(p["id"], [])]


def optionsOf(lang, p):
    """Optionen und Zusatzleistungen eines Geraets.

    Steht bewusst neben den Besonderheiten und nicht darin: was zum Geraet
    gehoert und was dazubestellt wird, sind zwei verschiedene Aussagen. Preise
    stehen hier nie - die Anfrage klaert sie.
    """
    e = OPT.get(p["id"])
    if not e:
        return []
    return e.get(lang) or e.get("de") or []


def referenzen(lang, geraet=None):
    """Kundenstimmen mit vorliegender Freigabe.

    Ohne "freigabe": true faellt ein Eintrag heraus - eine Firma namentlich zu
    nennen ist eine Bearbeitung von Personendaten, und ohne Zustimmung hat sie
    auf der Seite nichts verloren. Erfundene Stimmen gibt es hier ohnehin
    nicht; die Begruendung steht in data/REF.json.
    """
    out = []
    for r in REF.get("refs", []):
        if not r.get("freigabe"):
            continue
        if geraet and r.get("geraet") != geraet:
            continue
        txt = (r.get("text") or {})
        satz = txt.get(lang) or txt.get("de")
        if not satz or not r.get("firma"):
            continue
        out.append({"firma": r["firma"], "ort": r.get("ort", ""),
                    "person": r.get("person", ""), "rolle": r.get("rolle", ""),
                    "text": satz, "geraet": r.get("geraet"), "datum": r.get("datum", "")})
    return out


def galleryOf(lang, p):
    """Zusatzbilder unter dem Hauptbild.

    alt beschreibt das Bild und ist Pflicht - ohne Alt-Text ist ein Bild fuer
    Screenreader und fuer die Bildersuche nicht vorhanden. cap ist die sichtbare
    Bildunterschrift und freiwillig: manche Bilder erklaeren sich selbst und
    wollen keinen Absatz darunter.
    """
    out = []
    for g in GALLERY.get(p["id"], []):
        if not isinstance(g, dict) or not g.get("img"):
            continue
        a = g.get("alt") or {}
        cap = g.get("cap") or {}
        out.append({"img": g["img"],
                    "alt": a.get(lang) or a.get("de") or "",
                    "cap": cap.get(lang) or cap.get("de") or ""})
    return out


def highlightsOf(lang, p):
    """Besonderheiten eines Geraets.

    Reihenfolge: was MAHE fuer genau dieses Geraet angibt, sonst die Liste der
    Cleaner-Familie, sonst die Geraetefamilie. Frueher galt nur die Familie -
    dadurch stand an der Omega AX syn (MAHE: 5 Punkte) derselbe Text wie an der
    Omega AX pro (10 Punkte) und an allen anderen WIG-AC/DC-Geraeten.
    """
    dev = HL_DEVICE.get(p["id"])
    if dev:
        return dev.get(lang) or dev["de"]
    if p["cat"] == "reinigung" and p["sub"] == "Cleaner" and p["id"] in HL_CLEAN:
        h = HL_CLEAN[p["id"]]
        return h.get(lang) or h.get("de")
    fam = None
    if p["id"] == "hypermig-x":                 fam = "mig_hyper"
    elif p["sub"] == "MIG / MAG":               fam = "mig_std"
    elif p["sub"] == "WIG / TIG":               fam = "wig_acdc" if re.search(r"ac/dc", p["vt"], re.I) else "wig"
    elif p["sub"] == "MMA":                     fam = "mma"
    elif p["sub"] == "Plasma TIG":              fam = "plasmatig"
    elif p["cat"] == "plasmaschneiden":         fam = "theta"
    elif p["cat"] == "reinigung" and p["sub"] == "Cleaner":
        fam = "cleaner"
    if not fam or fam not in HL:
        return None
    return HL[fam].get(lang) or HL[fam].get("de")


def matOf(p):
    if p["sub"] == "MIG / MAG":            return ["ST", "SS", "AL"]
    if p["sub"] == "WIG / TIG":            return ["ST", "SS", "AL"] if re.search(r"ac/dc", p["vt"], re.I) else ["ST", "SS"]
    if p["sub"] == "MMA":                  return ["ST", "SS"]
    if p["sub"] == "Plasma TIG":           return ["ST", "SS", "AL"]
    if p["cat"] == "plasmaschneiden":      return ["ST", "SS", "AL"]
    if p["cat"] == "reinigung" and p["sub"] == "Cleaner":
        return ["SS"]
    return []


def matLabel(lang, m):
    d = MAT_LABEL.get(m)
    return (d.get(lang) or d.get("de")) if d else m


# Frontpanels je Geraet. Die Dateien stammen direkt von MAHE (build/panels.py);
# wo der Hersteller keines geliefert hat, bleibt der gezeichnete Ersatz oder es
# werden nur die Besonderheiten gezeigt - erfunden wird nichts.
PANELS = {
    # Reihenfolge wie auf der Herstellerseite
    "hypermig-x":        ["hypermig_ecomig", "hypermig_ex", "hypermig_hx",
                          "hypermig_steel", "hypermig_sx"],
    "ecomig":            ["ecomig_analog", "ecomig_low", "ecomig_2000"],
    "mms":               ["mms_light", "mms_ecomig", "mms_ecopuls"],
    "omega-ax":          ["omega_pro", "omega_syn"],
    "beta-dx":           ["betadx_pro", "betadx_syn"],
    "beta-digital":      ["betadig_profi", "betadig_syn"],
    "hypertig-ax":       ["hypertig_ax"],
    "hypertig-dx":       ["hypertig_dx"],
    "hypertig-acdc":     ["hypertig_acdc"],
    "i-1600":            ["i1600_panel"],
    "delta":             ["delta_panel"],
    # Das Panel mit der Uo-Vorwahl 15V/42V/max gehoert an die Delta Digital -
    # der Katalog nennt auf Seite 46 ausdruecklich "Einstellbare
    # Leerlaufspannung ab 15V". Frueher stand hier DeltaDigital_1800.png, ein
    # anderes Panel ohne diese Vorwahl.
    "delta-digital":     ["deltadig_big"],
    "delta-digital-ds":  ["deltadig_big"],
    "theta-40":          ["theta40_panel"],
    "theta-60":          ["theta_hsc"],
    "theta-120":         ["theta_hsc"],
    "theta-180":         ["theta_hsc"],
    "theta-60-aut":      ["theta_hsc"],
    "theta-120-aut":     ["theta_hsc"],
    "minicleaner":       ["mini_panel"],
    "hypercleaner-st":   ["cleaner_st"],
    "hypercleaner-plus": ["cleaner_plus"],
    "hypercleaner-ct200": ["ct200_panel", "ct200_syn"],
}


def fpGroups(p):
    """Frontpanels des Geraets, gruppiert wie auf der MAHE-Seite.

    [("MMS 2000C", ["mms_light"]), ("MMS 2000P EX", ["mms_ecomig", …]), …]

    Wo MAHE nicht nach Varianten gliedert, steht eine einzige Gruppe ohne
    Ueberschrift. Ein Panel darf in mehreren Gruppen stehen – die MMS 2000P EX
    und die 2400/3000 EX haben dieselben zwei, und der Hersteller fuehrt sie
    bei beiden auf.
    """
    g = FPGRP.get(p["id"])
    if g:
        return [(name, [k for k in keys if k in FP]) for name, keys in g]
    keys = PANELS.get(p["id"], [])
    return [("", keys)] if keys else []


def fpAssign(p):
    # Frueher fielen Geraete ohne eigenes Panel auf ein gezeichnetes
    # Familienpanel zurueck. Das hat der PlasmaTIG das Fronteingabesystem der
    # HyperTIG DX angehaengt – ein anderes Geraet. Wer kein Panel hat, zeigt
    # keines.
    return PANELS.get(p["id"], [])


def products_of(cat_id, sub=None):
    out = [p for p in P if p["cat"] == cat_id]
    if sub:
        out = [p for p in out if p["sub"] == sub]
    return out


def full_img(path):
    """'2024/06/IMGP5943-226x300.png' -> '2024/06/IMGP5943.png'"""
    return re.sub(r"-[0-9]+x[0-9]+(\.[a-zA-Z]+)$", r"\1", path)


# --------------------------------------------------------------------------
# Slugs & URLs
# --------------------------------------------------------------------------

def slugify(s):
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    s = s.replace("Ä", "ae").replace("Ö", "oe").replace("Ü", "ue")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return re.sub(r"-{2,}", "-", s)


# Sprachabhängige Pfadsegmente
SEG = {
    "de": {"root": "",   "products": "produkte", "search": "suche",     "processes": "verfahren",
           "downloads": "downloads", "contact": "kontakt", "faq": "faq",
           "service": "service",
           "imprint": "impressum", "privacy": "datenschutz", "terms": "agb"},
    "fr": {"root": "fr", "products": "produits", "search": "recherche", "processes": "procedes",
           "downloads": "telechargements", "contact": "contact", "faq": "questions-frequentes",
           "service": "service",
           "imprint": "mentions-legales", "privacy": "protection-des-donnees",
           "terms": "conditions-generales"},
    "it": {"root": "it", "products": "prodotti", "search": "ricerca",   "processes": "processi",
           "downloads": "download", "contact": "contatto", "faq": "domande-frequenti",
           "service": "assistenza",
           "imprint": "note-legali", "privacy": "protezione-dati",
           "terms": "condizioni-generali"},
}

# Unterseiten des Servicebereichs, je auf eigener URL. Wer „Schweissgeraet
# kalibrieren" sucht, sucht etwas anderes als wer „Schweissgeraet reparieren"
# sucht - eine Seite kann nur fuer eine Absicht die beste Antwort sein.
# Vorher zeigten alle drei Servicelinks der Fusszeile auf /kontakt/; damit gab
# es zu keinem dieser Begriffe eine Seite, die davon handelt.
SERVICE_SEG = {
    "de": {"repair": "reparatur",  "calib": "kalibrierung", "auto": "automation"},
    "fr": {"repair": "reparation", "calib": "calibrage",    "auto": "automation"},
    "it": {"repair": "riparazione", "calib": "calibrazione", "auto": "automazione"},
}
SERVICE_KEYS = ("repair", "calib", "auto")

CAT_SLUG = {
    "schweissgeraete": {"de": "schweissgeraete", "fr": "postes-de-soudage", "it": "saldatrici"},
    "plasmaschneiden": {"de": "plasmaschneiden", "fr": "decoupe-plasma",    "it": "taglio-plasma"},
    "reinigung":       {"de": "reinigungsgeraete", "fr": "nettoyage",       "it": "pulizia"},
    "zubehoer":        {"de": "zubehoer",        "fr": "accessoires",       "it": "accessori"},
}

# Sub-Slug pro Sprache aus dem übersetzten Namen
def sub_slug(lang, sub):
    return slugify(subT(lang, sub))


def _j(*parts):
    """Baut '/a/b/c/' aus Teilen, leere Teile fallen weg."""
    segs = [str(x).strip("/") for x in parts if x not in (None, "")]
    return "/" + "/".join(segs) + "/" if segs else "/"


def u_home(lang):
    return _j(SEG[lang]["root"])


def u_products(lang):
    return _j(SEG[lang]["root"], SEG[lang]["products"])


def u_cat(lang, cat_id):
    return _j(SEG[lang]["root"], SEG[lang]["products"], CAT_SLUG[cat_id][lang])


def u_sub(lang, cat_id, sub):
    return _j(SEG[lang]["root"], SEG[lang]["products"], CAT_SLUG[cat_id][lang], sub_slug(lang, sub))


def u_prod(lang, p):
    return _j(SEG[lang]["root"], SEG[lang]["products"], CAT_SLUG[p["cat"]][lang], p["id"])


def u_page(lang, key):
    return _j(SEG[lang]["root"], SEG[lang][key])


def u_service(lang, key=None):
    """/service/ und /service/<reparatur|kalibrierung|automation>/"""
    return _j(SEG[lang]["root"], SEG[lang]["service"],
              SERVICE_SEG[lang][key] if key else None)


def abs_url(path):
    return SITE + path


# Für den Sprachumschalter: dieselbe Seite in allen Sprachen
def alternates(kind, **kw):
    """kind: home|products|cat|sub|prod|page|service  -> {lang: path}"""
    out = {}
    for l in LANGS:
        if kind == "home":       out[l] = u_home(l)
        elif kind == "products": out[l] = u_products(l)
        elif kind == "cat":      out[l] = u_cat(l, kw["cat_id"])
        elif kind == "sub":      out[l] = u_sub(l, kw["cat_id"], kw["sub"])
        elif kind == "prod":     out[l] = u_prod(l, kw["p"])
        elif kind == "page":     out[l] = u_page(l, kw["key"])
        elif kind == "service":  out[l] = u_service(l, kw.get("key"))
    return out
