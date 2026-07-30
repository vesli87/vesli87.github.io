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


# Hero: dasselbe Bild in drei Breiten. Das Original bleibt als hero.jpg liegen
# und dient dem onerror-Fallback für Browser ohne WebP.
HERO_SRCSET = ("/assets/img/hero-640.webp 640w, /assets/img/hero-1000.webp 1000w, "
               "/assets/img/hero-1536.webp 1536w")
HERO_SRC = "/assets/img/hero-1536.webp"
HERO_W, HERO_H = 1536, 1024

# Das Hero ist das LCP-Element der Startseite. Ohne preload findet der Browser
# es erst, nachdem er CSS geparst hat – mit preload startet der Download sofort.
HERO_PRELOAD = (f'<link rel="preload" as="image" href="{HERO_SRC}" '
                f'imagesrcset="{HERO_SRCSET}" imagesizes="100vw" fetchpriority="high">')

CSS_URL = _ver("/assets/css/site.css")
JS_URL = _ver("/assets/js/app.js")


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


def img_tag(path, sizes, cls="", alt="", eager=False, width=None):
    """<img> mit WebP-Srcset, Massen gegen CLS und Remote-Fallback."""
    m = MANIFEST.get(C.full_img(path))
    remote = C.REMOTE_IMG + C.full_img(path)
    if not m:
        return (f'<img class="{cls}" src="{e(remote)}" alt="{e(alt)}" '
                f'referrerpolicy="no-referrer" loading="lazy" decoding="async">')
    k = m["key"]
    w = width or 400
    h = int(round(w * m["ratio"]))
    small = f"/assets/img/p/{k}-400.webp"
    large = f"/assets/img/p/{k}-1000.webp"
    loading = "" if eager else 'loading="lazy" '
    # Fällt ein Browser über WebP, lädt onerror das Original von mahe-online.de.
    onerror = ("this.onerror=null;this.removeAttribute(&quot;srcset&quot;);"
               "this.src=&quot;" + e(remote) + "&quot;")
    return (
        f'<img class="{cls}" src="{small}" '
        f'srcset="{small} 400w, {large} 1000w" sizes="{e(sizes)}" '
        f'width="{w}" height="{h}" alt="{e(alt)}" '
        f'{loading}decoding="async" referrerpolicy="no-referrer" '
        f'onerror="{onerror}">'
    )


def img_abs(path, size=1000):
    """Absolute URL des lokalen Bildes – für og:image und JSON-LD."""
    m = MANIFEST.get(C.full_img(path))
    if not m:
        return C.REMOTE_IMG + C.full_img(path)
    return f"{C.SITE}/assets/img/p/{m['key']}-{size}.webp"


# --------------------------------------------------------------------------
# JSON-LD-Bausteine
# --------------------------------------------------------------------------

def ld_org():
    co = C.COMPANY
    return {
        "@type": ["Organization", "LocalBusiness", "Store"],
        "@id": f"{C.SITE}/#organization",
        "name": co["name"],
        "legalName": co["legal_name"],
        "url": C.SITE + "/",
        "logo": {"@type": "ImageObject", "url": f"{C.SITE}/assets/icons/logo.png",
                 "width": 512, "height": 512},
        "image": f"{C.SITE}/assets/img/hero.jpg",
        "telephone": co["phone"],
        "email": co["email"],
        "address": {
            "@type": "PostalAddress",
            "streetAddress": co["street"],
            "postalCode": co["zip"],
            "addressLocality": co["city"],
            "addressRegion": co["region"],
            "addressCountry": co["country"],
        },
        "geo": {"@type": "GeoCoordinates", "latitude": co["lat"], "longitude": co["lon"]},
        "openingHoursSpecification": [
            {"@type": "OpeningHoursSpecification", "dayOfWeek": h["days"],
             "opens": h["opens"], "closes": h["closes"]} for h in co["hours_schema"]
        ],
        "areaServed": [{"@type": "Country", "name": "Schweiz"},
                       {"@type": "Country", "name": "Liechtenstein"}],
        "knowsLanguage": ["de-CH", "fr-CH", "it-CH"],
        "currenciesAccepted": "CHF",
        "brand": {"@type": "Brand", "name": C.BRAND, "url": C.BRAND_URL},
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
            "availableLanguage": ["German", "French", "Italian"],
            "areaServed": ["CH", "LI"],
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
             for k, v in p["specs"].items()]
    hl = C.highlightsOf(lang, p)
    d = {
        "@type": "Product",
        "@id": url + "#product",
        "name": f"{C.BRAND} {p['name']}",
        "alternateName": p["name"],
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
        # Preis auf Anfrage: bewusst KEIN price-Feld. Ein erfundener Preis wäre
        # falsch; Google akzeptiert das Offer ohne Preis (Warnung statt Fehler).
        "offers": {
            "@type": "Offer",
            "url": url,
            "availability": "https://schema.org/InStock",
            "priceCurrency": "CHF",
            "availableDeliveryMethod": "https://schema.org/OnSitePickup",
            "areaServed": ["CH", "LI"],
            "seller": {"@id": f"{C.SITE}/#organization"},
            "description": C.t(lang, "poa"),
        },
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

# Diese beiden Schnitte stehen auf jeder Seite über dem Falz (Anton in der H1,
# Inter im Fliesstext) – preload startet ihren Download vor dem CSS-Parsing.
# crossorigin ist bei Schriften auch für dieselbe Herkunft Pflicht.
FONT_PRELOAD = (
    '<link rel="preload" as="font" type="font/woff2" crossorigin '
    'href="/assets/fonts/inter-400-700-latin.woff2">\n'
    '<link rel="preload" as="font" type="font/woff2" crossorigin '
    'href="/assets/fonts/anton-400-latin.woff2">'
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
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="{e(robots)}">
<link rel="canonical" href="{e(C.abs_url(url))}">
{alt_links}
<meta name="author" content="{e(C.COMPANY['name'])}">
<meta name="geo.region" content="CH-{C.COMPANY['region']}">
<meta name="geo.placename" content="{e(C.COMPANY['city'])}">
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
    return f"""<a class="skip" href="#main">{e(C.t(lang,'skip_link'))}</a>
<div class="util"><div class="wrap">
  <div class="l"><a href="tel:{co['phone_href']}">{e(co['phone'])}</a>
    <span>{e(co['city'])} · {co['region']}</span><span>{e(C.t(lang,'hours'))}</span></div>
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
  <div class="top"><h2>{e(C.t(lang,'cart_title'))}</h2>
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
    co = C.COMPANY
    prod = "".join(f'<li><a href="{e(C.u_cat(lang, c["id"]))}">{e(C.catT(lang, c))}</a></li>'
                   for c in C.CATS)
    return f"""<footer>
  <div class="wrap">
    <div class="fcols">
      <div class="brand"><div class="name">VES<i>-</i>TECH</div>
        <p>{e(C.t(lang,'foot_brand'))}</p></div>
      <div><h2 class="fh">{e(C.t(lang,'foot_products'))}</h2><ul>{prod}
        <li><a href="{e(C.u_products(lang))}">{e(C.t(lang,'nav_all_products'))}</a></li></ul></div>
      <div><h2 class="fh">{e(C.t(lang,'foot_service'))}</h2><ul>
        <li><a href="{e(C.u_page(lang,'contact'))}">{e(C.t(lang,'foot_diag'))}</a></li>
        <li><a href="{e(C.u_page(lang,'contact'))}">{e(C.t(lang,'foot_calib'))}</a></li>
        <li><a href="{e(C.u_page(lang,'contact'))}">{e(C.t(lang,'foot_auto'))}</a></li>
        <li><a href="{e(C.u_page(lang,'processes'))}">{e(C.t(lang,'n_process'))}</a></li>
        <li><a href="{e(C.u_page(lang,'downloads'))}">{e(C.t(lang,'n_downloads'))}</a></li>
        <li><a href="{e(C.u_page(lang,'faq'))}">{e(C.t(lang,'nav_faq'))}</a></li>
      </ul></div>
      <div><h2 class="fh">{e(C.t(lang,'site_name'))}</h2><ul>
        <li><a href="{e(C.u_page(lang,'contact'))}">{e(co['street'])}, {co['zip']} {e(co['city'])}</a></li>
        <li><a href="tel:{co['phone_href']}">{e(co['phone'])}</a></li>
        <li><a href="mailto:{co['email']}">{co['email']}</a></li>
        <li><a href="{e(C.u_page(lang,'contact'))}">{e(C.t(lang,'foot_contact'))}</a></li>
      </ul></div>
    </div>
    <div class="fbar">
      <span>© 2026 {e(C.t(lang,'site_name'))} · Produktdaten &amp; Bilder: MAHE GmbH ·
        <a href="{e(C.u_page(lang,'imprint'))}">{e(C.t(lang,'nav_impressum'))}</a> ·
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
           "form_error", "form_required", "form_invalid_mail", "search_popular"]


def boot_script(lang):
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
    return ('<script>window.VT=' + json.dumps(cfg, ensure_ascii=False, separators=(",", ":"))
            + ";</script>")


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
        out.insert(0, ld_org())
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
    return f"/assets/img/p/{m['key']}-400.webp" if m else C.REMOTE_IMG + C.full_img(p["img"])


def pcard(lang, p):
    specs = "".join(f"<span>{e(C.trV(lang, v))}</span>"
                    for v in list(p["specs"].values())[:3])
    url = C.u_prod(lang, p)
    return f"""<article class="pcard">
  <a class="pcard-link" href="{e(url)}">
    <div class="imgbox"><span class="vtag">{e(p['vt'])}</span>
      {img_tag(p['img'], "(max-width:700px) 46vw, (max-width:1000px) 30vw, 280px",
               alt=f"{C.BRAND} {p['name']} – {C.pDesc(lang, p)}")}</div>
    <div class="body"><h3>{e(p['name'])}</h3><p>{e(C.pDesc(lang, p))}</p>
      <div class="spec">{specs}</div></div>
  </a>
  <div class="foot"><span class="poa">{e(C.t(lang,'poa'))}</span>
    <button class="add" type="button" data-add="{e(p['id'])}" data-name="{e(p['name'])}"
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
        f'<div class="usp"><h3>{e(C.t(lang, h))}</h3><p>{e(C.t(lang, p))}</p></div>'
        for h, p in items
    )
    return f'<section class="usps"><div class="wrap"><div class="usprow">{cards}</div></div></section>'


def faq_block(lang, items, h=None):
    rows = "".join(
        f'<details class="faq"{" open" if i == 0 else ""}>'
        f'<summary><h3>{e(q["q"])}</h3></summary>'
        f'<div class="faq-a"><p>{e(q["a"])}</p></div></details>'
        for i, q in enumerate(items)
    )
    head_html = f'<h2 class="sec-h">{e(h)}</h2>' if h else ""
    return f'<div class="faqlist">{head_html}{rows}</div>'
