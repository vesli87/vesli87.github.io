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

from urllib.parse import urlsplit
import json
import datetime
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
LANGS = ["de", "fr", "it", "en"]
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
    # Vom Inhaber bestaetigter Geschaeftskontakt; kein vorbefuellter Nachrichtentext.
    "whatsapp_href": "https://wa.me/41767109139",
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

# Featured products in the VOLT homepage carousel. Order is shared by DE/FR/IT.
HOME_FEATURED = ('mpt-3001', 'hypermig-twin', 'hypertig-ax', 'hypertig-dx',
                 'omega-ax', 'beta-dx')

# Kartenverweis auf die Werkstatt. Steht als hasMap im LocalBusiness.
MAP_URL = ("https://www.google.com/maps/search/?api=1&query="
           + WORKSHOP["street"].replace(" ", "+") + ",+"
           + WORKSHOP["zip"] + "+" + WORKSHOP["city"])

# Verifizierte Firmenprofile, am 22.09.2026 im jeweiligen Firmenkonto bestaetigt.
# Dieselben URLs erscheinen als normale Footerlinks und als Organization.sameAs.
# Nur tatsaechlich bestehende Firmenprofile aufnehmen, keine privaten Konten
# oder noch unbestaetigten Eintraege. Die Links laden keine Social-Media-Embeds.
SOCIAL_PROFILES = (
    ("Instagram", "https://www.instagram.com/vestechswiss/"),
    ("LinkedIn", "https://www.linkedin.com/company/ves-tech-swiss/"),
    ("Facebook", "https://www.facebook.com/profile.php?id=61594862482139"),
)
SAMEAS = [url for _, url in SOCIAL_PROFILES]

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
BING_SITE_VERIFICATION = "34CAE7C088828A1A6D1AD9507A4BAE23"

BRAND = "MAHE"
BRAND_URL = "https://mahe-online.de/"
HERSTELLER = "MAHE GmbH"
REMOTE_IMG = "https://mahe-online.de/wp-content/uploads/"

# Die Marke steht nicht mehr fest im Code, sondern am Produkt.
#
# Der Katalog war bis zum 10.09.2026 reiner MAHE-Katalog, und "MAHE" stand an
# 15 Stellen hart im Quelltext: vor jedem Produktnamen, in jedem Alt-Text, im
# JSON-LD als brand UND als manufacturer, im Feld "Marke" und in der
# Unterkategorie-Ueberschrift. Mit der Rubrik Occasion kamen gebrauchte
# Mikroplasma-Anlagen von Oerlikon dazu. Liefe das ueber dieselben Stellen,
# stuende auf jeder dieser Seiten "MAHE Plasmafix 51" - sachlich falsch, und
# auf einer Verkaufsseite ist das eine Taeuschung ueber die betriebliche
# Herkunft im Sinne von Art. 3 Abs. 1 lit. b UWG.
#
# Ohne "brand" am Produkt bleibt alles wie bisher: MAHE.
# "url" nur, wenn die Adresse nachweislich antwortet und wirklich zu dieser
# Marke gehoert. Bei Oerlikon steht deshalb keine: oerlikon-welding.com loest
# nicht mehr auf (am 10.09.2026 geprueft, keine Antwort), und oerlikon.com ist
# heute die Oerlikon Group der Oberflaechentechnik - eine andere Firma. Das
# Schweissgeschaeft ging an Air Liquide Welding und von dort weiter. Ein
# Verweis dorthin waere schlimmer als keiner. schema.org verlangt url weder an
# Brand noch an Organization; ein name genuegt.
MARKEN = {
    "Oerlikon": {
        "url": None,
        "hersteller": "Oerlikon, Schweissindustrie Oerlikon Bührle AG / Air Liquide Welding",
    },
}


def pBrand(p):
    """Die Marke dieses Produkts."""
    return p.get("brand", BRAND)


def pBrandUrl(p):
    if p.get("models"):
        return None
    m = p.get("brand")
    return MARKEN[m]["url"] if m in MARKEN else BRAND_URL


def pHersteller(p):
    m = p.get("brand")
    return MARKEN[m]["hersteller"] if m in MARKEN else HERSTELLER


def istMahe(p):
    return p.get("brand", BRAND) == BRAND


# Sprachfassungen von Angaben, die in COMPANY/WORKSHOP nur auf Deutsch stehen.
#
# Bis zum 10.09.2026 stand auf der franzoesischen und der italienischen
# Kontaktseite als Land "Schweiz" und auf "Ueber uns" die Zeit "Mo-Do
# 07:30-17:00 · Fr 07:30-11:30" - deutsche Wochentagskuerzel mitten im
# franzoesischen Satz. Im Italienischen ist "Fr" ausserdem missverstaendlich:
# es liest sich als Abkuerzung fuer Franken, nicht fuer Freitag.
LAND = {"de": "Schweiz", "fr": "Suisse", "it": "Svizzera", "en": "Switzerland"}
ZEITEN = {
    "de": "Mo–Do 07:30–17:00 · Fr 07:30–11:30",
    "fr": "lun.–jeu. 07h30–17h00 · ven. 07h30–11h30",
    "it": "lun.–gio. 07:30–17:00 · ven. 07:30–11:30",
    "en": "Mon–Thu 07:30–17:00 · Fri 07:30–11:30",
}
REGION_NAMES = {
    "SG": {"de": "St. Gallen", "fr": "Saint-Gall", "it": "San Gallo", "en": "St. Gallen"},
    "AR": {"de": "Appenzell Ausserrhoden", "fr": "Appenzell Rhodes-Extérieures",
           "it": "Appenzello Esterno", "en": "Appenzell Ausserrhoden"},
}
SEARCH_POPULAR = {
    "de": ["HyperMIG", "WIG AC/DC", "Theta", "Cleaner", "Fahrwagen", "Plasma", "Reparatur"],
    "fr": ["HyperMIG", "TIG AC/DC", "Theta", "Cleaner", "Chariot", "Plasma", "Réparation"],
    "it": ["HyperMIG", "TIG AC/DC", "Theta", "Cleaner", "Carrello", "Plasma", "Riparazione"],
    "en": ["HyperMIG", "TIG AC/DC", "Theta", "Cleaner", "Trolley", "Plasma", "Repairs"],
}


# Fachgebiete fuer knowsAbout im JSON-LD. Standen bis zum 10.09.2026 auch auf
# den 240 franzoesischen und italienischen Seiten auf Deutsch - eine Maschine
# liest daraus, die Firma koenne "MIG/MAG-Schweissen", nicht "soudage MIG/MAG".
KANN = {
    "de": ["MIG/MAG-Schweissen", "WIG/TIG-Schweissen", "MMA-Elektrodenschweissen",
           "Plasmaschneiden", "Elektrolytische Schweissnahtreinigung",
           "Schweissautomation", "EN 1090", "MAHE-Schweissgeräte",
           "Mikroplasma-Schweissen", "Gebrauchte Schweissanlagen (Occasion)",
           "Oerlikon PlasmaFix"],
    "fr": ["Soudage MIG/MAG", "Soudage TIG", "Soudage à l’électrode enrobée",
           "Découpe plasma", "Nettoyage électrolytique des cordons",
           "Automatisation du soudage", "EN 1090", "Postes de soudage MAHE",
           "Soudage microplasma", "Postes de soudage d’occasion",
           "Oerlikon PlasmaFix"],
    "it": ["Saldatura MIG/MAG", "Saldatura TIG", "Saldatura a elettrodo",
           "Taglio al plasma", "Pulizia elettrolitica dei cordoni",
           "Automazione della saldatura", "EN 1090", "Saldatrici MAHE",
           "Saldatura microplasma", "Saldatrici usate (occasioni)",
           "Oerlikon PlasmaFix"],
    "en": ["MIG/MAG welding", "TIG welding", "MMA stick welding", "Plasma cutting",
           "Electrolytic weld cleaning", "Welding automation", "EN 1090", "MAHE welding equipment",
           "Microplasma welding", "Refurbished welding equipment", "Oerlikon PlasmaFix"],
}


def kannAbout(lang):
    return KANN.get(lang, KANN["de"])


def land(lang):
    return LAND.get(lang, LAND["de"])


def zeiten(lang):
    return ZEITEN.get(lang, ZEITEN["de"])


def regionName(lang, code):
    return REGION_NAMES.get(code, {}).get(lang, code)


# Panelnamen: das Modell bleibt, uebersetzt wird nur das Gattungswort.
# "EX: EcoPuls Front Panel" heisst beim Hersteller so und bleibt; aber
# "Bedienpanel" ist unser eigenes Wort und stand auf 40 FR- und IT-Seiten.
PANELWORT = {"fr": "panneau de commande", "it": "pannello di comando", "en": "control panel"}


def fpName(lang, fp):
    if fp.get("names"):
        return fp["names"][lang]
    n = fp["n"]
    if lang == 'en':
        n = n.replace('WIG', 'TIG').replace('MiniReiniger', 'MiniCleaner')
    wort = PANELWORT.get(lang)
    if not wort or "Bedienpanel" not in n:
        return n
    if n.endswith(": Bedienpanel"):
        modell = n[: -len(": Bedienpanel")]
        trenner = " : " if lang == "fr" else ": "
        return f"{modell}{trenner}{wort}"
    if n.endswith("-Bedienpanel"):
        modell = n[: -len("-Bedienpanel")]
        return f"{wort[0].upper()}{wort[1:]} {modell}"
    return n.replace("Bedienpanel", wort)


# schema.org kennt vier Zustaende am Produkt. "refurbished" ist der richtige
# fuer eine Anlage, die komplett revidiert wurde - "used" waere zu wenig, es
# sagt nur, dass sie gebraucht ist.
ZUSTAND_LD = {
    "refurbished": "https://schema.org/RefurbishedCondition",
    "used": "https://schema.org/UsedCondition",
    "new": "https://schema.org/NewCondition",
}


def zustandText(lang, p):
    z = ZUSTAND.get(p["id"])
    return (z.get(lang) or z.get("de")) if z else ""


def zustandLD(p):
    z = ZUSTAND.get(p["id"])
    if z:
        return ZUSTAND_LD.get(z.get("grad", "used"), ZUSTAND_LD["used"])
    return ZUSTAND_LD["used"] if p["cat"] == "occasion" else None


def occText(lang, p):
    """Abschnitte und Fragen zu einer Occasion, aus data/OCCTEXT.json.

    Eine Gebrauchtmaschine mit 250 Woertern Text steht in der Suche hinter
    jeder Galerieseite eines Mitbewerbers, die das Geraet wenigstens
    beschreibt. Am 15.09.2026 nachgesehen: fuer "oerlikon mikroplasma" lag
    eine Bildergalerie mit 60 Woertern auf Platz fuenf, die eigene Seite mit
    Datenblatt und Zustand tauchte gar nicht auf. Was der Kaeufer wissen will
    (wofuer die Anlage gebaut ist, was P+T bedeutet, was dazugehoert, was
    revidiert wurde), stand nirgends. Jetzt steht es unter den Reitern, in
    drei Sprachen, mit den Fragen zusaetzlich als FAQPage im JSON-LD.
    """
    d = OCCTEXT.get(p["id"])
    if not d:
        return None
    return d.get(lang) or d.get("de")


def verwandt(p):
    """Produkte, die unter der Detailseite als Karten stehen (VERWANDT.json).

    Nur Kennungen, die es im Katalog gibt: ein Tippfehler in der Datei darf
    keine tote Karte erzeugen.
    """
    return [k for k in VERWANDT.get(p["id"], []) if k in BY_ID]


def markeMitPraeposition(lang, p):
    """„von MAHE", „d’Oerlikon", „di Oerlikon" - die Praeposition mitgeliefert.

    Im Franzoesischen verschmilzt „de" vor einem Vokal zu „d’". In der Vorlage
    stand „de {marke}", und daraus wurde „de Oerlikon" - falsches Franzoesisch.
    Die Elision haengt am Wort, nicht am Satz, also gehoert sie hierher und
    nicht in die Vorlage.
    """
    m = pBrand(p)
    if lang == "en":
        return "by " + pBrand(p)
    if lang == "fr":
        return ("d’" + m) if m[:1].lower() in "aeiouyh" else ("de " + m)
    if lang == "it":
        return "di " + m
    return "von " + m


def catBrand(cid):
    """Die Marke einer Kategorie - fuer die Ueberschrift „Sub · Marke".

    Fuehrt eine Kategorie nur eine Marke, steht sie in der Ueberschrift. Fuehrt
    sie mehrere (in der Rubrik Occasion kann das jederzeit vorkommen), steht
    dort nichts von einer Marke, denn dann waere jede Angabe falsch.
    """
    marken = {pBrand(p) for p in P if p["cat"] == cid}
    return marken.pop() if len(marken) == 1 else ""

# Web3Forms-Key: wird aus build/config.local.json oder aus der Umgebung gelesen.
# Ohne Key fallen die Formulare automatisch auf mailto: zurück.
def setting(name, env):
    value = os.environ.get(env)
    if value:
        return value.strip()
    for p in (BUILD / "config.local.json", BUILD / "config.public.json"):
        if p.exists():
            try:
                config = json.loads(p.read_text("utf-8"))
                if name not in config:
                    continue
                value = config[name] or ""
                if not isinstance(value, str):
                    raise ValueError(f"{name} must be a string")
                return value.strip()
            except (ValueError, AttributeError) as exc:
                raise ValueError(f"Invalid {p.name}: {exc}") from exc
    return ""


def web3forms_key():
    return setting("web3forms_key", "WEB3FORMS_KEY")


def cloudflare_analytics_token():
    token = setting("cloudflare_analytics_token", "CLOUDFLARE_ANALYTICS_TOKEN")
    if token and not re.fullmatch(r"[a-fA-F0-9]{32}", token):
        raise ValueError("CLOUDFLARE_ANALYTICS_TOKEN must be the 32-character Web Analytics beacon token, not an API credential")
    return token


def ahrefs_analytics_key():
    key = setting("ahrefs_analytics_key", "AHREFS_ANALYTICS_KEY")
    if key and not re.fullmatch(r"[A-Za-z0-9_-]{22}", key):
        raise ValueError("AHREFS_ANALYTICS_KEY must be the 22-character public Web Analytics site key, not an API credential")
    return key


def analytics_enabled():
    # Validate both providers even when the first one is already enabled.
    cloudflare, ahrefs = cloudflare_analytics_token(), ahrefs_analytics_key()
    return bool(cloudflare or ahrefs)


# --------------------------------------------------------------------------
# Daten laden
# --------------------------------------------------------------------------

def _load(name):
    return json.loads((DATA / f"{name}.json").read_text("utf-8"))

P         = _load("P")           # 52 Produkte
CATS      = _load("CATS")        # 4 Kategorien
ANALYTICS_CAMPAIGNS = _load("ANALYTICS_CAMPAIGNS")
INQUIRY_OPTIONS = _load("INQUIRY_OPTIONS")
PK        = _load("PK")          # Kategorie-Icons
UI        = _load("UI")          # 88 UI-Keys × de/fr/it
CATTR     = _load("CATTR")
SUBTR     = _load("SUBTR")
VTTR      = _load("VTTR")      # Geraetetypen (Feld vt) je Sprache
PDESC     = _load("PDESC")
PNAME     = _load("PNAME")     # Gattungsnamen je Sprache
SPECK     = _load("SPECK")
SPECV     = _load("SPECV")
PROC      = _load("PROC")        # 19 erklaerte Verfahren/Funktionen
PROCESS_GUIDE = _load("PROCESS_GUIDE")
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
DLOCC     = _load("DLOCC")       # Prospekte der Occasion-Maschinen, lokal gehostet
IMGCAP    = _load("IMGCAP")      # Bildunterschrift zum Hauptbild, wo noetig
ZUSTAND   = _load("ZUSTAND")     # Zustand einer Occasion-Maschine
OCCTEXT   = _load("OCCTEXT")     # Beschreibung und Fragen zu einer Occasion, DE/FR/IT
VERWANDT  = _load("VERWANDT")    # Neugeraet <-> Occasion derselben Technik
GALLERY   = _load("GALLERY")     # Zusatzbilder unter dem Hauptbild
PANEL_HL_DEVICE = _load("PANEL_HL_DEVICE")  # je Frontpanel, ebenso
PANEL_SVG_SMALL = _load("PANEL_SVG")
SPECMAP   = _load("SPECMAP")     # Produkt -> Tabelle(n) bei MAHE
SPECROW   = _load("SPECROW")     # Zeilenbeschriftung -> fr/it
SPECNOTE  = _load("SPECNOTE")    # Fussnote unter der Tabelle
REF       = _load("REF")         # echte Kundenstimmen, siehe data/REF.json
BUYING_GUIDE = _load("BUYING_GUIDE")
SUBCATEGORY_GUIDES = _load("SUBCATEGORY_GUIDES")
PRODUCT_GUIDES = _load("PRODUCT_GUIDES")
PANEL_GUIDES = _load("PANEL_GUIDES")
HYPERMIG_CWK = _load("HYPERMIG_CWK")
GUIDE_LINKS = _load("GUIDE_LINKS")

# Die technischen Daten kommen so, wie MAHE sie zeigt, aus build/mahe_specs.json
# (geholt mit build/scrape_specs.py, geprueft mit build/verify_mahe.py).
MAHE_SPECS = json.loads((BUILD / "mahe_specs.json").read_text("utf-8"))
# Separately reviewed PDF tables survive refreshes of the HTML/AJAX scraper.
MAHE_CWK_SPECS = json.loads((BUILD / "mahe_cwk_specs.json").read_text("utf-8"))
MAHE_SPECS.update(MAHE_CWK_SPECS)

EX = json.loads((BUILD / "i18n_extra.json").read_text("utf-8"))

BY_ID = {p["id"]: p for p in P}
CAT_BY_ID = {c["id"]: c for c in CATS}


# --------------------------------------------------------------------------
# i18n
# --------------------------------------------------------------------------

def t(lang, key, **fmt):
    """UI-String in der gewünschten Sprache; Fallback DE, dann Key."""
    singular = key + '_one'
    if fmt.get('n') == 1 and (singular in EX.get(lang, {}) or singular in UI.get(lang, {})):
        key = singular
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


def pFullName(lang, p):
    """Keep each reviewed brand paired with its model in a shared listing."""
    if p.get("models"):
        return " / ".join(f"{m['brand']} {m['name']}" for m in p["models"])
    return f"{pBrand(p)} {pName(lang, p)}"


def trK(lang, k):
    return SPECK.get(k, {}).get(lang, k)


def trV(lang, v):
    if v in SPECV and lang in SPECV[v]:
        return SPECV[v][lang]
    if lang == "de":
        return v
    if v.startswith("bis "):
        v = {"fr": "jusqu’à ", "it": "fino a ", "en": "up to "}[lang] + v[4:]
    return re.sub(r'(?<=\d),(?=\d)', '.', v) if lang == 'en' else v


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
            if r.get('model') in t.get('unconfirmed_rows', []):
                continue
            k = _specK(r.get("model", ""))
            lab = SPECROW.get(k, {}).get(lang, k)
            rows.append([lab] + [trV(lang, _specV(r.get(c, ""))) for c in keys])
        note = SPECNOTE.get(key) or {}
        title = HYPERMIG_CWK[lang]['general_table_title'] if key == 'hypermig' else t.get('title', '')
        out.append({"title": title,
                    "cols": [c["title"] for c in t["columns"]],
                    "rows": rows,
                    "source": t.get('source', {}).get('url', ''),
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


def quickFacts(lang, p):
    """Only show source values shared by every listed model and construction.

    A family overview must not present one model's fuse, current or weight as
    a specification of the whole family. Empty and unconfirmed cells stay out.
    Products without manufacturer tables retain their existing editorial data.
    """
    tables = [MAHE_SPECS[key] for key in SPECMAP.get(p['id'], []) if key in MAHE_SPECS]
    if not tables:
        return [(trK(lang, key), trV(lang, value)) for key, value in list(specRest(p).items())[:3]]
    priorities = [('Schweissstrombereich',), ('Ausgangsstrom max.',), ('Netzspannung',),
                  ('Netzabsicherung', 'Netzabsicherung (träge)'), ('Gewicht', 'Gewicht CWK'),
                  ('Schutzklasse',), ('Empfohlener Schnitt',)]
    out = []
    for alternatives in priorities:
        values, label = [], ''
        for table in tables:
            rows = [row for row in table['rows'] if _specK(row.get('model', '')) in alternatives]
            if len(rows) != 1 or rows[0].get('model') in table.get('unconfirmed_rows', []):
                break
            row = rows[0]
            cells = [_specV(row.get(column['key'], '')) for column in table['columns']]
            if not cells or any(not cell or cell == SPEC_EMPTY for cell in cells) or len(set(cells)) != 1:
                break
            values.append(cells[0])
            label = _specK(row['model'])
        if len(values) == len(tables) and len(set(values)) == 1:
            out.append((SPECROW.get(label, {}).get(lang, label), trV(lang, values[0])))
            if len(out) == 3:
                break
    return out


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


_ZUGEHOER = None


def geraeteZu(p):
    """Die Umkehrung: zu welchen Geraeten gehoert dieses Zubehoerteil.

    ACC.json steht nur in einer Richtung im Repository - vom Geraet zum Teil.
    Auf der Seite des Teils selbst stand an derselben Stelle deshalb der Satz
    „Fuer dieses Geraet ist kein spezifisches Zubehoer hinterlegt", also nichts.
    Das betraf 43 Seiten. Dabei ist die Angabe vorhanden und stammt vom
    Hersteller: 37 der 43 Teile fuehrt MAHE bei mindestens einem Geraet auf.

    Wer nach einem Brenner oder einem Kabel sucht, will genau das wissen -
    passt es an meine Maschine. Und die Seite bekommt einen Inhalt, den keine
    zweite Seite in derselben Zusammenstellung hat.
    """
    global _ZUGEHOER
    if _ZUGEHOER is None:
        _ZUGEHOER = {}
        for geraet, teile in ACC.items():
            if geraet not in BY_ID:
                continue
            for teil in teile:
                if teil in BY_ID and teil != geraet:
                    _ZUGEHOER.setdefault(teil, []).append(geraet)
    return _ZUGEHOER.get(p["id"], [])


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
    if p['id'] == 'hypermig-x':
        return HYPERMIG_CWK[lang]['family_highlights']
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
    "hypermig-x":        ["hypermig_x_graphic", "hypermig_hx", "hypermig_ecomig",
                          "hypermig_ex", "hypermig_steel", "hypermig_sx"],
    "hypermig-twin":     ["hypermig_x_graphic", "hypermig_hx"],
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
    "hypercleaner-speed": ["cleaner_speed"],
    "hypercleaner-plus": ["cleaner_plus"],
    "hypercleaner-ct200": ["ct200_panel", "ct200_syn"],
    "mlf100":            ["mlf100_panel"],
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


def panel_text(lang, p):
    """Searchable panel features and documented operating explanations."""
    out = []
    for key in fpAssign(p):
        out.append(fpName(lang, FP[key]))
        out.extend(PANEL_HL_DEVICE.get(key, {}).get(lang, []))
        guide = PANEL_GUIDES.get(key, {}).get(lang)
        if guide:
            out.extend([guide['intro'], guide['note']])
            out.extend(text for pair in guide['sections'] for text in pair)
    return ' '.join(out)


def cwk_text(lang, p):
    if p['id'] != 'hypermig-x':
        return ''
    copy = HYPERMIG_CWK[lang]
    out = [copy['title'], copy['intro'], copy['matrix_note'], copy['scope_note'], copy['technical_note']]
    for key in HYPERMIG_CWK['symbols']:
        out.extend([featLabel(lang, key), copy['symbol_notes'][key]])
    out.extend(text for pair in copy['benefits'] for text in pair)
    for row in HYPERMIG_CWK['matrix']:
        out.append(featLabel(lang, row['feature']) if row.get('feature') else copy['mma_label'])
        out.extend(f'{variant} {copy["status"][state]}' for variant, state in zip(('X', 'HX', 'EX', 'SX'), row['states']))
    return ' '.join(out)


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
           "about": "ueber-uns",
           "imprint": "impressum", "privacy": "datenschutz", "terms": "agb"},
    "fr": {"root": "fr", "products": "produits", "search": "recherche", "processes": "procedes",
           "downloads": "telechargements", "contact": "contact", "faq": "questions-frequentes",
           "service": "service",
           "about": "a-propos",
           "imprint": "mentions-legales", "privacy": "protection-des-donnees",
           "terms": "conditions-generales"},
    "it": {"root": "it", "products": "prodotti", "search": "ricerca",   "processes": "processi",
           "downloads": "download", "contact": "contatto", "faq": "domande-frequenti",
           "service": "assistenza",
           "about": "chi-siamo",
           "imprint": "note-legali", "privacy": "protezione-dati",
           "terms": "condizioni-generali"},
    "en": {"root": "en", "products": "products", "search": "search", "processes": "processes",
           "downloads": "downloads", "contact": "contact", "faq": "faq", "service": "service",
           "about": "about", "imprint": "legal-notice", "privacy": "privacy", "terms": "terms"},
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
    "en": {"repair": "repairs", "calib": "calibration", "auto": "automation"},
}
SERVICE_KEYS = ("repair", "calib", "auto")


def inquiry_options():
    """Reviewed public choices; never infer a stock item or manufacturer code."""
    known = {p["id"] for p in P}
    out = {}
    for product_id, row in INQUIRY_OPTIONS.items():
        if product_id.startswith("_"):
            continue
        if product_id not in known or not isinstance(row, dict) or row.get("kind") not in {"variant", "unit"}:
            raise ValueError("Unknown inquiry product or choice kind")
        options = row.get("options")
        if not isinstance(options, list) or not 1 <= len(options) <= 20:
            raise ValueError("Inquiry choices must be a small explicit list")
        if "availability" in row:
            stock = row["availability"]
            if (row["kind"] != "unit" or not isinstance(stock, dict)
                    or set(stock) != {"count", "confirmed_on"}
                    or type(stock["count"]) is not int or not 0 <= stock["count"] <= len(options)):
                raise ValueError("Unit availability needs an explicit bounded count")
            datetime.date.fromisoformat(stock["confirmed_on"])
        seen = set()
        for option in options:
            oid = option.get("id") if isinstance(option, dict) else None
            if not isinstance(oid, str) or not re.fullmatch(r"[a-z0-9-]{1,60}", oid) or oid in seen:
                raise ValueError("Invalid or duplicate inquiry choice")
            seen.add(oid)
            for field in ("label", "description"):
                values = option.get(field)
                if not isinstance(values, dict) or set(values) != set(LANGS):
                    raise ValueError("Inquiry choice must be translated in every language")
                if any(not isinstance(v, str) or not v.strip() or len(v) > 700 for v in values.values()):
                    raise ValueError("Invalid inquiry choice text")
        out[product_id] = row
    return out


def inquiry_services(lang):
    names = {"overview": "foot_service", "repair": "foot_diag", "calib": "foot_calib", "auto": "foot_auto"}
    return {key: {"n": t(lang, label), "u": u_service(lang, None if key == "overview" else key)}
            for key, label in names.items()}


def analytics_campaigns():
    """Finite reviewed tuples, never customer input or arbitrary URL values."""
    sources = {"linkedin", "facebook", "instagram", "tiktok", "google_business", "youtube"}
    campaigns = {"mahe-programm-2026", "occasion-microplasma-2026", "service-2026"}
    data = ANALYTICS_CAMPAIGNS
    if not isinstance(data, dict) or len(data) > 100:
        raise ValueError("Analytics campaigns must be a small registry")
    seen = set()
    for key, row in data.items():
        if not isinstance(key, str) or not re.fullmatch(r"[a-z0-9_-]{1,80}", key):
            raise ValueError("Invalid analytics campaign ID")
        if not isinstance(row, dict) or set(row) != {"source", "medium", "campaign", "content"}:
            raise ValueError("Analytics campaign must contain exactly source, medium, campaign, content")
        if any(not isinstance(value, str) or not re.fullmatch(r"[a-z0-9_-]{1,80}", value)
               for value in row.values()):
            raise ValueError("Analytics campaign values must be static public labels")
        if row["source"] not in sources or row["campaign"] not in campaigns:
            raise ValueError("Unknown analytics source or campaign")
        medium = "local_listing" if row["source"] == "google_business" else "organic_social"
        if row["medium"] != medium:
            raise ValueError("Analytics source and medium do not match")
        identity = tuple(row[field] for field in ("source", "medium", "campaign", "content"))
        if identity in seen:
            raise ValueError("Duplicate analytics campaign tuple")
        seen.add(identity)
    return data

CAT_SLUG = {
    "schweissgeraete": {"de": "schweissgeraete", "fr": "postes-de-soudage", "it": "saldatrici", "en": "welding-equipment"},
    "plasmaschneiden": {"de": "plasmaschneiden", "fr": "decoupe-plasma",    "it": "taglio-plasma", "en": "plasma-cutting"},
    "reinigung":       {"de": "reinigungsgeraete", "fr": "nettoyage",       "it": "pulizia", "en": "cleaning-equipment"},
    "zubehoer":        {"de": "zubehoer",        "fr": "accessoires",       "it": "accessori", "en": "accessories"},
    "occasion":        {"de": "occasion",        "fr": "occasion",          "it": "occasioni", "en": "used-equipment"},
}

# Sub-Slug pro Sprache aus dem übersetzten Namen
# URLs are identifiers, not editable display labels. Preserve the published
# routes when a translation gains a preposition or punctuation correction.
SUBCATEGORY_SLUGS = json.loads((BUILD / "subcategory_slugs.json").read_text("utf-8"))


def sub_slug(lang, sub):
    return SUBCATEGORY_SLUGS.get(sub, {}).get(lang) or slugify(subT(lang, sub))


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


def editorial_target(lang, ref):
    """Resolve navigation references, without extending manufacturer compatibility."""
    if not isinstance(ref, dict) or not isinstance(ref.get('id'), str):
        raise ValueError('Editorial link needs a typed catalogue identifier')
    kind, key = ref.get('kind'), ref['id']
    fields = {'kind', 'id', 'sub'} if kind == 'subcategory' else {'kind', 'id'}
    if set(ref) != fields:
        raise ValueError('Unknown or missing editorial link fields')
    if kind == 'product' and key in BY_ID:
        return pFullName(lang, BY_ID[key]), u_prod(lang, BY_ID[key])
    if kind == 'category' and key in CAT_BY_ID:
        return catT(lang, CAT_BY_ID[key]), u_cat(lang, key)
    if kind == 'subcategory' and key in CAT_BY_ID and ref['sub'] in CAT_BY_ID[key]['subs']:
        return subT(lang, ref['sub']), u_sub(lang, key, ref['sub'])
    if kind == 'service' and key in ('overview', *SERVICE_KEYS):
        label = {'overview':'foot_service', 'repair':'foot_diag',
                 'calib':'foot_calib', 'auto':'foot_auto'}[key]
        return t(lang, label), u_service(lang, None if key == 'overview' else key)
    if kind == 'page' and key in ('about', 'contact', 'imprint', 'products', 'processes'):
        label = {'about':'nav_about', 'contact':'n_contact',
                 'imprint':'nav_impressum', 'products':'nav_products', 'processes':'n_process'}[key]
        return t(lang, label), u_page(lang, key)
    raise ValueError(f'Unknown editorial link: {kind}/{key}')


def validate_editorial_guides():
    """Validate all languages and destinations before replacing generated files."""
    def links(refs):
        if not isinstance(refs, list) or not 1 <= len(refs) <= 6:
            raise ValueError('Editorial link groups need one to six references')
        for lang in LANGS:
            targets = [editorial_target(lang, ref)[1] for ref in refs]
            if len(targets) != len(set(targets)):
                raise ValueError('Duplicate editorial link destination')

    if set(HYPERMIG_CWK) != {'source', 'symbols', 'matrix', *LANGS}:
        raise ValueError('Incomplete CWK source/language structure')
    if len(HYPERMIG_CWK['symbols']) != 11 or len(set(HYPERMIG_CWK['symbols'])) != 11 or any(
            key not in FEAT for key in HYPERMIG_CWK['symbols']):
        raise ValueError('CWK needs the eleven distinct manufacturer symbols')
    states = {'listed', 'option', 'not_listed'}
    if len({row['id'] for row in HYPERMIG_CWK['matrix']}) != len(HYPERMIG_CWK['matrix']):
        raise ValueError('Duplicate CWK matrix row')
    for row in HYPERMIG_CWK['matrix']:
        if len(row['states']) != 4 or set(row['states']) - states or row.get('feature', 'mis') not in FEAT:
            raise ValueError('Invalid CWK availability matrix')
    cwk_strings = {'title', 'intro', 'symbols_title', 'benefits_title', 'matrix_title',
                   'matrix_label', 'mma_label', 'matrix_note', 'scope_note', 'technical_note',
                   'source_label', 'scroll_hint', 'summary_note', 'summary_link', 'general_table_title'}
    for lang in LANGS:
        copy = HYPERMIG_CWK[lang]
        if set(copy) != cwk_strings | {'symbol_notes', 'status', 'benefits', 'family_highlights'}:
            raise ValueError(f'Incomplete CWK language: {lang}')
        if set(copy['symbol_notes']) != set(HYPERMIG_CWK['symbols']) or set(copy['status']) != states:
            raise ValueError(f'Incomplete CWK symbols/status translation: {lang}')
        for key in cwk_strings:
            if not isinstance(copy[key], str) or not copy[key].strip():
                raise ValueError(f'Empty CWK text: {lang}/{key}')
        if any(not isinstance(value, str) or not value.strip()
               for value in [*copy['symbol_notes'].values(), *copy['status'].values(), *copy['family_highlights']]):
            raise ValueError(f'Empty CWK description: {lang}')
        if not copy['benefits'] or any(len(pair) != 2 or any(not text.strip() for text in pair)
                                       for pair in copy['benefits']):
            raise ValueError(f'Incomplete CWK benefits: {lang}')

    for key, guide in PANEL_GUIDES.items():
        if key not in FP or set(guide) != {'sources', *LANGS}:
            raise ValueError(f'Incomplete panel guide: {key}')
        if not guide['sources'] or any(
                set(source) != {'url', 'title'} or
                not source['url'].startswith('https://mahe-online.de/') or
                not source['title'].strip() for source in guide['sources']):
            raise ValueError(f'Invalid panel provenance: {key}')
        for lang in LANGS:
            copy = guide[lang]
            if set(copy) != {'intro', 'heading', 'sections', 'note', 'sources_label', 'processes_label'} or any(
                    not isinstance(copy[field], str) or not copy[field].strip()
                    for field in ('intro', 'heading', 'note', 'sources_label', 'processes_label')):
                raise ValueError(f'Incomplete panel guide language: {key}/{lang}')
            if not copy['sections'] or any(
                    not isinstance(pair, list) or len(pair) != 2 or
                    any(not isinstance(text, str) or not text.strip() for text in pair)
                    for pair in copy['sections']):
                raise ValueError(f'Invalid panel guide sections: {key}/{lang}')
            if not FP[key].get('names', {}).get(lang):
                raise ValueError(f'Missing localized panel name: {key}/{lang}')

    for pid, guide in PRODUCT_GUIDES.items():
        if pid not in BY_ID or set(guide) != {'sources', 'links', *LANGS}:
            raise ValueError(f'Incomplete product guide: {pid}')
        if not isinstance(guide['sources'], list) or not guide['sources'] or any(
                not isinstance(source, str) or not source for source in guide['sources']):
            raise ValueError(f'Missing product guide provenance: {pid}')
        links(guide['links'])
        if any(ref == {'kind':'product', 'id':pid} for ref in guide['links']):
            raise ValueError(f'Product guide links to itself: {pid}')
        for lang in LANGS:
            copy = guide[lang]
            if not isinstance(copy, dict) or set(copy) != {'intro', 'checks'}:
                raise ValueError(f'Incomplete product guide language: {pid}/{lang}')
            if not isinstance(copy['intro'], str) or not copy['intro'].strip():
                raise ValueError(f'Empty product guide intro: {pid}/{lang}')
            if not isinstance(copy['checks'], list) or not 2 <= len(copy['checks']) <= 3 or any(
                    not isinstance(text, str) or not text.strip() for text in copy['checks']):
                raise ValueError(f'Incomplete product guide checks: {pid}/{lang}')
    if set(GUIDE_LINKS) != {'categories', 'subcategories', 'services', 'company'}:
        raise ValueError('Incomplete editorial navigation groups')
    if set(GUIDE_LINKS['categories']) != set(CAT_BY_ID):
        raise ValueError('Missing category editorial navigation')
    if set(GUIDE_LINKS['subcategories']) != set(SUBCATEGORY_GUIDES):
        raise ValueError('Missing subcategory editorial navigation')
    for refs in GUIDE_LINKS['categories'].values():
        links(refs)
    for cid, subs in SUBCATEGORY_GUIDES.items():
        if set(GUIDE_LINKS['subcategories'][cid]) != set(subs):
            raise ValueError(f'Missing subcategory editorial navigation: {cid}')
        for refs in GUIDE_LINKS['subcategories'][cid].values():
            links(refs)
    if set(GUIDE_LINKS['services']) != {'overview', *SERVICE_KEYS}:
        raise ValueError('Missing service editorial navigation')
    for refs in GUIDE_LINKS['services'].values():
        links(refs)
    links(GUIDE_LINKS['company'])


def analytics_paths():
    """Known canonical routes, never a wildcard accepting arbitrary 404 paths."""
    paths = set()
    for lang in LANGS:
        paths.add(u_home(lang))
        paths.update(u_page(lang, key) for key in SEG[lang] if key != "root")
        paths.update(u_prod(lang, p) for p in P)
        paths.update(u_service(lang, key) for key in SERVICE_KEYS)
        for cat in CATS:
            paths.add(u_cat(lang, cat["id"]))
            paths.update(u_sub(lang, cat["id"], sub) for sub in cat["subs"])
    return sorted(paths)


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


def process_text(lang, process):
    """The same complete copy feeds HTML, search and machine-readable text."""
    return ' '.join(process[key][lang] for key in ('d', 'principle', 'use', 'setup'))


def validate_translations():
    """Fail before publishing if a language is missing or a template is broken."""
    def shape(reference, value, location):
        if type(reference) is not type(value):
            raise ValueError(f'Translation type differs: {location}')
        if isinstance(reference, str):
            if reference.strip() and not value.strip():
                raise ValueError(f'Empty translation: {location}')
            tokens = lambda text: set(re.findall(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}', text))
            if tokens(reference) != tokens(value):
                raise ValueError(f'Translation placeholders differ: {location}')
        elif isinstance(reference, list):
            if len(reference) != len(value):
                raise ValueError(f'Translation list is incomplete: {location}')
            for i, (a, b) in enumerate(zip(reference, value)):
                shape(a, b, f'{location}/{i}')
        elif isinstance(reference, dict):
            if set(reference) != set(value):
                raise ValueError(f'Translation fields differ: {location}')
            for key in reference:
                shape(reference[key], value[key], f'{location}/{key}')

    count = 0
    def walk(value, location):
        nonlocal count
        if isinstance(value, dict):
            if any(lang in value for lang in LANGS):
                for lang in LANGS:
                    # Some original German labels are dictionary keys, not a de member.
                    if lang != DEFAULT_LANG and lang not in value:
                        raise ValueError(f'Missing {lang} translation: {location}')
                shape(value.get('de', value['fr']), value['en'], location + '/en')
                count += 1
            else:
                for key, child in value.items():
                    if not key.startswith('_'):
                        walk(child, f'{location}/{key}')
        elif isinstance(value, list):
            for i, child in enumerate(value):
                walk(child, f'{location}/{i}')

    for path in sorted(DATA.glob('*.json')) + [BUILD / 'i18n_extra.json', BUILD / 'subcategory_slugs.json']:
        if path.name in ('_raw.json', 'products.json') or path.name.startswith('search-'):
            continue
        walk(json.loads(path.read_text('utf-8')), str(path.relative_to(ROOT)))
    return count


def validate_process_guide():
    """Reject incomplete translations, unsafe anchors and broken references before build."""
    def translated(value):
        if (not isinstance(value, dict) or set(value) != set(LANGS)
                or any(not isinstance(value[l], str) or not value[l].strip() for l in LANGS)):
            raise ValueError('Process copy needs complete DE/FR/IT/EN text')

    groups = {x['id'] for x in PROCESS_GUIDE['groups']}
    sources = {x['id'] for x in PROCESS_GUIDE['sources']}
    seen = set()
    for process in PROC:
        key = process['id']
        if not re.fullmatch(r'[a-z][a-z0-9-]*', key) or key in seen:
            raise ValueError('Invalid/duplicate process anchor')
        seen.add(key)
        if process['group'] not in groups or not process['sources'] or not set(process['sources']) <= sources:
            raise ValueError('Unknown process group/source')
        if process['ic'] is not None and (process['ic'] not in FEAT or not FEAT[process['ic']].get('img')):
            raise ValueError('Missing manufacturer process symbol')
        if not process['products'] or any(pid not in BY_ID for pid in process['products']):
            raise ValueError('Unknown process product')
        for field in ('n', 'd', 'principle', 'use', 'setup'):
            translated(process[field])
    for group in PROCESS_GUIDE['groups']:
        translated(group['n']); translated(group['d'])
        if not re.fullmatch(r'[a-z][a-z0-9-]*', group['anchor']) or group['anchor'] in seen:
            raise ValueError('Invalid process group anchor')
        seen.add(group['anchor'])
    keys = set(PROCESS_GUIDE['de'])
    for lang in LANGS:
        guide = PROCESS_GUIDE[lang]
        if set(guide) != keys:
            raise ValueError('Process guide translations differ')
        if not all(row['target'] in {p['id'] for p in PROC} for row in guide['comparison']):
            raise ValueError('Unknown process comparison target')
        for field, fields in (('comparison', ('target', 'n', 'principle', 'focus')),
                              ('glossary', ('n', 'd')), ('faq', ('q', 'a'))):
            if len(guide[field]) != len(PROCESS_GUIDE['de'][field]):
                raise ValueError('Process guide section translation is incomplete')
            for row in guide[field]:
                if set(row) != set(fields) or any(not isinstance(row[k], str) or not row[k].strip() for k in fields):
                    raise ValueError('Process guide section needs complete translated copy')
        for key, value in guide.items():
            if isinstance(value, str) and not value.strip():
                raise ValueError('Empty process guide translation')
    for source in PROCESS_GUIDE['sources']:
        translated(source['n'])
        parsed = urlsplit(source['url'])
        if parsed.username or parsed.password or parsed.scheme != 'https' or parsed.hostname not in ('mahe-online.de', 'www.twi-global.com', 'manuals.fronius.com'):
            raise ValueError('Unexpected technical source URL')
