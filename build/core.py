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
# Umstellen auf True, sobald  www.ves-tech.ch  auf vesli87.github.io. zeigt.
CUSTOM_DOMAIN = "www.ves-tech.ch"
EMIT_CNAME = False
LANGS = ["de", "fr", "it"]
DEFAULT_LANG = "de"

COMPANY = {
    "name": "VES-TECH Swiss",
    "legal_name": "VES-TECH Swiss",
    "street": "Bildfelsstrasse 24",
    "zip": "9552",
    "city": "Bronschhofen",
    "region": "SG",
    "region_name": "St. Gallen",
    "country": "CH",
    "country_name": "Schweiz",
    "phone": "+41 76 710 91 39",
    "phone_href": "+41767109139",
    "email": "info@ves-tech.ch",
    "hours": "Mo-Fr 07:30-17:30",
    "hours_schema": [{"days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                      "opens": "07:30", "closes": "17:30"}],
    "lat": 47.4906,      # Bronschhofen (SG), Näherung für LocalBusiness
    "lon": 9.0205,
    "founding_area": ["CH", "LI"],
}

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
PDESC     = _load("PDESC")
SPECK     = _load("SPECK")
SPECV     = _load("SPECV")
PROC      = _load("PROC")        # 7 Verfahren
DLS       = _load("DLS")         # 7 Download-PDFs
FEAT      = _load("FEAT")        # 19 Verfahrens-Icons
HL        = _load("HL")
HL_CLEAN  = _load("HL_CLEAN")
CTRL      = _load("CTRL")
FP        = _load("FP")
PANEL_HL  = _load("PANEL_HL")
MAT_LABEL = _load("MAT_LABEL")
PANEL_SVG_SMALL = _load("PANEL_SVG")

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


def pDesc(lang, p):
    if lang != "de" and p["id"] in PDESC:
        return PDESC[p["id"]][lang]
    return p["desc"]


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
# Fachlogik (1:1 aus dem alten JS portiert)
# --------------------------------------------------------------------------

def deriveFeat(p):
    s = (p["vt"] + " " + p["name"] + " " + " ".join(p["specs"].values())).lower()
    f = []
    if re.search(r"mig", s):                       f.append("mig")
    if re.search(r"mma|elektrode", s):             f.append("mma")
    if re.search(r"wig|tig", s):                   f.append("wig")
    if re.search(r"doppelpuls", s):                f.append("doppelpuls")
    elif re.search(r"puls", s):                    f.append("puls")
    if re.search(r"plasma", s):                    f.append("plasma")
    if re.search(r"wasser|cwk", s):                f.append("h2o")
    if re.search(r"synerg", s):                    f.append("synergy")
    if re.search(r"digital", s):                   f.append("display")
    if re.search(r"rollen", s):                    f.append("rollen")
    if re.search(r"automation|cnc", s):            f.append("auto")
    if re.search(r"reinig|cleaner", s):            f.append("clean")
    if re.search(r"signier", s):                   f.append("mark")
    if re.search(r"dosier", s):                    f.append("dose")
    if p["sub"] == "WIG / TIG" and "hf" not in f:  f.append("hf")
    if p["sub"] in ("WIG / TIG", "MMA") and "lift" not in f:
        f.append("lift")
    if p["cat"] == "reinigung":
        if p["sub"] == "Cleaner":
            f = ["reinigen", "polieren", "beschriften"]
        elif p["id"] == "p1":
            f = ["polieren"]
        elif p["id"] == "m1" or p["sub"] == "Signiergeräte":
            f = ["beschriften"]
        else:
            f = ["reinigen"]
    seen, out = set(), []
    for x in f:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def featLabel(lang, k):
    f = FEAT.get(k)
    return (f.get(lang) or f.get("de")) if f else k


def isWater(p):
    return bool(re.search(r"wasser|cwk|wwk",
                          p["name"] + " " + " ".join(p["specs"].values()), re.I))


def relatedAcc(p):
    if p["cat"] == "zubehoer":
        return []
    ids = []
    if p["id"] == "hypermig-x":
        ids = ["dvs410", "dvl420", "wk350"]
    elif p["sub"] == "MIG / MAG":
        ids = ["stt30", "mpf02", "wk300"] if p["id"] == "mms" else ["stt30", "mpf02", "wk200"]
    elif p["sub"] == "WIG / TIG":
        ids = ["wk350", "stt30", "mpf02", "frc5"] if isWater(p) else ["stt30", "mpf02", "frc5", "rc5"]
    elif p["sub"] == "MMA":
        ids = ["stt35", "mpf02", "rc5", "rc100"]
    elif p["sub"] == "Plasma TIG":
        ids = ["mpf02", "rc100"]
    elif p["cat"] == "plasmaschneiden":
        ids = ["stt35", "mpf02"]
    elif p["cat"] == "reinigung" and p["sub"] == "Cleaner":
        ids = ["r1", "rp1", "p1", "m1", "mhct01", "elektrodenkabel"]
    elif p["cat"] == "reinigung" and p["sub"] == "Elektrolyte":
        ids = ["hypercleaner-st", "minicleaner", "mhct01"]
    elif p["cat"] == "reinigung":
        ids = ["mhct01", "r1"]
    return [i for i in ids if i in BY_ID][:6]


def highlightsOf(lang, p):
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


def fpAssign(p):
    if p["id"] == "hypermig-x":
        return ["ecomig", "ecopuls", "hyper", "steel", "steelpuls"]
    if p["sub"] == "MIG / MAG":       return ["ecomig", "ecopuls"]
    if p["sub"] == "WIG / TIG":       return ["wig_acdc" if re.search(r"ac/dc", p["vt"], re.I) else "wig"]
    if p["sub"] == "Plasma TIG":      return ["wig"]
    if p["sub"] == "MMA":             return ["mma"]
    if p["cat"] == "plasmaschneiden": return ["theta"]
    return []


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
           "imprint": "impressum", "privacy": "datenschutz"},
    "fr": {"root": "fr", "products": "produits", "search": "recherche", "processes": "procedes",
           "downloads": "telechargements", "contact": "contact", "faq": "questions-frequentes",
           "imprint": "mentions-legales", "privacy": "protection-des-donnees"},
    "it": {"root": "it", "products": "prodotti", "search": "ricerca",   "processes": "processi",
           "downloads": "download", "contact": "contatto", "faq": "domande-frequenti",
           "imprint": "note-legali", "privacy": "protezione-dati"},
}

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


def abs_url(path):
    return SITE + path


# Für den Sprachumschalter: dieselbe Seite in allen Sprachen
def alternates(kind, **kw):
    """kind: home|products|cat|sub|prod|page  -> {lang: path}"""
    out = {}
    for l in LANGS:
        if kind == "home":       out[l] = u_home(l)
        elif kind == "products": out[l] = u_products(l)
        elif kind == "cat":      out[l] = u_cat(l, kw["cat_id"])
        elif kind == "sub":      out[l] = u_sub(l, kw["cat_id"], kw["sub"])
        elif kind == "prod":     out[l] = u_prod(l, kw["p"])
        elif kind == "page":     out[l] = u_page(l, kw["key"])
    return out
