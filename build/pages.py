#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VES-TECH Swiss — Seitenvorlagen. Jede Funktion liefert (pfad, html)."""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import core as C          # noqa: E402
import render as R        # noqa: E402
from render import e      # noqa: E402

PANEL_DRAWN = json.loads((C.DATA / "PANEL_DRAWN.json").read_text("utf-8"))

# Achtung: DLS[].k ist NICHT eindeutig – Produktkatalog und EN-1090-Zertifikat
# tragen beide "PDF". Deshalb wird hier über den Titel identifiziert.
DL_CATALOG = next(d for d in C.DLS if "Produktkatalog" in d["t"]["de"])
DL_EN1090 = next(d for d in C.DLS if "1090" in d["t"]["de"])
DL_SDS = {d["k"]: d for d in C.DLS if d["k"] != "PDF"}     # R1, RP1, P1, M1, N1


# --------------------------------------------------------------------------
# Produktbezogene Blöcke
# --------------------------------------------------------------------------

def dls_for(p):
    """Für das Produkt relevante PDFs – Sicherheitsdatenblätter zuerst."""
    out = []
    if p["sub"] == "Elektrolyte" and p["id"].upper() in DL_SDS:
        out.append(DL_SDS[p["id"].upper()])
    if p["cat"] == "reinigung" and p["sub"] == "Cleaner":
        out += [DL_SDS[k] for k in ("R1", "RP1", "P1", "M1", "N1") if k in DL_SDS]
    if p["cat"] == "schweissgeraete":
        out.append(DL_EN1090)
    out.append(DL_CATALOG)
    seen, res = set(), []
    for d in out:
        if d["u"] not in seen:
            seen.add(d["u"])
            res.append(d)
    return res


def procs_block(lang, p):
    badges = ""
    for k in C.deriveFeat(p):
        f = C.FEAT.get(k)
        if not f:
            continue
        badges += (f'<div class="procbadge{" tile" if f.get("tile") else ""}">'
                   f'<div class="ic" aria-hidden="true">{f["svg"]}</div>'
                   f'<div class="lb">{e(C.featLabel(lang, k))}</div></div>')
    mats = C.matOf(p)
    chips = ""
    if mats:
        chips = ('<div class="matchips">' + "".join(
            f'<span class="matchip"><b>{m}</b>{e(C.matLabel(lang, m))}</span>' for m in mats
        ) + "</div>")
    return f'<div class="procs">{badges}{chips}</div>'


def front_html(lang, p):
    """Fronteingabe- bzw. Besonderheiten-Tab, vorgerendert."""
    panels = C.fpAssign(p)
    hl = C.highlightsOf(lang, p)
    out = []
    if hl:
        out.append('<div class="fp-highlights"><h3 class="besond">'
                   + e(C.t(lang, "highlights")) + '</h3><ul class="besond-list">'
                   + "".join(f"<li>{e(x)}</li>" for x in hl) + "</ul></div>")
    if panels:
        out.append(f'<h3 class="fp-section">{e(C.t(lang,"front_h"))}</h3>')
        for pk in panels:
            fp = C.FP[pk]
            # Unter dem Panelfoto steht nur, was MAHE zu genau diesem Panel
            # schreibt. Wo der Hersteller nichts veroeffentlicht, steht auch bei
            # uns nichts – frueher lief das auf einen selbst verfassten Text
            # hinaus, der bei allen fuenf Theta-Modellen derselbe war.
            src = C.PANEL_HL_DEVICE.get(pk)
            ph = (src.get(lang) or src["de"]) if src else []
            if fp.get("img"):
                media = R.img_tag(fp["img"], "(max-width:760px) 90vw, 340px",
                                  cls="fp-photo", alt=f"{C.BRAND} {fp['n']}", width=340)
            else:
                media = PANEL_DRAWN["big" if fp.get("big") else "small"]
            bes = ""
            if ph:
                bes = (f'<div class="fp-right">'
                       f'<h5 class="besond">{e(C.t(lang,"front_bes"))}</h5>'
                       f'<ul class="besond-list fp-list">'
                       + "".join(f"<li>{e(x)}</li>" for x in ph)
                       + "</ul></div>")
            out.append(
                f'<div class="fp{"" if ph else " fp-solo"}">'
                f'<h4 class="fp-title">{e(fp["n"])}</h4>'
                f'<div class="fp-body"><div class="fp-panel">{media}</div>'
                f"{bes}</div></div>"
            )
    elif not hl:
        out.append('<div class="featlist">' + "".join(
            f'<div class="fitem">{C.FEAT[k]["svg"]}<span>{e(C.featLabel(lang, k))}</span></div>'
            for k in C.deriveFeat(p) if k in C.FEAT
        ) + "</div>")
    return "".join(out)


def spec_html(lang, p):
    """Technische Daten wie bei MAHE: eine Tabelle, eine Spalte je Variante.

    Darunter das, was in der MAHE-Tabelle nicht vorkommt (Verfahren, Kühlung,
    Antrieb …). Geräte ohne MAHE-Tabelle – Zubehör, Elektrolyte, Kabel –
    behalten nur diese Liste.
    """
    tabs = C.specTables(lang, p)
    out = [f'<h3 class="spec-h">{e(C.t(lang,"techdata"))}</h3>']

    for t in tabs:
        cap = f'<caption>{e(t["title"])}</caption>' if len(tabs) > 1 and t["title"] else ""
        head = "".join(f'<th scope="col">{e(c)}</th>' for c in t["cols"])
        body = ""
        for r in t["rows"]:
            cells = "".join(f"<td>{e(v)}</td>" for v in r[1:])
            body += f'<tr><th scope="row">{e(r[0])}</th>{cells}</tr>'
        out.append(
            f'<div class="spectab-scroll" tabindex="0" role="region" '
            f'aria-label="{e(C.t(lang,"techdata"))} {e(C.pName(lang, p))}">'
            f'<table class="spectab">{cap}'
            f'<thead><tr><th scope="col">{e(C.t(lang,"spec_model"))}</th>{head}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>"
        )
        if t["note"]:
            out.append(f'<p class="spectab-note"><span aria-hidden="true">*</span> {e(t["note"])}</p>')

    rest = C.specRest(p)
    if rest:
        rows = "".join(
            f'<div class="r"><span class="k">{e(C.trK(lang, k))}</span>'
            f'<span class="v">{e(C.trV(lang, v))}</span></div>'
            for k, v in rest.items()
        )
        title = f'<h4>{e(C.t(lang,"spec_more"))}</h4>' if tabs else ""
        out.append(f'<div class="spectable">{title}{rows}</div>')
    return "".join(out)


def acc_html(lang, p):
    acc = C.relatedAcc(p)
    if not acc:
        return f'<p class="noacc">{e(C.t(lang,"no_acc"))}</p>'
    cards = ""
    for pid in acc:
        a = C.BY_ID[pid]
        alt = "%s %s" % (C.BRAND, C.pName(lang, a))
        im = R.img_tag(a["img"], "(max-width:760px) 40vw, 180px", alt=alt)
        cards += (
            f'<a class="acccard" href="{e(C.u_prod(lang, a))}">'
            f'<div class="im">{im}</div>'
            f'<div class="bd"><div class="vt">{e(a["vt"])}</div><h3>{e(C.pName(lang, a))}</h3>'
            f'<p>{e(C.pDesc(lang, a))}</p></div></a>'
        )
    return f'<div class="accgrid">{cards}</div>'


def dl_html(lang, p):
    items = ""
    for d in dls_for(p):
        items += (
            f'<a class="dlitem" href="{e(d["u"])}" target="_blank" rel="noopener nofollow">'
            f'<div class="ico">{e(d["k"])}</div>'
            f'<div class="nm">{e(d["t"].get(lang) or d["t"]["de"])}'
            f'<span>{e(d["s"].get(lang) or d["s"]["de"])}</span></div>'
            f'<span class="arw" aria-hidden="true">↓</span></a>'
        )
    return f'<div class="dlrow">{items}</div>'


def clip(s, n):
    """Kürzt eine meta description an der Wortgrenze – Google schneidet ~160 Zeichen ab."""
    s = " ".join(s.split())
    if len(s) <= n:
        return s
    cut = s[:n]
    return cut[:cut.rfind(" ")].rstrip(" ,.;:–-") + " …"


# --------------------------------------------------------------------------
# Seiten
# --------------------------------------------------------------------------

def page_home(lang):
    url, alts = C.u_home(lang), C.alternates("home")
    cards = ""
    for i, c in enumerate(C.CATS, 1):
        n = len(C.products_of(c["id"]))
        cards += (
            f'<a class="cat" href="{e(C.u_cat(lang, c["id"]))}">'
            f'<div class="idx">{i:02d} · {n} {e(C.t(lang,"devices"))}</div>'
            f'<div class="pk" aria-hidden="true">{C.PK[c["pk"]]}</div>'
            f'<h3>{e(C.catT(lang, c))}</h3><p>{e(C.catD(lang, c))}</p>'
            f'<div class="go">{e(C.t(lang,"card_open"))}</div></a>'
        )
    faq6 = C.EX[lang]["faq"][:6]
    body = f"""
<section class="hero">
  <img class="hero-photo" src="{R.HERO_SRC}" srcset="{R.HERO_SRCSET}" sizes="100vw"
       width="{R.HERO_W}" height="{R.HERO_H}" fetchpriority="high" decoding="async"
       alt="{e(C.BRAND)} HyperMIG SX – Schweissanlagen bei {e(C.t(lang,'site_name'))}"
       onerror="this.onerror=null;this.removeAttribute('srcset');this.src='/assets/img/hero.jpg'">
</section>
<div class="hero-cta"><div class="wrap"><div class="cta-row">
  <a class="btn pri" href="{e(C.u_page(lang,'contact'))}">{e(C.t(lang,'hero_cta1'))}</a>
  <a class="btn ghost light" href="{e(C.u_products(lang))}">{e(C.t(lang,'hero_cta2'))}</a>
</div></div></div>

<section class="intro"><div class="wrap">
  <h1>{e(C.t(lang,'home_h1'))}</h1>
  <p class="lead">{e(C.t(lang,'hero_lead'))}</p>
</div></section>

{R.usp_row(lang)}

<section class="programm"><div class="wrap">
  <p class="p-eyebrow">{e(C.t(lang,'prog_eyebrow'))}</p>
  <h2>{e(C.t(lang,'prog_h2'))}</h2>
  <p class="sub">{e(C.t(lang,'prog_sub'))}</p>
  <div class="cards">{cards}</div>
</div></section>

<section class="trust"><div class="wrap"><div class="row">
  <div class="lead"><h2>{e(C.t(lang,'trust_h3'))}</h2><p>{e(C.t(lang,'trust_p'))}</p></div>
  <a class="dl" href="{e(C.u_page(lang,'downloads'))}"><div class="k">{e(C.t(lang,'dl'))}</div>
    <h3>{e(C.t(lang,'dl_cat'))}</h3><p>{e(C.t(lang,'dl_cat_p'))}</p></a>
  <a class="dl" href="{e(C.u_page(lang,'contact'))}"><div class="k">{e(C.t(lang,'svc'))}</div>
    <h3>{e(C.t(lang,'dl_en'))}</h3><p>{e(C.t(lang,'dl_en_p'))}</p></a>
</div></div></section>

<section class="faqsec"><div class="wrap">
  {R.faq_block(lang, faq6, C.t(lang,'faq_h1'))}
  <p class="more"><a href="{e(C.u_page(lang,'faq'))}">{e(C.t(lang,'nav_faq'))} →</a></p>
</div></section>
"""
    ld = [R.ld_org(), R.ld_website(lang),
          R.ld_webpage(lang, url, C.t(lang, "home_title"), C.t(lang, "home_desc"),
                       {"@type": ["WebPage", "CollectionPage"]}),
          R.ld_faq_subset(lang, faq6, url)]
    return url, R.document(
        lang, title=C.t(lang, "home_title"), desc=C.t(lang, "home_desc"),
        url=url, alts=alts, jsonld_blocks=ld, body=body,
        extra_head=R.HERO_PRELOAD)


def page_products(lang):
    url, alts = C.u_products(lang), C.alternates("products")
    n = len(C.P)
    title = C.t(lang, "all_title")
    desc = clip(C.t(lang, "all_desc", n=n), 165)
    chips = '<div class="chips">' + "".join(
        f'<a class="chip" href="{e(C.u_cat(lang, c["id"]))}">{e(C.catT(lang, c))}</a>'
        for c in C.CATS) + "</div>"
    body = (
        R.cbar(lang, crumb_items=[(C.t(lang, "nav_home"), C.u_home(lang)),
                                  (C.t(lang, "nav_products"), None)],
               h1=C.t(lang, "all_h1"), desc=C.t(lang, "all_lead"), chips=chips)
        + '<div class="catalog"><div class="wrap">'
        + f'<div class="cathead"><h2>{e(C.t(lang,"sec_all"))}</h2>'
          f'<span class="count">{n} {e(C.t(lang,"items"))} · {e(C.t(lang,"poa"))}</span></div>'
        + R.pgrid(lang, C.P) + "</div></div>"
    )
    ld = [R.ld_org(),
          R.ld_webpage(lang, url, title, desc, {"@type": "CollectionPage"}),
          R.ld_breadcrumb([(C.t(lang, "nav_home"), C.u_home(lang)),
                           (C.t(lang, "nav_products"), url)]),
          R.ld_itemlist(lang, C.P, C.t(lang, "all_h1"))]
    return url, R.document(lang, title=title, desc=desc, url=url, alts=alts,
                           jsonld_blocks=ld, body=body)


def page_cat(lang, c, sub=None):
    cid = c["id"]
    if sub:
        url = C.u_sub(lang, cid, sub)
        alts = C.alternates("sub", cat_id=cid, sub=sub)
        items = C.products_of(cid, sub)
        h1 = f"{C.subT(lang, sub)} · {C.BRAND}"
        title = C.t(lang, "sub_title_tpl", sub=C.subT(lang, sub), cat=C.catT(lang, c))
        desc = clip(C.t(lang, "sub_desc_tpl", sub=C.subT(lang, sub), n=len(items)), 165)
        lead = C.catD(lang, c)
        crumb = [(C.t(lang, "nav_home"), C.u_home(lang)),
                 (C.t(lang, "nav_products"), C.u_products(lang)),
                 (C.catT(lang, c), C.u_cat(lang, cid)),
                 (C.subT(lang, sub), None)]
    else:
        url = C.u_cat(lang, cid)
        alts = C.alternates("cat", cat_id=cid)
        items = C.products_of(cid)
        h1 = C.catT(lang, c)
        subs_txt = ", ".join(C.subT(lang, s) for s in c["subs"])
        title = C.t(lang, "cat_title_tpl", cat=C.catT(lang, c),
                    sub_hint=C.subT(lang, c["subs"][0]))
        desc = clip(C.t(lang, "cat_desc_tpl", cat=C.catT(lang, c), n=len(items), subs=subs_txt), 165)
        lead = C.catD(lang, c)
        crumb = [(C.t(lang, "nav_home"), C.u_home(lang)),
                 (C.t(lang, "nav_products"), C.u_products(lang)),
                 (C.catT(lang, c), None)]

    chip_html = [f'<a class="chip{"" if sub else " active"}" href="{e(C.u_cat(lang, cid))}">'
                 f'{e(C.t(lang,"chip_all"))}</a>']
    for s in c["subs"]:
        chip_html.append(
            f'<a class="chip{" active" if s == sub else ""}" href="{e(C.u_sub(lang, cid, s))}">'
            f'{e(C.subT(lang, s))}</a>')
    chips = '<div class="chips">' + "".join(chip_html) + "</div>"

    body = (
        R.cbar(lang, crumb_items=crumb, h1=h1, desc=lead, chips=chips)
        + '<div class="catalog"><div class="wrap">'
        + f'<div class="cathead"><h2>{e(C.subT(lang, sub) if sub else C.t(lang,"sec_all"))}</h2>'
          f'<span class="count">{len(items)} {e(C.t(lang,"items"))} · {e(C.t(lang,"poa"))}</span></div>'
        + R.pgrid(lang, items) + "</div></div>"
    )
    ld = [R.ld_org(),
          R.ld_webpage(lang, url, title, desc, {"@type": "CollectionPage"}),
          R.ld_breadcrumb(crumb[:-1] + [(crumb[-1][0], url)]),
          R.ld_itemlist(lang, items, h1)]
    return url, R.document(lang, title=title, desc=desc, url=url, alts=alts,
                           jsonld_blocks=ld, body=body)


def page_product(lang, p):
    url = C.u_prod(lang, p)
    alts = C.alternates("prod", p=p)
    c = C.CAT_BY_ID[p["cat"]]
    # Titel muss pro Sprache eindeutig sein: die übersetzte Kategorie sorgt dafür,
    # auch wenn die Unterkategorie in allen drei Sprachen gleich heisst (z. B. "Theta").
    sub_t, cat_t = C.subT(lang, p["sub"]), C.catT(lang, c)
    nm = C.pName(lang, p)
    suffix = " | " + C.t(lang, "site_name")
    # Von der ausführlichsten Variante abwärts, bis der Titel unter 68 Zeichen bleibt.
    for cand in (f"MAHE {nm} · {sub_t} – {cat_t}" + suffix,
                 f"MAHE {nm} · {sub_t} – {cat_t}",
                 f"MAHE {nm} · {sub_t}" + suffix,
                 f"MAHE {nm} · {sub_t}"):
        title = cand
        if len(cand) <= 68:
            break
    desc = clip(C.t(lang, "prod_desc_tpl", name=nm, vt=p["vt"], desc=C.pDesc(lang, p)), 165)
    crumb = [(C.t(lang, "nav_home"), C.u_home(lang)),
             (C.t(lang, "nav_products"), C.u_products(lang)),
             (C.catT(lang, c), C.u_cat(lang, p["cat"])),
             (C.subT(lang, p["sub"]), C.u_sub(lang, p["cat"], p["sub"])),
             (nm, None)]

    has_panel = bool(C.fpAssign(p))
    tab1 = C.t(lang, "tab_feat") if has_panel else C.t(lang, "highlights")
    tabs = [("feat", tab1), ("tech", C.t(lang, "tab_tech")),
            ("acc", C.t(lang, "tab_acc")), ("dl", C.t(lang, "tab_dl"))]
    tabbar = "".join(
        f'<button class="tabbtn{" active" if i == 0 else ""}" type="button" role="tab" '
        f'id="tb-{k}" aria-controls="tab-{k}" aria-selected="{"true" if i == 0 else "false"}" '
        f'data-tab="{k}">{e(n)}</button>' for i, (k, n) in enumerate(tabs))
    panes = {
        "feat": front_html(lang, p),
        "tech": spec_html(lang, p),
        "acc": acc_html(lang, p),
        "dl": dl_html(lang, p),
    }
    panehtml = "".join(
        f'<section class="tabpane{" active" if i == 0 else ""}" id="tab-{k}" role="tabpanel" '
        f'aria-labelledby="tb-{k}"><h2 class="sr-only">{e(n)}</h2>{panes[k]}</section>'
        for i, (k, n) in enumerate(tabs))

    body = f"""
<div class="detail"><div class="wrap">
  {R.crumbs(lang, crumb)}
  <div class="dgrid">
    <div class="dimg"><span class="vtag">{e(p['vt'])}</span>
      {R.img_tag(p['img'], "(max-width:900px) 92vw, 520px", alt=f"{C.BRAND} {nm} – {C.pDesc(lang, p)}", eager=True, width=560)}</div>
    <div class="dinfo">
      <p class="kicker">{e(C.catT(lang, c))} · {C.BRAND}</p>
      <h1>{e(p['name'])}</h1>
      <p class="lead">{e(C.pDesc(lang, p))}</p>
      {procs_block(lang, p)}
      <div class="pmeta">
        <div class="m"><span class="lab">{e(C.t(lang,'availability'))}</span>
          <span class="val ok">{e(C.t(lang,'avail_val'))}</span></div>
        <div class="m"><span class="lab">{e(C.t(lang,'brand'))}</span>
          <span class="val">{C.BRAND}</span></div>
        <div class="m"><span class="lab">{e(C.t(lang,'artno'))}</span>
          <span class="val">{e(p['id'].upper())}</span></div>
      </div>
      <div class="poa-box"><span class="p">{e(C.t(lang,'poa'))}</span>
        <span class="s">{e(C.t(lang,'poa_sub'))}</span></div>
      <div class="dactions">
        <button class="btn pri" type="button" data-add="{e(p['id'])}" data-name="{e(p['name'])}"
                data-url="{e(url)}" data-img="{e(R.thumb(p))}">{e(C.t(lang,'to_inquiry'))}</button>
        <a class="btn ghost" href="{e(C.u_page(lang,'contact'))}">{e(C.t(lang,'consult'))}</a>
      </div>
      <p class="prod-intro">{e(C.t(lang,'prod_intro_tpl', name=p['name'], vt=p['vt'], cat=C.catT(lang,c)))}</p>
    </div>
  </div>

  <div class="tabs">
    <div class="tabbar" role="tablist" aria-label="{e(p['name'])}">{tabbar}</div>
    {panehtml}
  </div>
  <noscript><style>.tabpane{{display:block!important}}.tabbar{{display:none}}</style></noscript>

  <p class="backlink"><a href="{e(C.u_cat(lang, p['cat']))}">← {e(C.t(lang,'back_to_cat'))}</a></p>
</div></div>
"""
    ld = [R.ld_org(), R.ld_product(lang, p),
          R.ld_webpage(lang, url, title, desc, {"@type": "ItemPage"}),
          R.ld_breadcrumb(crumb[:-1] + [(p["name"], url)])]
    return url, R.document(lang, title=title, desc=desc, url=url, alts=alts,
                           jsonld_blocks=ld, body=body, og_type="product",
                           og_image=R.img_abs(p["img"], 1000))


def page_processes(lang):
    url, alts = C.u_page(lang, "processes"), C.alternates("page", key="processes")
    cards = ""
    for i, pr in enumerate(C.PROC, 1):
        ic = C.FEAT.get(pr["ic"], {}).get("svg", "")
        cards += (f'<article class="srv"><div class="no">{i:02d}</div>'
                  f'<div class="pic" aria-hidden="true">{ic}</div>'
                  f'<h2>{e(pr["n"].get(lang) or pr["n"]["de"])}</h2>'
                  f'<p>{e(pr["d"].get(lang) or pr["d"]["de"])}</p>'
                  f'<div class="bar" aria-hidden="true"></div></article>')
    body = (R.cbar(lang, crumb_items=[(C.t(lang, "nav_home"), C.u_home(lang)),
                                      (C.t(lang, "n_process"), None)],
                   h1=C.t(lang, "verf_h1"), desc=C.t(lang, "verf_sub"))
            + f'<div class="catalog"><div class="wrap"><div class="procgrid">{cards}</div></div></div>')
    ld = [R.ld_org(), R.ld_webpage(lang, url, C.t(lang, "verf_title"), C.t(lang, "verf_desc")),
          R.ld_breadcrumb([(C.t(lang, "nav_home"), C.u_home(lang)),
                           (C.t(lang, "n_process"), url)])]
    return url, R.document(lang, title=C.t(lang, "verf_title"), desc=C.t(lang, "verf_desc"),
                           url=url, alts=alts, jsonld_blocks=ld, body=body)


def page_downloads(lang):
    url, alts = C.u_page(lang, "downloads"), C.alternates("page", key="downloads")
    items = "".join(
        f'<a class="dlitem" href="{e(d["u"])}" target="_blank" rel="noopener nofollow">'
        f'<div class="ico">{e(d["k"])}</div><div class="nm">{e(d["t"].get(lang) or d["t"]["de"])}'
        f'<span>{e(d["s"].get(lang) or d["s"]["de"])}</span></div>'
        f'<span class="arw" aria-hidden="true">↓</span></a>' for d in C.DLS)
    body = (R.cbar(lang, crumb_items=[(C.t(lang, "nav_home"), C.u_home(lang)),
                                      (C.t(lang, "n_downloads"), None)],
                   h1=C.t(lang, "dl_h1"), desc=C.t(lang, "dl_sub"))
            + f'<div class="catalog"><div class="wrap">'
              f'<div class="dlrow" style="max-width:680px">{items}</div></div></div>')
    ld = [R.ld_org(), R.ld_webpage(lang, url, C.t(lang, "dl_title"), C.t(lang, "dl_desc")),
          R.ld_breadcrumb([(C.t(lang, "nav_home"), C.u_home(lang)),
                           (C.t(lang, "n_downloads"), url)])]
    return url, R.document(lang, title=C.t(lang, "dl_title"), desc=C.t(lang, "dl_desc"),
                           url=url, alts=alts, jsonld_blocks=ld, body=body)


def page_contact(lang):
    url, alts = C.u_page(lang, "contact"), C.alternates("page", key="contact")
    co = C.COMPANY
    body = (R.cbar(lang, crumb_items=[(C.t(lang, "nav_home"), C.u_home(lang)),
                                      (C.t(lang, "n_contact"), None)],
                   h1=C.t(lang, "k_h1"), desc=C.t(lang, "k_desc"))
            + f"""<div class="catalog"><div class="wrap kontaktwrap">
  <form class="form kform" id="kontaktForm" novalidate>
    <label for="kName">{e(C.t(lang,'f_name'))}</label>
    <input id="kName" name="name" type="text" required autocomplete="organization">
    <label for="kMail">{e(C.t(lang,'f_mail'))}</label>
    <input id="kMail" name="email" type="email" required autocomplete="email">
    <label for="kTel">{e(C.t(lang,'k_tel'))}</label>
    <input id="kTel" name="phone" type="tel" autocomplete="tel" placeholder="+41 …">
    <label for="kMsg">{e(C.t(lang,'k_msg'))}</label>
    <textarea id="kMsg" name="message" rows="5" required></textarea>
    <input type="checkbox" name="botcheck" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
    <button class="send" type="submit">{e(C.t(lang,'f_send'))}</button>
    <p class="fstatus" role="status" aria-live="polite"></p>
  </form>
  <aside class="kinfo">
    <h2>{e(C.t(lang,'site_name'))}</h2>
    <address>
      {e(co['street'])}<br>{co['zip']} {e(co['city'])}<br>{e(co['country_name'])}<br><br>
      <a class="accent" href="tel:{co['phone_href']}">{e(co['phone'])}</a><br>
      <a class="accent" href="mailto:{co['email']}">{co['email']}</a><br><br>
      {e(C.t(lang,'hours'))}
    </address>
  </aside>
</div></div>""")
    ld = [R.ld_org(),
          R.ld_webpage(lang, url, C.t(lang, "kontakt_title"), C.t(lang, "kontakt_desc"),
                       {"@type": "ContactPage"}),
          R.ld_breadcrumb([(C.t(lang, "nav_home"), C.u_home(lang)),
                           (C.t(lang, "n_contact"), url)])]
    return url, R.document(lang, title=C.t(lang, "kontakt_title"), desc=C.t(lang, "kontakt_desc"),
                           url=url, alts=alts, jsonld_blocks=ld, body=body)


def page_faq(lang):
    url, alts = C.u_page(lang, "faq"), C.alternates("page", key="faq")
    body = (R.cbar(lang, crumb_items=[(C.t(lang, "nav_home"), C.u_home(lang)),
                                      (C.t(lang, "nav_faq"), None)],
                   h1=C.t(lang, "faq_h1"), desc=C.t(lang, "faq_lead"))
            + '<div class="catalog"><div class="wrap textwrap">'
            + R.faq_block(lang, C.EX[lang]["faq"]) + "</div></div>")
    # Die FAQPage liefert ld_faq() mitsamt mainEntity. Die WebPage bleibt WebPage –
    # sonst stuenden zwei FAQPage-Knoten auf der Seite und einer davon ohne Fragen.
    ld = [R.ld_org(), R.ld_faq(lang),
          R.ld_webpage(lang, url, C.t(lang, "faq_title"), C.t(lang, "faq_desc")),
          R.ld_breadcrumb([(C.t(lang, "nav_home"), C.u_home(lang)),
                           (C.t(lang, "nav_faq"), url)])]
    return url, R.document(lang, title=C.t(lang, "faq_title"), desc=C.t(lang, "faq_desc"),
                           url=url, alts=alts, jsonld_blocks=ld, body=body)


def page_search(lang):
    url, alts = C.u_page(lang, "search"), C.alternates("page", key="search")
    popular = ["HyperMIG", "WIG AC/DC", "Theta", "Cleaner", "Fahrwagen", "Plasma"]
    chips = "".join(f'<a class="chip" href="{e(url)}?q={e(x)}">{e(x)}</a>' for x in popular)
    body = (R.cbar(lang, crumb_items=[(C.t(lang, "nav_home"), C.u_home(lang)),
                                      (C.t(lang, "c_search"), None)],
                   h1=C.t(lang, "search_h1"), desc=C.t(lang, "search_lead"),
                   chips=f'<div class="chips">{chips}</div>')
            + f"""<div class="catalog"><div class="wrap">
  <form class="bigsearch" role="search" action="{e(url)}" method="get" id="pageSearchForm">
    <input id="pq" name="q" type="search" placeholder="{e(C.t(lang,'search_ph'))}"
           aria-label="{e(C.t(lang,'c_search'))}" spellcheck="false">
    <button type="submit">{e(C.t(lang,'search_btn'))}</button>
  </form>
  <div class="cathead"><h2 id="srTitle">{e(C.t(lang,'search_h1'))}</h2>
    <span class="count" id="srCount"></span></div>
  <div id="srResults"></div>
  <noscript><p class="noacc">{e(C.t(lang,'search_lead'))}
    <a href="{e(C.u_products(lang))}">{e(C.t(lang,'nav_all_products'))}</a></p></noscript>
</div></div>""")
    ld = [R.ld_org(), R.ld_webpage(lang, url, C.t(lang, "search_title"), C.t(lang, "search_desc"),
                                   {"@type": "SearchResultsPage"})]
    return url, R.document(lang, title=C.t(lang, "search_title"), desc=C.t(lang, "search_desc"),
                           url=url, alts=alts, jsonld_blocks=ld, body=body,
                           robots="noindex,follow")


# Rechtsseiten: URL-Schluessel -> Text-Praefix in i18n_extra -> nav-Schluessel.
# Das Impressum darf indexiert werden: es traegt Name, Adresse und Telefonnummer
# und ist damit ein Beleg fuer die lokale Suche. AGB und Datenschutzerklaerung
# bleiben noindex – sie gehoeren nicht in die Suchergebnisse.
LEGAL = {
    "imprint": ("impressum", "nav_impressum", "index,follow"),
    "privacy": ("datenschutz", "nav_datenschutz", "noindex,follow"),
    "terms":   ("agb", "nav_agb", "noindex,follow"),
}


def page_legal(lang, kind):
    tkey, navkey, robots = LEGAL[kind]
    url, alts = C.u_page(lang, kind), C.alternates("page", key=kind)
    nav = C.t(lang, navkey)
    # Der Text bringt sein eigenes <p>/<ul> mit – Rechtstexte brauchen Listen,
    # und eine Liste in einem <p> waere kaputtes HTML.
    secs = "".join(
        f"<section><h2>{e(h)}</h2>{b if b.lstrip().startswith('<') else '<p>' + b + '</p>'}</section>"
        for h, b in C.EX[lang][f"{tkey}_body"])
    body = (R.cbar(lang, crumb_items=[(C.t(lang, "nav_home"), C.u_home(lang)), (nav, None)],
                   h1=C.t(lang, f"{tkey}_h1"), desc="")
            + f'<div class="catalog"><div class="wrap textwrap legal">{secs}</div></div>')
    title, desc = C.t(lang, f"{tkey}_title"), C.t(lang, f"{tkey}_desc")
    ld = [R.ld_org(), R.ld_webpage(lang, url, title, desc),
          R.ld_breadcrumb([(C.t(lang, "nav_home"), C.u_home(lang)), (nav, url)])]
    return url, R.document(lang, title=title, desc=desc, url=url, alts=alts,
                           jsonld_blocks=ld, body=body, robots=robots)


def page_404(lang=C.DEFAULT_LANG):
    url, alts = "/404.html", C.alternates("home")
    body = f"""<div class="cbar"><div class="wrap">
  <h1>{e(C.t(lang,'err404_h1'))}</h1><p class="desc">{e(C.t(lang,'err404_lead'))}</p>
  <p style="margin-top:24px"><a class="btn pri" href="/">{e(C.t(lang,'err404_cta'))}</a></p>
</div></div>"""
    return url, R.document(lang, title=C.t(lang, "err404_title"), desc=C.t(lang, "err404_lead"),
                           url="/", alts=alts, jsonld_blocks=[R.ld_org()], body=body,
                           robots="noindex,follow")
