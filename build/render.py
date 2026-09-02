#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VES-TECH Swiss — HTML-Bausteine und Seitenvorlagen.

Jede Seite wird vollständig vorgerendert ausgeliefert (kein Client-Side-Rendering
für Inhalte). Das ist die Grundlage für SEO und AEO: Crawler und Antwortmaschinen
sehen denselben Text wie ein Mensch, ohne JavaScript auszuführen.

JavaScript ist reine Anreicherung: Suche mit Autocomplete, Anfrageliste,
Schubladen, Formularversand.
"""

import base64
import hashlib
import html
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import core as C  # noqa: E402

MANIFEST = json.loads((C.ROOT / "assets/img/manifest.json").read_text("utf-8"))


def _ver(rel):
    """?v=<hash> an CSS/JS – sonst liefern Browser und CDN nach einem Deploy
    noch tagelang die alte Datei aus."""
    f = C.ROOT / rel.lstrip("/")
    if not f.exists():
        return rel
    return rel + "?v=" + hashlib.md5(f.read_bytes()).hexdigest()[:8]


# Herobilder: Breiten und Masse kommen aus assets/img/hero-manifest.json,
# erzeugt von build/hero.py. Fest verdrahtet waren sie vorher zweimal falsch:
#
#   * im srcset stand fuer hero-mpt eine Stufe "2048w", obwohl die Vorlage nur
#     1536 px breit ist - die Datei war hochgerechnet. Ein Browser auf einem
#     feinen Bildschirm waehlte genau diese Stufe und zog ein weiches Bild auf
#     die volle Breite. Deshalb wirkte die zweite Folie unscharf.
#   * width/height standen fest auf 1536x1024 fuer beide Folien. Ein Bild in
#     einem anderen Seitenverhaeltnis haette die Seite beim Umschalten
#     springen lassen.
#
# Beides kann jetzt nicht mehr auseinanderlaufen: was hier steht, steht auch
# als Datei auf der Platte. Neues Bild einspielen:
#     python3 build/hero.py hero-mpt <datei>
HERO_MANIFEST = json.loads((C.ROOT / "assets/img/hero-manifest.json").read_text("utf-8"))


def _hero(name):
    """(srcset, groesste Datei, Breite, Hoehe) fuer eine Herofolie.

    Mit ?v=<hash> wie bei CSS und JS. Die Dateinamen der Herobilder aendern
    sich beim Austausch nicht - ohne diesen Anhang sah ein wiederkehrender
    Besucher noch tagelang das alte Bild aus seinem Zwischenspeicher. Bei den
    Produktbildern waere derselbe Anhang unnoetig: die heissen nach dem Inhalt
    ihrer Vorlage und aendern sich ohnehin mit.
    """
    m = HERO_MANIFEST[name]
    stufen = m["sizes"]
    srcset = ", ".join(_ver(f"/assets/img/{name}-{s}.webp") + f" {s}w" for s in stufen)
    return (srcset, _ver(f"/assets/img/{name}-{stufen[-1]}.webp"), m["w"], m["h"])


HERO_SRCSET, HERO_SRC, HERO_W, HERO_H = _hero("hero")

# Das Hero ist das LCP-Element der Startseite. Ohne preload findet der Browser
# es erst, nachdem er CSS geparst hat – mit preload startet der Download sofort.
HERO_PRELOAD = (f'<link rel="preload" as="image" href="{HERO_SRC}" '
                f'imagesrcset="{HERO_SRCSET}" imagesizes="100vw" fetchpriority="high">')

# Zweite Herofolie: der Plasmaschneidtisch. Sie wird NICHT vorgeladen - das
# erste Bild bleibt das LCP-Element.
#
# Sie stand aber auch auf loading="lazy", und das war falsch: die Folie liegt
# uebereinander mit der ersten und ist mit visibility:hidden ausgeblendet.
# Ein Browser holt ein solches Bild ueberhaupt nicht - gemessen am 05.08.2026
# war es nach sieben Sekunden noch immer nicht geladen. Nach dem Umschalten
# bei Sekunde 5 sah man also erst eine weisse Flaeche, bis 137 kB nachgeladen
# waren. Jetzt: loading="eager" mit fetchpriority="low" - der Browser holt es,
# aber erst wenn das Wichtige durch ist.
HERO2_SRCSET, HERO2_SRC, HERO2_W, HERO2_H = _hero("hero-mpt")

CSS_URL = _ver("/assets/css/site.css")
JS_URL = _ver("/assets/js/app.js")

# --------------------------------------------------------------------------
# Sicherheit im <head>
#
# GitHub Pages laesst keine eigenen HTTP-Kopfzeilen zu. Was per <meta> geht,
# steht hier; was nur als Kopfzeile ginge (X-Frame-Options,
# X-Content-Type-Options, HSTS), geht auf dieser Plattform gar nicht.
#
# Die Richtlinie ist so eng, wie es die Seite zulaesst. Gemessen am 12.08.2026:
# alle Ressourcen kommen von der eigenen Domain, ausser den Herstellerbildern
# von mahe-online.de (Rueckfall, wenn eine lokale Kopie fehlt) und dem
# Formulardienst api.web3forms.com.
#
# Seit dem 12.08.2026 kommt die Richtlinie ohne 'unsafe-inline' aus - weder
# fuer Skripte noch fuer Stile. Das war vorher nicht moeglich und hat drei
# Aenderungen gebraucht:
#
#   1. Die 1530 onerror-Attribute an den Bildern sind weg. Der Rueckfall steht
#      jetzt als data-fb="…" am Bild, und app.js hoert einmal zentral auf
#      error-Ereignisse. Ereignisattribute lassen sich grundsaetzlich nicht
#      per Hash erlauben - solange auch nur eines im HTML stand, war
#      script-src 'unsafe-inline' unvermeidlich.
#   2. window.VT haengt nur an der Sprache, nicht an der Seite. Es gibt also
#      genau drei verschiedene Startskripte, und jede Seite traegt den Hash
#      ihres eigenen.
#   3. Der <noscript>-Block der Produktseiten ist eine einzige, feste
#      Zeichenkette (NOSCRIPT_CSS) - ein Hash deckt alle 231 Seiten ab.
#
# Der Gewinn ist nicht theoretisch: mit 'unsafe-inline' darf jedes Skript
# laufen, das es irgendwie ins HTML schafft. Ohne es laeuft nur, was exakt
# einem hinterlegten Hash entspricht. Ein eingeschleuster <script>-Block ist
# damit wirkungslos, auch wenn er im Markup landet.
# Ohne JavaScript gibt es kein Umschalten - dann sollen alle Folien
# untereinander stehen und die Reiter offen sein. Die Zeichenkette wird per
# sha256 in der CSP jeder Produktseite erlaubt (siehe csp()); wer sie aendert,
# aendert damit auch den Hash. Ein zusaetzliches Leerzeichen genuegt, und der
# Browser wendet den Block nicht mehr an.
NOSCRIPT_CSS = (".tabpane{display:block!important}.tabbar{display:none}\n"
                "    .galslide{display:grid!important;place-items:center;"
                "gap:12px;margin-bottom:18px}\n"
                "    .galnav,.galthumbs{display:none}")

# Der Bildrueckfall. Fehlt die lokale Kopie eines Herstellerbildes, laedt das
# Bild stattdessen das Original von mahe-online.de; die Adresse steht als
# data-fb am <img>.
#
# Warum das hier im <head> steht und nicht in app.js:
#
# error-Ereignisse feuern genau einmal. app.js laeuft mit defer, also erst
# nachdem der Parser das Dokument gelesen hat - bis dahin koennen Bilder
# laengst gescheitert sein, und ihr Ereignis ist dann verloren. Der naechste
# Gedanke waere, gescheiterte Bilder beim Start nachzuschlagen: complete ===
# true und naturalWidth === 0 gilt als kaputt. Am 12.08.2026 gemessen: dieses
# Paar ist nicht verlaesslich. Bei decoding="async" meldet der Browser fuer
# voellig intakte Bilder complete === true, waehrend naturalWidth noch 0 ist -
# auch noch bei window.load. Das Hauptbild jeder Produktseite wurde dadurch
# faelschlich als kaputt eingestuft und gegen das Bild von mahe-online.de
# getauscht, obwohl die lokale Kopie mit 200 ausgeliefert wurde. Jeder
# Besucher haette Bilder von einem fremden Server geholt, langsamer und mit
# seiner IP-Adresse.
#
# Im <head>, vor dem ersten <img>, entfaellt das Raten: kein error-Ereignis
# kann mehr verloren gehen, und es wird nur zurueckgefallen, wenn wirklich
# eines gefeuert hat. Ereignisse steigen bei Ressourcen nicht auf, wohl aber
# in der Erfassungsphase - daher das true.
#
# Kosten, damit niemand eine Ersparnis hineinliest: die 1530 onerror-Attribute
# waren rund 230 kB, ihr Ersatz data-fb ist kleiner - aber dieses Skript und
# die beiden Hashes in der Richtlinie kommen auf jeder der 347 Seiten dazu.
# Unterm Strich ist die Website 33 kB groesser als vorher. Bezahlt wird damit
# eine Richtlinie ohne 'unsafe-inline'; das ist es wert, eine Ersparnis ist es
# nicht.
IMG_FALLBACK_JS = (
    'addEventListener("error",function(e){var t=e.target;'
    'if(t&&t.tagName==="IMG"&&t.dataset.fb&&!t.dataset.fbDone){'
    't.dataset.fbDone="1";t.removeAttribute("srcset");t.removeAttribute("sizes");'
    't.src=t.dataset.fb}},true)'
)


def sri_hash(text):
    """Der CSP-Hash einer Inline-Zeichenkette: sha256, base64, in Anfuehrung.

    Gehasht wird genau der Text zwischen den Tags - kein Zeichen mehr, keines
    weniger. Ein zusaetzliches Leerzeichen im HTML macht den Hash ungueltig
    und das Skript stumm; deshalb entstehen Skript und Hash in dieser Datei
    aus derselben Zeichenkette.
    """
    d = hashlib.sha256(text.encode("utf-8")).digest()
    return "'sha256-" + base64.b64encode(d).decode("ascii") + "'"


def csp(lang):
    return "; ".join([
        "default-src 'self'",
        "base-uri 'self'",
        "object-src 'none'",
        "frame-src 'none'",
        "img-src 'self' https://mahe-online.de",
        f"script-src 'self' {sri_hash(IMG_FALLBACK_JS)} {sri_hash(boot_json(lang))}",
        f"style-src 'self' {sri_hash(NOSCRIPT_CSS)}",
        "font-src 'self'",
        "connect-src 'self' https://api.web3forms.com",
        "form-action 'self'",
        # frame-ancestors steht bewusst nicht hier: per <meta> ignorieren es
        # alle Browser und melden es als Warnung in der Konsole. Gegen
        # Einbetten in fremde Seiten hilft auf GitHub Pages nichts.
        "upgrade-insecure-requests",
    ])


def security_meta(lang):
    return (
        f'<meta http-equiv="Content-Security-Policy" content="{e(csp(lang))}">\n'
        # Beim Klick auf ein Herstellerdokument erfaehrt mahe-online.de sonst,
        # von welcher Unterseite aus verlinkt wurde. Der Domainname genuegt.
        '<meta name="referrer" content="strict-origin-when-cross-origin">'
    )


# --------------------------------------------------------------------------
# Kleine Helfer
# --------------------------------------------------------------------------

def e(s):
    """HTML-escape für Text."""
    return html.escape(str(s if s is not None else ""), quote=True)


def jsonld(obj):
    return ('<script type="application/ld+json">'
            + json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
            + "</script>")


# Welches Seitenverhaeltnis der Bildrahmen einer Produktseite bekommt.
#
# Der Rahmen war bis zum 12.08.2026 immer quadratisch; gemessen ueber alle 77
# Produktbilder blieb er dadurch im Schnitt zu 31 % leer, beim MPT zu 56 %.
# Ihn stattdessen vom Bild wachsen zu lassen (height:auto) war der erste
# Versuch und ein Rueckschritt: ein <img> mit width:auto reserviert vor dem
# Laden keinen Platz. Nachgemessen mit einem absichtlich gebremsten Server:
# der Rahmen stand bei 56 px - nur das Polster - und sprang beim Eintreffen des
# Bildes auf 357 px. Die ganze Seite darunter ruckte um 301 px. Genau das misst
# Google als Layoutverschiebung.
#
# Deshalb traegt der Rahmen ein festes Verhaeltnis, das der Build aus dem
# Manifest waehlt. Es steht im Stylesheet als Klasse - ein style-Attribut ginge
# nicht, die Richtlinie erlaubt keine Inline-Stile. Das Bild darin fuellt
# hoechstens 90 % in beiden Richtungen, also bleibt ringsum Luft, und bei
# passendem Eimer beruehrt es beide Grenzen zugleich: kein Balken, kein Sprung.
#
# Verschnitt im Rahmen mit diesen sieben Eimern: 10 % im Schnitt statt 31 %.
# Hohe Bilder (die Elektrolytflaschen stehen 1:3) laufen bewusst in "hoch" und
# behalten Luft an den Seiten - ein Rahmen in ihrem echten Verhaeltnis waere
# bei 590 px Breite 1770 px hoch.
DIMG_EIMER = [
    (0.47, "ar-weit"),      # 25/11 - Massekabel, MLF 100
    (0.62, "ar-kino"),      # 16/9  - MPT 3001 und 2501
    (0.72, "ar-quer"),      # 3/2
    (0.80, "ar-foto"),      # 4/3
    (0.94, "ar-fast"),      # 8/7
    (1.10, ""),             # 1/1   - Vorgabe im Stylesheet
]


def dimg_klasse(*pfade):
    """Der Eimer fuer einen Rahmen. Bei mehreren Bildern zaehlt das hoechste.

    Eine Galerie hat einen Rahmen fuer alle Folien. Waehlt man ihn nach der
    ersten, werden die anderen abgeschnitten - beim MLF 100 gemessen: die
    beiden Hochformate wurden 619 und 638 px hoch in einem 260 px hohen
    Rahmen. Also bestimmt die hoechste Folie, und die breite bekommt Luft
    darueber und darunter.
    """
    verhaeltnisse = [m["ratio"] for m in (MANIFEST.get(C.full_img(p)) for p in pfade)
                     if m and m.get("ratio")]
    if not verhaeltnisse:
        return ""
    ratio = max(verhaeltnisse)
    for grenze, klasse in DIMG_EIMER:
        if ratio <= grenze:
            return (" " + klasse) if klasse else ""
    return " ar-hoch"        # 5/6


def img_tag(path, sizes, cls="", alt="", eager=False, width=None):
    """<img> mit WebP-Srcset, Massen gegen CLS und Remote-Fallback."""
    m = MANIFEST.get(C.full_img(path))
    remote = C.REMOTE_IMG + C.full_img(path)
    if not m:
        return (f'<img class="{cls}" src="{e(remote)}" alt="{e(alt)}" '
                f'referrerpolicy="no-referrer" loading="lazy" decoding="async">')
    k = m["key"]
    nat = m.get("w") or 1000
    # images.py skaliert nie hoch: die Datei "-1000.webp" ist bei einer 242 px
    # breiten Vorlage auch nur 242 px breit. Stand im srcset trotzdem "1000w",
    # hielt der Browser sie fuer hochaufloesend und zog sie auf die volle
    # Anzeigebreite – der Brenner MT200W sah dadurch unscharf aus. Deshalb hier
    # die tatsaechlichen Breiten, und angezeigt wird hoechstens so gross, wie
    # die Vorlage wirklich ist.
    w = min(width or 400, nat)
    h = int(round(w * m["ratio"]))
    # Frontpanels kommen direkt vom Hersteller und liegen lokal; Produktbilder
    # stammen von mahe-online.de und behalten dorthin einen Rückfall.
    folder = "panels" if m.get("local") else "p"
    # Welche Breiten es wirklich gibt, steht im Manifest. Frueher standen hier
    # fest 400 und 1000; bei einer 4800 px breiten Vorlage blieb das Bild
    # dadurch auf 1000 px stehen und wirkte auf feinen Bildschirmen weich.
    # Ohne Eintrag im Manifest gilt weiter das alte Paar 400/1000, wobei die
    # 1000er Datei bei schmaleren Vorlagen nur so breit ist wie die Vorlage.
    # Sie einfach wegzulassen, sobald 1000 > nat ist, haette 160 Seiten die
    # groessere Stufe genommen - gemessen an einem Vorher/Nachher-Vergleich
    # aller 348 Seiten.
    stufen = m.get("sizes") or ([400] + ([1000] if nat > 400 else []))
    small = f"/assets/img/{folder}/{k}-{stufen[0]}.webp"
    srcset = ", ".join(f"/assets/img/{folder}/{k}-{s}.webp {min(s, nat)}w"
                       for s in stufen)
    klein = min(stufen[0], nat)
    if nat < (width or 400):
        sizes = f"{w}px"          # das Bild fuellt den Platz gar nicht aus
    # Das eager geladene Bild ist auf Produktseiten das LCP-Element. Ohne
    # fetchpriority stuft der Browser Bilder anfangs niedrig ein und hebt sie
    # erst nach dem Layout an - die schwerste und sichtbarste Datei startet
    # damit hinter Schriften und CSS. Das Hero der Startseite bekommt diese
    # Auszeichnung seit jeher (render.py::HERO_PRELOAD), das Produktbild nicht.
    loading = 'fetchpriority="high" ' if eager else 'loading="lazy" '
    # Rueckfall auf das Herstellerbild, falls die lokale Kopie fehlt: nur die
    # Adresse steht am Bild, das Verhalten liegt in app.js (bildRueckfall).
    # Frueher stand hier ein onerror-Attribut - 1530 Stueck ueber die Seite
    # verteilt, rund 230 kB, und sie zwangen die CSP zu 'unsafe-inline'.
    fb = "" if m.get("local") else f' data-fb="{e(remote)}"'
    return (
        f'<img class="{cls}" src="{small}" '
        f'srcset="{srcset}" sizes="{e(sizes)}" '
        f'width="{w}" height="{h}" alt="{e(alt)}" '
        f'{loading}decoding="async" referrerpolicy="no-referrer"'
        + fb + ">"
    )


def img_step(m, wunsch):
    """Die vorhandene Stufe, die dem Wunsch am naechsten kommt.

    Seit die Dateien nach ihrer echten Breite heissen, gibt es zu einer 792 px
    breiten Vorlage kein "-1000.webp" mehr. Wer die Groesse fest verdrahtet,
    verlinkt ins Leere - genau das taten og:image, das Bild im JSON-LD, die
    Anfrageliste und das Suchergebnisbild.
    """
    stufen = m.get("sizes") or ([400] + ([1000] if (m.get("w") or 0) > 400 else []))
    passend = [x for x in stufen if x <= wunsch]
    return max(passend) if passend else min(stufen)


def img_folder(m):
    """Herstellerbilder liegen unter p/, selbst gelieferte unter panels/.

    Stand nur img_tag richtig, zeigten og:image, das Product-Bild im JSON-LD,
    das Bild in der Anfrageliste und das Suchergebnisbild eines lokalen Bildes
    auf assets/img/p/, wo nichts liegt – ohne dass check.py etwas meldete.
    """
    return "panels" if m.get("local") else "p"


def img_abs(path, size=1000):
    """Absolute URL des lokalen Bildes – für og:image und JSON-LD."""
    m = MANIFEST.get(C.full_img(path))
    if not m:
        return C.REMOTE_IMG + C.full_img(path)
    return f"{C.SITE}/assets/img/{img_folder(m)}/{m['key']}-{img_step(m, size)}.webp"


# --------------------------------------------------------------------------
# JSON-LD-Bausteine
# --------------------------------------------------------------------------

def ld_org(lang=C.DEFAULT_LANG):
    co = C.COMPANY
    vis = C.WORKSHOP
    return {
        "@type": ["Organization", "LocalBusiness", "Store"],
        "@id": f"{C.SITE}/#organization",
        "name": co["name"],
        "legalName": co["legal_name"],
        # Ohne Beschreibung muss sich eine Suchmaschine ihr Bild der Firma aus
        # dem Seitentext zusammenreimen. Google hat daraus geschlossen, unter
        # der Adresse stehe kein aktiver Schweizer Firmenauftritt, und auf
        # Fassadenbauer mit aehnlichem Namen verwiesen.
        "description": C.t(lang, "org_desc"),
        "url": C.SITE + "/",
        "logo": {"@type": "ImageObject", "url": f"{C.SITE}/assets/icons/logo.png",
                 "width": 512, "height": 512},
        "image": f"{C.SITE}/assets/img/hero.jpg",
        "telephone": co["phone"],
        "email": co["email"],
        # Besucheradresse, nicht Rechnungsadresse: hier wird Kundschaft
        # empfangen, und genau diese Anschrift steht im Google-
        # Unternehmensprofil. Weichen Profil und Website voneinander ab,
        # bestaetigt Google den Eintrag nicht. Die Rechnungsadresse in
        # Bronschhofen steht im Impressum und auf der Kontaktseite.
        "address": {
            "@type": "PostalAddress",
            "streetAddress": vis["street"],
            "postalCode": vis["zip"],
            "addressLocality": vis["city"],
            "addressRegion": vis["region"],
            "addressCountry": "CH",
        },
        "geo": {"@type": "GeoCoordinates", "latitude": vis["lat"], "longitude": vis["lon"]},
        # Kein openingHoursSpecification: die Zeiten unten sind die telefonische
        # Erreichbarkeit des Inhabers, nicht die Oeffnungszeiten der Werkstatt in
        # Herisau. Als Oeffnungszeiten am LocalBusiness ausgegeben, wuerden sie
        # mit dem Google-Unternehmensprofil kollidieren, sobald dort andere
        # Zeiten stehen. Sie gehoeren an den ContactPoint - da stimmen sie.
        "areaServed": [{"@type": "Country", "name": "Schweiz"},
                       {"@type": "Country", "name": "Liechtenstein"}],
        # Sprachen, in denen beraten wird - nicht zu verwechseln mit den
        # Sprachen der Website (die stehen als inLanguage am WebSite-Knoten).
        "knowsLanguage": ["de", "cs", "en"],
        "currenciesAccepted": "CHF",
        # Karte zur Werkstatt. Google verknuepft damit Website und Ort; wer die
        # Seite auf dem Telefon liest, kommt mit einem Tippen zur Navigation.
        "hasMap": C.MAP_URL,
        # Leer, solange es keine Profile gibt - siehe core.py::SAMEAS.
        **({"sameAs": C.SAMEAS} if C.SAMEAS else {}),
        "brand": {"@type": "Brand", "name": C.BRAND, "url": C.BRAND_URL},
        "founder": {"@type": "Person", "name": co["owner"]},
        "slogan": C.t("de", "brand_claim"),
        "knowsAbout": [
            "MIG/MAG-Schweissen", "WIG/TIG-Schweissen", "MMA-Elektrodenschweissen",
            "Plasmaschneiden", "Elektrolytische Schweissnahtreinigung",
            "Schweissautomation", "EN 1090", "MAHE Schweissgeräte",
        ],
        "contactPoint": [{
            "@type": "ContactPoint",
            "contactType": "sales",
            "telephone": co["phone"],
            "email": co["email"],
            "availableLanguage": ["German", "Czech", "English"],
            "areaServed": ["CH", "LI"],
            "hoursAvailable": [
                {"@type": "OpeningHoursSpecification", "dayOfWeek": h["days"],
                 "opens": h["opens"], "closes": h["closes"]} for h in co["hours_schema"]
            ],
        }],
    }


def ld_website(lang):
    return {
        "@type": "WebSite",
        "@id": f"{C.SITE}/#website",
        "url": C.SITE + "/",
        "name": C.t(lang, "site_name"),
        "description": C.t(lang, "home_desc"),
        "inLanguage": [C.EX[l]["hreflang"] for l in C.LANGS],
        "publisher": {"@id": f"{C.SITE}/#organization"},
        "potentialAction": {
            "@type": "SearchAction",
            "target": {"@type": "EntryPoint",
                       "urlTemplate": f"{C.SITE}{C.u_page(lang, 'search')}?q={{search_term_string}}"},
            "query-input": "required name=search_term_string",
        },
    }


def ld_breadcrumb(items):
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n,
             **({"item": C.abs_url(u)} if u else {})}
            for i, (n, u) in enumerate(items)
        ],
    }


def ld_product(lang, p):
    cat = C.CAT_BY_ID[p["cat"]]
    url = C.abs_url(C.u_prod(lang, p))
    props = [{"@type": "PropertyValue", "name": C.trK(lang, k), "value": C.trV(lang, v)}
             for k, v in C.specRest(p).items()]
    # Die MAHE-Tabelle hat eine Spalte je Variante, PropertyValue kennt nur ein
    # Wertfeld. Also je Zeile die Variante mitschreiben — "Netzabsicherung (300)"
    # -> "20A". Wo alle Varianten denselben Wert haben (Schutzklasse, CE …),
    # steht die Zeile einmal ohne Variante statt sechsmal gleich.
    for t in C.specTables(lang, p):
        for r in t["rows"]:
            vals = [v for v in r[1:] if v != C.SPEC_EMPTY]
            if not vals:
                continue
            if len(set(vals)) == 1:
                props.append({"@type": "PropertyValue", "name": r[0], "value": vals[0]})
                continue
            for col, val in zip(t["cols"], r[1:]):
                if val != C.SPEC_EMPTY:
                    props.append({"@type": "PropertyValue",
                                  "name": f"{r[0]} ({col})", "value": val})
    hl = C.highlightsOf(lang, p)
    d = {
        "@type": "Product",
        "@id": url + "#product",
        "name": f"{C.BRAND} {C.pName(lang, p)}",
        "alternateName": C.pName(lang, p),
        "sku": p["id"].upper(),
        "mpn": p["id"].upper(),
        "url": url,
        "description": C.pDesc(lang, p),
        "image": [img_abs(p["img"], 1000)],
        "brand": {"@type": "Brand", "name": C.BRAND, "url": C.BRAND_URL},
        "manufacturer": {"@type": "Organization", "name": "MAHE GmbH", "url": C.BRAND_URL},
        "category": f"{C.catT(lang, cat)} > {C.subT(lang, p['sub'])}",
        "inLanguage": C.EX[lang]["hreflang"],
        "additionalProperty": props,
        # Preis auf Anfrage: bewusst KEIN price-Feld, und deshalb seit dem
        # 05.08.2026 auch KEIN offers-Knoten mehr.
        #
        # Hier stand ein Offer mit priceCurrency "CHF", aber ohne price. Eine
        # Waehrung ohne Betrag ist kein Angebot, sondern ein halbes: jeder
        # Validator meldet das fehlende Pflichtfeld, und Google zeigt ein Offer
        # ohne Preis ohnehin nicht an. Der Knoten kostete also 231 Fehlermeldungen
        # und brachte nichts. Ein erfundener Preis kaeme nicht in Frage - die
        # Regel "keine Preise" ist der Kern dieses Katalogs.
        #
        # Was das Angebot ausmacht, steht weiterhin da: sichtbar "Preis auf
        # Anfrage" auf jeder Seite, das Liefergebiet CH/LI am Organization-
        # Knoten, und die Anfrageliste als Weg zum Angebot. Ein "seller" waere
        # hier uebrigens falsch - das ist eine Eigenschaft von Offer, nicht
        # von Product.
    }
    if hl:
        d["additionalProperty"] = props + [
            {"@type": "PropertyValue", "name": C.t(lang, "highlights"), "value": x} for x in hl
        ]
    return d


def ld_itemlist(lang, products, name):
    return {
        "@type": "ItemList",
        "name": name,
        "numberOfItems": len(products),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "url": C.abs_url(C.u_prod(lang, p)),
             "name": f"{C.BRAND} {p['name']}"}
            for i, p in enumerate(products)
        ],
    }


def ld_faq(lang):
    return {
        "@type": "FAQPage",
        "@id": C.abs_url(C.u_page(lang, "faq")) + "#faq",
        "inLanguage": C.EX[lang]["hreflang"],
        "mainEntity": [
            {"@type": "Question", "name": q["q"],
             "acceptedAnswer": {"@type": "Answer", "text": q["a"]}}
            for q in C.EX[lang]["faq"]
        ],
    }


def ld_faq_subset(lang, items, url):
    """FAQ-Auszug (z. B. die ersten sechs Fragen auf der Startseite)."""
    return {
        "@type": "FAQPage",
        "@id": C.abs_url(url) + "#faq",
        "inLanguage": C.EX[lang]["hreflang"],
        "mainEntity": [
            {"@type": "Question", "name": q["q"],
             "acceptedAnswer": {"@type": "Answer", "text": q["a"]}}
            for q in items
        ],
    }


def ld_about(lang, url, title, desc):
    """AboutPage samt Person des Inhabers.

    Google braucht bei einem Einzelunternehmen einen Anhaltspunkt, wer hinter
    der Firma steht. Der Person-Knoten haengt als founder am Organization-
    Knoten und traegt dieselbe Adresse - so ist die Verbindung explizit statt
    nur im Fliesstext.
    """
    person = {
        "@type": "Person",
        "@id": f"{C.SITE}/#inhaber",
        "name": C.COMPANY["owner"],
        "jobTitle": C.t(lang, "about_role"),
        "worksFor": {"@id": f"{C.SITE}/#organization"},
        "knowsLanguage": ["de", "cs", "en"],
        "workLocation": {
            "@type": "Place",
            "name": C.WORKSHOP["partner"],
            "address": {"@type": "PostalAddress",
                        "streetAddress": C.WORKSHOP["street"],
                        "postalCode": C.WORKSHOP["zip"],
                        "addressLocality": C.WORKSHOP["city"],
                        "addressRegion": C.WORKSHOP["region"],
                        "addressCountry": "CH"},
        },
    }
    seite = ld_webpage(lang, url, title, desc,
                       extra={"@type": "AboutPage", "mainEntity": {"@id": f"{C.SITE}/#organization"}})
    return [seite, person]


def ld_webpage(lang, url, title, desc, extra=None):
    d = {
        "@type": "WebPage",
        "@id": C.abs_url(url) + "#webpage",
        "url": C.abs_url(url),
        "name": title,
        "description": desc,
        "inLanguage": C.EX[lang]["hreflang"],
        "isPartOf": {"@id": f"{C.SITE}/#website"},
        "about": {"@id": f"{C.SITE}/#organization"},
        "primaryImageOfPage": {"@type": "ImageObject", "url": f"{C.SITE}/assets/img/hero.jpg"},
    }
    if extra:
        d.update(extra)
    return d


# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------

FONTS_URL = _ver("/assets/fonts/fonts.css")

# Diese vier Schnitte stehen auf jeder Seite über dem Falz – preload startet
# ihren Download vor dem CSS-Parsing. crossorigin ist bei Schriften auch für
# dieselbe Herkunft Pflicht.
#
#   Inter            Fliesstext
#   Anton            Wortmarke VES-TECH
#   DM Serif Display die H1 jeder Seite. Sie stand bis zum 05.08.2026 nicht
#                    hier - der grösste Text der Seite wurde also erst nach dem
#                    CSS neu gezeichnet.
#   Barlow Cond. 700 Navigation, Schaltflächen, Tabellenköpfe; mit 66 Stellen
#                    die meistbenutzte Familie im Stylesheet.
#
# Nur die latin-Schnitte: latin-ext holt der Browser dank unicode-range
# ohnehin nur, wenn ein Zeichen daraus vorkommt.
FONT_PRELOAD = (
    '<link rel="preload" as="font" type="font/woff2" crossorigin '
    'href="/assets/fonts/inter-400-700-latin.woff2">\n'
    '<link rel="preload" as="font" type="font/woff2" crossorigin '
    'href="/assets/fonts/anton-400-latin.woff2">\n'
    '<link rel="preload" as="font" type="font/woff2" crossorigin '
    'href="/assets/fonts/dm-serif-display-400-latin.woff2">\n'
    '<link rel="preload" as="font" type="font/woff2" crossorigin '
    'href="/assets/fonts/barlow-condensed-700-latin.woff2">'
)


def head(lang, *, title, desc, url, alts, jsonld_blocks, og_image=None,
         og_type="website", robots="index,follow,max-image-preview:large", extra_head=""):
    alt_links = "\n".join(
        f'<link rel="alternate" hreflang="{C.EX[l]["hreflang"]}" href="{e(C.abs_url(u))}">'
        for l, u in alts.items()
    )
    alt_links += f'\n<link rel="alternate" hreflang="x-default" href="{e(C.abs_url(alts[C.DEFAULT_LANG]))}">'
    verification = ""
    if C.GOOGLE_SITE_VERIFICATION:
        verification += f'<meta name="google-site-verification" content="{e(C.GOOGLE_SITE_VERIFICATION)}">\n'
    if C.BING_SITE_VERIFICATION:
        verification += f'<meta name="msvalidate.01" content="{e(C.BING_SITE_VERIFICATION)}">\n'
    verification = verification.rstrip("\n")
    graph = {"@context": "https://schema.org", "@graph": jsonld_blocks}
    og_image = og_image or f"{C.SITE}/assets/img/hero.jpg"
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{security_meta(lang)}
<script>{IMG_FALLBACK_JS}</script>
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="{e(robots)}">
<link rel="canonical" href="{e(C.abs_url(url))}">
{alt_links}
<meta name="author" content="{e(C.COMPANY['name'])}">
<meta name="geo.region" content="CH-{C.WORKSHOP['region']}">
<meta name="geo.placename" content="{e(C.WORKSHOP['city'])}">
<meta name="geo.position" content="{C.WORKSHOP['lat']};{C.WORKSHOP['lon']}">
<meta name="ICBM" content="{C.WORKSHOP['lat']}, {C.WORKSHOP['lon']}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{e(C.t(lang,'site_name'))}">
<meta property="og:locale" content="{C.EX[lang]['locale']}">
{"".join(f'<meta property="og:locale:alternate" content="{C.EX[l]["locale"]}">' for l in C.LANGS if l != lang)}
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(C.abs_url(url))}">
<meta property="og:image" content="{e(og_image)}">
<meta property="og:image:alt" content="{e(title)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{e(og_image)}">
<meta name="theme-color" content="#E0511A">
{verification}
<link rel="icon" href="/assets/icons/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/icons/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
{FONT_PRELOAD}
<link rel="stylesheet" href="{FONTS_URL}">
<link rel="stylesheet" href="{CSS_URL}">
{extra_head}
{jsonld(graph)}"""


def lang_switch(lang, alts):
    out = []
    for l in C.LANGS:
        cur = "true" if l == lang else "false"
        out.append(f'<a href="{e(alts[l])}" hreflang="{C.EX[l]["hreflang"]}" '
                   f'aria-current="{ "true" if l==lang else "false" }" '
                   f'data-lang="{l}" aria-pressed="{cur}" '
                   f'title="{e(C.EX[l]["lang_name"])}">{l.upper()}</a>')
    return "".join(out)


def mega(lang):
    """Hauptnavigation. Alle Ziele sind echte <a href> – crawlbar, auch wenn
    das Akkordeon per CSS eingeklappt ist."""
    blocks = []
    for c in C.CATS:
        rows = [f'<a href="{e(C.u_cat(lang, c["id"]))}"><span class="num">00</span>'
                f'<b>{e(C.t(lang, "chip_all"))}</b><span aria-hidden="true">→</span></a>']
        for i, s in enumerate(c["subs"], 1):
            rows.append(
                f'<a href="{e(C.u_sub(lang, c["id"], s))}"><span class="num">{i:02d}</span>'
                f'<b>{e(C.subT(lang, s))}</b><span aria-hidden="true">→</span></a>'
            )
        blocks.append(
            f'<div class="mgroup"><button type="button" aria-expanded="false">'
            f'<span>{e(C.catT(lang, c))}</span><span class="chev" aria-hidden="true">▸</span>'
            f'</button><div class="sub">{"".join(rows)}</div></div>'
        )
    for name, url in [
        (C.t(lang, "n_process"),   C.u_page(lang, "processes")),
        (C.t(lang, "n_downloads"), C.u_page(lang, "downloads")),
        (C.t(lang, "nav_faq"),     C.u_page(lang, "faq")),
        (C.t(lang, "nav_about"),   C.u_page(lang, "about")),
        (C.t(lang, "n_contact"),   C.u_page(lang, "contact")),
    ]:
        blocks.append(
            f'<div class="mgroup"><a class="mlink" href="{e(url)}">'
            f'<span>{e(name)}</span><span class="chev" aria-hidden="true">→</span></a></div>'
        )
    return f"""<aside class="mega" id="mega" aria-label="{e(C.t(lang,'menu_aria'))}" aria-hidden="true">
  <div class="top"><span class="t">{e(C.t(lang,'menu_title'))}</span>
    <button class="x" type="button" data-close="mega" aria-label="✕">✕</button></div>
  <nav class="scroll" id="megaScroll" aria-label="{e(C.t(lang,'menu_aria'))}">{"".join(blocks)}</nav>
  <div class="foot"><a class="pri" href="{e(C.u_page(lang,'contact'))}">{e(C.t(lang,'m_inquire'))}</a>
    <a href="{e(C.u_products(lang))}">{e(C.t(lang,'m_all'))}</a></div>
</aside>"""


def header(lang, alts):
    co = C.COMPANY
    vis = C.WORKSHOP
    return f"""<a class="skip" href="#main">{e(C.t(lang,'skip_link'))}</a>
<div class="util"><div class="wrap">
  <div class="l"><a href="tel:{co['phone_href']}">{e(co['phone'])}</a>
    <a class="adr" href="{e(C.u_page(lang,'contact'))}">
      <span class="adr-str">{e(vis['street'])},</span>
      <span class="adr-ort">{vis['zip']} {e(vis['city'])}</span></a></div>
  <nav class="langs" aria-label="{e(C.t(lang,'lang_aria'))}">{lang_switch(lang, alts)}</nav>
</div></div>

<header>
  <div class="wrap head">
    <a class="logo" href="{e(C.u_home(lang))}" aria-label="{e(C.t(lang,'site_name'))}">
      <span class="name">VES<i>-</i>TECH</span><span class="flag" aria-hidden="true"></span></a>
    <form class="hsearch" role="search" action="{e(C.u_page(lang,'search'))}" method="get"
          id="searchForm" autocomplete="off">
      <input id="q" name="q" type="search" placeholder="{e(C.t(lang,'search_ph'))}"
             aria-label="{e(C.t(lang,'c_search'))}" role="combobox" aria-expanded="false"
             aria-controls="sugg" aria-autocomplete="list" spellcheck="false">
      <button type="submit">{e(C.t(lang,'search_btn'))}</button>
      <div class="sugg" id="sugg" role="listbox" aria-label="{e(C.t(lang,'search_aria_listbox'))}" hidden></div>
    </form>
    <div class="hactions">
      <button class="basket" type="button" data-open="cart" aria-label="{e(C.t(lang,'cart_title'))}">
        <span aria-hidden="true">▤</span><span class="txt">{e(C.t(lang,'inquiry'))}</span>
        <span class="cnt" id="cnt">0</span></button>
      <button class="burger" type="button" data-open="mega" aria-label="{e(C.t(lang,'menu_aria'))}"
              aria-expanded="false"><span></span><span></span><span></span></button>
    </div>
  </div>
</header>
<div class="scrim" id="scrim" data-close="all"></div>
{mega(lang)}
{cart_drawer(lang)}"""


def cart_drawer(lang):
    return f"""<aside class="cart" id="cart" aria-label="{e(C.t(lang,'cart_title'))}" aria-hidden="true">
  <div class="top"><p class="drawer-title">{e(C.t(lang,'cart_title'))}</p>
    <button class="x" type="button" data-close="cart" aria-label="✕">✕</button></div>
  <div class="items" id="cartItems"></div>
  <form class="form" id="cartForm" hidden novalidate>
    <label for="cName">{e(C.t(lang,'f_name'))}</label>
    <input id="cName" name="name" type="text" required autocomplete="organization"
           placeholder="Max Muster · Muster AG">
    <label for="cMail">{e(C.t(lang,'f_mail'))}</label>
    <input id="cMail" name="email" type="email" required autocomplete="email" placeholder="max@firma.ch">
    <label for="cMsg">{e(C.t(lang,'f_msg'))}</label>
    <textarea id="cMsg" name="message" rows="2" placeholder="…"></textarea>
    <input type="checkbox" name="botcheck" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
    <button class="send" type="submit">{e(C.t(lang,'f_send'))}</button>
    <p class="fstatus" role="status" aria-live="polite"></p>
  </form>
</aside>"""


def footer(lang):
    """Fusszeile.

    Hier stand einmal eine vierte Spalte mit Inhabername, Werkstattadresse,
    Telefon und E-Mail - auf jeder der 333 Seiten. Diese Angaben gehoeren ins
    Impressum, nicht unter jede Produktseite. Rechtlich reicht das: UWG Art. 3
    Abs. 1 lit. s verlangt klare und vollstaendige Angaben und einen leicht
    erreichbaren Weg dorthin, nicht deren Wiederholung auf jeder Seite. Das
    Impressum ist von hier aus zweimal verlinkt.

    Verloren geht dadurch nichts: die Telefonnummer steht in der obersten
    Leiste jeder Seite, die vollstaendige Anschrift im JSON-LD jeder Seite
    (LocalBusiness), und sichtbar auf Kontakt- und Impressumseite.
    """
    prod = "".join(f'<li><a href="{e(C.u_cat(lang, c["id"]))}">{e(C.catT(lang, c))}</a></li>'
                   for c in C.CATS)
    return f"""<footer>
  <div class="wrap">
    <div class="fcols">
      <div class="brand"><div class="name">VES<i>-</i>TECH</div>
        <p>{e(C.t(lang,'foot_brand'))}</p></div>
      <div><h2 class="fh">{e(C.t(lang,'foot_products'))}</h2><ul>{prod}
        <li><a href="{e(C.u_products(lang))}">{e(C.t(lang,'nav_all_products'))}</a></li></ul></div>
      <div><h2 class="fh"><a href="{e(C.u_service(lang))}">{e(C.t(lang,'foot_service'))}</a></h2><ul>
        <li><a href="{e(C.u_service(lang,'repair'))}">{e(C.t(lang,'foot_diag'))}</a></li>
        <li><a href="{e(C.u_service(lang,'calib'))}">{e(C.t(lang,'foot_calib'))}</a></li>
        <li><a href="{e(C.u_service(lang,'auto'))}">{e(C.t(lang,'foot_auto'))}</a></li>
        <li><a href="{e(C.u_page(lang,'processes'))}">{e(C.t(lang,'n_process'))}</a></li>
        <li><a href="{e(C.u_page(lang,'downloads'))}">{e(C.t(lang,'n_downloads'))}</a></li>
        <li><a href="{e(C.u_page(lang,'faq'))}">{e(C.t(lang,'nav_faq'))}</a></li>
        <li><a href="{e(C.u_page(lang,'about'))}">{e(C.t(lang,'nav_about'))}</a></li>
        <li><a href="{e(C.u_page(lang,'contact'))}">{e(C.t(lang,'foot_contact'))}</a></li>
        <li><a href="{e(C.u_page(lang,'imprint'))}">{e(C.t(lang,'nav_impressum'))}</a></li>
      </ul></div>
    </div>
    <div class="fbar">
      <span>© 2026 {e(C.t(lang,'site_name'))} · {e(C.t(lang,'footer_credit'))} ·
        <a href="{e(C.u_page(lang,'imprint'))}">{e(C.t(lang,'nav_impressum'))}</a> ·
        <a href="{e(C.u_page(lang,'terms'))}">{e(C.t(lang,'nav_agb'))}</a> ·
        <a href="{e(C.u_page(lang,'privacy'))}">{e(C.t(lang,'nav_datenschutz'))}</a></span>
    </div>
  </div>
</footer>
<div class="toast" id="toast" role="status" aria-live="polite"></div>"""


JS_KEYS = ["poa", "inquire", "added", "already", "cart_empty", "cart_title", "opened_mail",
           "no_hits", "items", "c_search", "dl_soon", "to_inquiry", "f_send",
           "search_results_for", "search_n_results", "search_one_result", "search_no_results",
           "search_no_results_help", "search_did_you_mean", "search_all_results",
           "search_group_products", "search_group_cats", "search_group_procs",
           "search_group_dl", "search_min_chars", "form_sending", "form_success",
           "form_error", "form_required", "form_invalid_mail", "search_popular",
           "lupe_open", "lupe_close", "lupe_in", "lupe_out",
             "mail_h", "mail_p", "mail_copy", "mail_open", "mail_copied",
             "mail_copy_manual",
             # Bausteine der Anfrage-Mail. Ohne sie schrieb app.js den Text
             # in jeder Sprache auf Deutsch: ein Kunde aus der Romandie
             # klickte "Envoyer la demande" und bekam einen Entwurf mit
             # "Anfrage VES-TECH" und "Gewuenschte Geraete".
             "mail_f_name", "mail_f_mail", "mail_f_tel", "mail_f_msg",
             "mail_f_sent", "mail_f_dev", "mail_s_cart", "mail_s_item", "mail_s_item1",
             "mail_s_kont"]


def boot_json(lang):
    """Der Inhalt des Startskripts - ohne die <script>-Tags.

    Getrennt von boot_script, weil csp() genau diese Zeichenkette hasht. Beide
    muessen dasselbe liefern, sonst passt der Hash nicht und der Browser
    verweigert das Skript: keine Suche, keine Anfrageliste, keine Formulare.
    """
    cfg = {
        "lang": lang,
        "hreflang": C.EX[lang]["hreflang"],
        "searchIndex": f"/data/search-{lang}.json",
        "searchUrl": C.u_page(lang, "search"),
        "productsUrl": C.u_products(lang),
        "web3formsKey": C.web3forms_key(),
        "mailto": C.COMPANY["email"],
        "i18n": {k: C.t(lang, k) for k in JS_KEYS},
    }
    return ("window.VT=" + json.dumps(cfg, ensure_ascii=False, separators=(",", ":"))
            + ";")


def boot_script(lang):
    return "<script>" + boot_json(lang) + "</script>"


def _complete_graph(lang, blocks):
    """Organization und WebSite gehören in jeden Graph.

    Die Seiten verweisen mit isPartOf/publisher/seller per @id auf diese beiden
    Knoten. Fehlen sie, zeigt der Verweis ins Leere und die Angaben lassen sich
    weder Google noch einer Antwortmaschine zuordnen.
    """
    have = set()
    for b in blocks:
        ty = b.get("@type")
        for x in (ty if isinstance(ty, list) else [ty]):
            have.add(x)
    out = list(blocks)
    if "Organization" not in have:
        out.insert(0, ld_org(lang))
    if "WebSite" not in have:
        pos = 1 if out and "Organization" in str(out[0].get("@type")) else 0
        out.insert(pos, ld_website(lang))
    return out


def document(lang, *, title, desc, url, alts, jsonld_blocks, body,
             og_image=None, og_type="website", robots="index,follow,max-image-preview:large",
             extra_head="", body_class=""):
    jsonld_blocks = _complete_graph(lang, jsonld_blocks)
    return f"""<!DOCTYPE html>
<html lang="{C.EX[lang]['hreflang']}">
<head>
{head(lang, title=title, desc=desc, url=url, alts=alts, jsonld_blocks=jsonld_blocks,
      og_image=og_image, og_type=og_type, robots=robots, extra_head=extra_head)}
</head>
<body{f' class="{body_class}"' if body_class else ''}>
{header(lang, alts)}
<main id="main">
{body}
</main>
{footer(lang)}
{boot_script(lang)}
<script src="{JS_URL}" defer></script>
</body>
</html>
"""


# --------------------------------------------------------------------------
# Inhalts-Bausteine
# --------------------------------------------------------------------------

def crumbs(lang, items):
    """items: [(name, url|None)] – letztes Element ohne URL."""
    parts = []
    for i, (n, u) in enumerate(items):
        if i:
            parts.append('<span class="sep" aria-hidden="true">›</span>')
        parts.append(f'<a href="{e(u)}">{e(n)}</a>' if u else f"<span>{e(n)}</span>")
    return (f'<nav class="crumbs" aria-label="{e(C.t(lang,"breadcrumb_aria"))}">'
            + "".join(parts) + "</nav>")


def thumb(p):
    """Kleines WebP für Anfrageliste und Suchvorschläge."""
    m = MANIFEST.get(C.full_img(p["img"]))
    return (f"/assets/img/{img_folder(m)}/{m['key']}-{img_step(m, 400)}.webp" if m
            else C.REMOTE_IMG + C.full_img(p["img"]))


def pcard(lang, p):
    specs = "".join(f"<span>{e(C.trV(lang, v))}</span>"
                    for v in list(p["specs"].values())[:3])
    url = C.u_prod(lang, p)
    return f"""<article class="pcard">
  <a class="pcard-link" href="{e(url)}">
    <div class="imgbox">
      {img_tag(p['img'], "(max-width:700px) 46vw, (max-width:1000px) 30vw, 280px",
               alt=f"{C.BRAND} {C.pName(lang, p)}: {C.pDesc(lang, p)}")}</div>
    <div class="body"><h3>{e(C.pName(lang, p))}</h3><p>{e(C.pDesc(lang, p))}</p>
      <div class="spec">{specs}</div></div>
  </a>
  <div class="foot"><span class="poa">{e(C.t(lang,'poa'))}</span>
    <button class="add" type="button" data-add="{e(p['id'])}" data-name="{e(C.pName(lang, p))}"
            data-url="{e(url)}" data-img="{e(thumb(p))}">{e(C.t(lang,'inquire'))}</button></div>
</article>"""


def pgrid(lang, products):
    return f'<div class="pgrid">{"".join(pcard(lang, p) for p in products)}</div>'


def cbar(lang, *, crumb_items, h1, desc, chips=""):
    return f"""<div class="cbar"><div class="wrap">
  {crumbs(lang, crumb_items)}
  <h1>{e(h1)}</h1>
  <p class="desc">{e(desc)}</p>
  {chips}
</div></div>"""


def usp_row(lang):
    items = [("usp_1_h", "usp_1_p"), ("usp_2_h", "usp_2_p"), ("usp_3_h", "usp_3_p")]
    cards = "".join(
        f'<div class="usp"><h2>{e(C.t(lang, h))}</h2><p>{e(C.t(lang, p))}</p></div>'
        for h, p in items
    )
    return f'<section class="usps"><div class="wrap"><div class="usprow">{cards}</div></div></section>'


def ref_block(lang, geraet=None):
    """Kundenstimmen. Gibt es keine mit Freigabe, kommt gar nichts - ein
    leerer Kasten mit der Ueberschrift "Referenzen" waere schlimmer als
    nichts, weil er die Luecke betont."""
    refs = C.referenzen(lang, geraet)
    if not refs:
        return ""
    karten = ""
    for x in refs:
        wer = ", ".join(p for p in (x["person"], x["rolle"]) if p)
        karten += (
            f'<figure class="refcard">'
            f'<blockquote><p>{e(x["text"])}</p></blockquote>'
            f'<figcaption><b>{e(x["firma"])}</b>'
            + (f'<span>{e(x["ort"])}</span>' if x["ort"] else "")
            + (f'<span>{e(wer)}</span>' if wer else "")
            + "</figcaption></figure>")
    return (f'<section class="refs"><div class="wrap">'
            f'<h2 class="refs-h">{e(C.t(lang, "ref_h"))}</h2>'
            f'<div class="refrow">{karten}</div></div></section>')


def ld_reviews(lang):
    """Review-Knoten am Organization - nur fuer Stimmen mit Freigabe.

    Ohne echte Eintraege wird gar nichts ausgegeben. Eine erfundene
    Review-Auszeichnung waere Spam im Sinne der Google-Richtlinien und
    zugleich eine irrefuehrende Angabe nach UWG Art. 3 Abs. 1 lit. b.
    """
    refs = C.referenzen(lang)
    if not refs:
        return []
    return [{
        "@type": "Review",
        "itemReviewed": {"@id": f"{C.SITE}/#organization"},
        "author": {"@type": "Organization", "name": x["firma"]},
        "reviewBody": x["text"],
        **({"datePublished": x["datum"]} if x["datum"] else {}),
    } for x in refs]


def faq_block(lang, items, h=None):
    # Ohne Abschnittsüberschrift folgen die Fragen direkt auf das h1 und sind
    # damit h2; steht eine h2 davor (Startseite), werden sie zu h3.
    lv = "h3" if h else "h2"
    rows = "".join(
        f'<details class="faq"{" open" if i == 0 else ""}>'
        f'<summary><{lv}>{e(q["q"])}</{lv}></summary>'
        f'<div class="faq-a"><p>{e(q["a"])}</p></div></details>'
        for i, q in enumerate(items)
    )
    head_html = f'<h2 class="sec-h">{e(h)}</h2>' if h else ""
    return f'<div class="faqlist">{head_html}{rows}</div>'
