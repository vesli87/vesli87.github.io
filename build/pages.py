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
TRAINING = json.loads((C.DATA / "TRAINING.json").read_text("utf-8"))

# Wie breit das Bild auf der Produktseite wirklich wird.
#
# Drei Deckel wirken zusammen:
#   * die Spalte - Fensterbreite minus 28 px Aussenpolster je Seite, ab 1000 px
#     zweispaltig mit 44 px Abstand, hoechstens 1400 px breit;
#   * der Rahmen - das Bild fuellt hoechstens 90 % davon (site.css: .dimg > img);
#   * das width-Attribut, das render.img_tag auf hoechstens 560 setzt.
#
# Ohne den dritten Deckel versprach sizes bei 900 px Fensterbreite 788 px; ein
# Telefon mit dreifacher Punktdichte rechnete 2364 und griff zur 3000er Stufe -
# 373 kB fuer ein Bild, das nie breiter als 560 px erscheint. 90 % der Spalte
# erreichen die 560 px bei 678 px Fensterbreite, darum dort der Umbruch.
# Ausgerechnet statt mit min(): das versteht auch ein aelterer Browser.
DIMG_SIZES = ("(max-width:678px) calc(90vw - 51px), "
              "(max-width:1000px) 560px, "
              "(max-width:1400px) calc((90vw - 90px) / 2.12), "
              "552px")

# Achtung: DLS[].k ist NICHT eindeutig – Produktkatalog und EN-1090-Zertifikat
# tragen beide "PDF". Deshalb wird hier über den Titel identifiziert.
# Ausgehende Verweise auf den Hersteller und auf die Partnerwerkstatt tragen
# bewusst KEIN nofollow.
#
# nofollow ist fuer bezahlte Verweise und fuer Inhalte gedacht, fuer die man
# nicht geradesteht - Gaestebuecher, Kommentare. Hier ist beides nicht der
# Fall: mahe-online.de ist der Hersteller, dessen Programm diese Website
# fuehrt, und die Schweisstechnik Scherrer AG ist die Firma, in deren
# Werkstatt gearbeitet wird. Genau diese beiden Verbindungen soll eine
# Suchmaschine erkennen. Mit nofollow stand auf jeder dieser 582 Stellen das
# Gegenteil: bitte nicht zuordnen.
#
# noopener bleibt - das ist Sicherheit und hat mit Bewertung nichts zu tun.
DL_CATALOG = next(d for d in C.DLS if "Produktkatalog" in d["t"]["de"])
DL_EN1090 = next(d for d in C.DLS if "1090" in d["t"]["de"])
DL_SDS = {d["k"]: d for d in C.DLS if d["k"] != "PDF"}     # R1, RP1, P1, M1, N1


# --------------------------------------------------------------------------
# Persönliche Geräteschulung; keine Händler- oder Unternehmenszertifizierung.
# Das vollständige, vom Inhaber bereitgestellte Dokument bleibt zoombar.
def training_block(lang, on_about=False):
    copy = TRAINING["copy"][lang]
    photo = R.img_tag(TRAINING["image"],
                      "(max-width:760px) min(calc(100vw - 84px), 640px), "
                      "(max-width:800px) min(calc(100vw - 108px), 640px), "
                      "(max-width:1440px) calc(52vw - 83px), 665px",
                      cls="zoomable", alt=copy["alt"], width=1448)
    topics = "".join(f'<li>{e(topic)}</li>' for topic in copy["topics"])
    target = C.u_page(lang, "contact") if on_about else C.u_page(lang, "about") + "#mahe-training"
    cta = C.t(lang, "n_contact") if on_about else copy["details"]
    return (
        '<section class="wrap mahe-training" id="mahe-training" aria-labelledby="mahe-training-title">'
        '<div class="mahe-training-card">'
        f'<figure class="mahe-training-photo">{photo}'
        f'<figcaption>{e(copy["zoom"])}</figcaption></figure>'
        '<div class="mahe-training-copy">'
        f'<p class="p-eyebrow">{e(copy["eyebrow"])}</p>'
        f'<h2 id="mahe-training-title">{e(copy["heading"])}</h2>'
        f'<p>{e(copy["summary"])}</p><ul>{topics}</ul>'
        '<dl class="mahe-training-facts">'
        f'<div><dt>{e(copy["date_label"])}</dt><dd><time datetime="{e(TRAINING["date"])}">{e(copy["date_text"])}</time></dd></div>'
        f'<div><dt>{e(copy["place_label"])}</dt><dd>{e(TRAINING["place"])}</dd></div>'
        f'<div><dt>{e(copy["certificate_label"])}</dt><dd>{e(TRAINING["number"])}</dd></div>'
        '</dl>'
        f'<a class="volt-text-link" href="{e(target)}">{e(cta)} <span aria-hidden="true">→</span></a>'
        '</div></div></section>'
    )


# Produktbezogene Blöcke
# --------------------------------------------------------------------------

def dls_for(p):
    """Für das Produkt relevante PDFs.

    Zuerst das, was zu genau diesem Gerät gehört: Bedienungsanleitung und
    technisches Datenblatt beim Hersteller. Danach erst das Allgemeine -
    Sicherheitsdatenblätter und Katalog. Wer eine Anleitung
    sucht, soll sie nicht unter drei generischen PDFs hervorkramen müssen.
    """
    out = list(C.DLDEV.get(p["id"], [])) + list(C.DLOCC.get(p["id"], []))
    if p["sub"] == "Elektrolyte" and p["id"].upper() in DL_SDS:
        out.append(DL_SDS[p["id"].upper()])
    if p["cat"] == "reinigung" and p["sub"] == "Cleaner":
        out += [DL_SDS[k] for k in ("R1", "RP1", "P1", "M1", "N1") if k in DL_SDS]
    # Die Herstellererklaerung vom 30.01.2016 nennt nur sechs Baureihen.
    # Sie bleibt mit Datum und Geltungsbereich im Downloadverzeichnis;
    # daraus folgt kein Konformitaetsnachweis fuer jedes aktuelle Modell.
    # Der MAHE-Produktkatalog gehoert nur zu MAHE-Geraeten. Bei einer
    # gebrauchten Oerlikon-Anlage haette er dort nichts verloren - er fuehrt
    # ein anderes Programm eines anderen Herstellers.
    if C.istMahe(p):
        out.append(DL_CATALOG)
    seen, res = set(), []
    for d in out:
        if d["u"] not in seen:
            seen.add(d["u"])
            res.append(d)
    return res


def procs_block(lang, p):
    # Die Symbole stehen in Gruppen, so wie MAHE sie im Katalog setzt: eine
    # Kopfzeile (MIG, WIG, Elektrode, Plasma, Reinigen) und darunter die
    # Kacheln, die das Geraet in dieser Disziplin beherrscht.
    badges = ""
    for gruppe, keys in C.symbolsOf(p):
        kacheln = ""
        for k in keys:
            f = C.FEAT.get(k)
            if not f:
                continue
            # Die Kachel ist das Bild des Herstellers aus seinem Katalog, nicht
            # ein Nachbau. Beschriftung steht im Bild und noch einmal als Text
            # darunter - fuer Suche, Screenreader und kleine Bildschirme.
            kacheln += (f'<div class="procbadge">'
                        f'<img class="ic" src="{f["img"]}" width="{f["w"]}" height="{f["h"]}" '
                        f'alt="{e(C.featLabel(lang, k))}" aria-hidden="true" loading="lazy" decoding="async">'
                        f'<div class="lb">{e(C.featLabel(lang, k))}</div></div>')
        if kacheln:
            badges += (f'<div class="symgrp"><span class="symgrp-h">'
                       f'{e(C.t(lang, "sym_" + gruppe))}</span>'
                       f'<div class="symrow">{kacheln}</div></div>')
    mats = C.matOf(p)
    chips = ""
    if mats:
        chips = ('<div class="matchips">' + "".join(
            f'<span class="matchip"><b>{m}</b>{e(C.matLabel(lang, m))}</span>' for m in mats
        ) + "</div>")
    scope = ''
    if p['id'] == 'hypermig-x':
        copy = C.HYPERMIG_CWK[lang]
        scope = (f'<p class="symbol-scope">{e(copy["summary_note"])} '
                 f'<a href="#hypermig-cwk">{e(copy["summary_link"])}</a></p>')
    return f'<div class="procs">{badges}{chips}{scope}</div>'


def quickfacts_html(lang, p):
    facts = C.quickFacts(lang, p)
    rows = ''.join(f'<div><dt>{e(label)}</dt><dd>{e(value)}</dd></div>' for label, value in facts)
    data = (f'<h2>{e(C.t(lang, "facts_title"))}</h2><dl>{rows}</dl>' if rows else '')
    return (f'<div class="product-facts">{data}'
            f'<a class="detail-jump" href="#tab-tech">{e(C.t(lang, "all_tech_data"))}'
            '<span aria-hidden="true"> →</span></a></div>')


def cwk_benefits(lang):
    guide = C.HYPERMIG_CWK
    copy = guide[lang]
    symbols = ''
    for key in guide['symbols']:
        feature = C.FEAT[key]
        label = C.featLabel(lang, key)
        symbols += (f'<li class="mahe-symbol-card" data-mahe-symbol="{e(key)}">'
                    f'<img src="{e(feature["img"])}" width="{feature["w"]}" height="{feature["h"]}" '
                    f'alt="{e(label)}" aria-hidden="true" loading="lazy" decoding="async">'
                    f'<div><h5>{e(label)}</h5><p>{e(copy["symbol_notes"][key])}</p></div></li>')
    benefits = ''.join(f'<div><dt>{e(title)}</dt><dd>{e(text)}</dd></div>'
                       for title, text in copy['benefits'])
    rows = ''
    for row in guide['matrix']:
        label = C.featLabel(lang, row['feature']) if row.get('feature') else copy['mma_label']
        cells = ''.join(f'<td class="cwk-{state}">{e(copy["status"][state])}</td>' for state in row['states'])
        rows += f'<tr data-cwk-feature="{e(row["id"])}"><th scope="row">{e(label)}</th>{cells}</tr>'
    return (f'<section class="mahe-cwk" id="hypermig-cwk"><h3>{e(copy["title"])}</h3>'
            f'<p class="cwk-intro">{e(copy["intro"])}</p><h4>{e(copy["symbols_title"])}</h4>'
            f'<ul class="mahe-symbol-grid">{symbols}</ul><h4>{e(copy["benefits_title"])}</h4>'
            f'<dl class="cwk-benefits">{benefits}</dl><h4>{e(copy["matrix_title"])}</h4>'
            f'<p class="cwk-scroll-hint" id="cwk-scroll-hint">{e(copy["scroll_hint"])}</p>'
            f'<div class="spectab-scroll cwk-compare" tabindex="0" role="region" '
            f'aria-label="{e(copy["matrix_title"])}" aria-describedby="cwk-scroll-hint">'
            f'<table class="spectab"><caption class="sr-only">{e(copy["matrix_title"])}</caption>'
            f'<thead><tr><th scope="col">{e(copy["matrix_label"])}</th>'
            '<th scope="col">X CWK</th><th scope="col">HX CWK</th><th scope="col">EX CWK</th><th scope="col">SX CWK</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div><p class="cwk-note">{e(copy["matrix_note"])}</p>'
            f'<p class="cwk-note">{e(copy["scope_note"])}</p><p class="cwk-tech-note">{e(copy["technical_note"])}</p>'
            f'<p><a href="{e(guide["source"]["url"])}">{e(copy["source_label"])}</a></p></section>')


def front_html(lang, p):
    """Fronteingabe- bzw. Besonderheiten-Tab, vorgerendert."""
    panels = C.fpAssign(p)
    hl = C.highlightsOf(lang, p)
    out = []
    varianten = C.hlVariants(lang, p)
    if p['id'] == 'hypermig-x':
        out.append(cwk_benefits(lang))
    elif varianten:
        # Der Hersteller stellt die Ausfuehrungen nebeneinander, jede mit Bild
        # und eigener Liste. Genau so hier – eine gemeinsame Liste wuerde die
        # schwaecheren Ausfuehrungen zu gut aussehen lassen.
        out.append(f'<h3 class="besond">{e(C.t(lang, "highlights"))}</h3>'
                   '<div class="varianten">')
        for name, img, items in varianten:
            bild = R.img_tag(img, "(max-width:760px) 90vw, 260px", cls="var-img zoomable",
                             alt=f"{C.pBrand(p)} {name}", width=260)
            out.append(f'<div class="variante"><h4 class="var-t">{e(name)}</h4>{bild}'
                       '<ul class="besond-list var-list">'
                       + "".join(f"<li>{e(x)}</li>" for x in items) + "</ul></div>")
        out.append("</div>")
    elif hl:
        out.append('<div class="fp-highlights"><h3 class="besond">'
                   + e(C.t(lang, "highlights")) + '</h3><ul class="besond-list">'
                   + "".join(f"<li>{e(x)}</li>" for x in hl) + "</ul></div>")
    if panels:
        out.append(f'<h3 class="fp-section">{e(C.t(lang,"front_h"))}</h3>')
        gruppen = C.fpGroups(p)
        # Gliedert der Hersteller nach Geraetevarianten, rutschen die
        # Paneltitel eine Ebene tiefer - sonst stuende die Variante auf
        # derselben Stufe wie das Panel darunter.
        mit_variante = any(name for name, _ in gruppen)
        h_panel, h_bes = ("h5", "h6") if mit_variante else ("h4", "h5")
        for variante, keys in gruppen:
          if variante:
            out.append(f'<h4 class="fp-variant">{e(variante)}</h4>')
          for pk in keys:
            fp = C.FP[pk]
            # Unter dem Panelfoto steht nur, was MAHE zu genau diesem Panel
            # schreibt. Wo der Hersteller nichts veroeffentlicht, steht auch bei
            # uns nichts – frueher lief das auf einen selbst verfassten Text
            # hinaus, der bei allen fuenf Theta-Modellen derselbe war.
            src = C.PANEL_HL_DEVICE.get(pk)
            ph = (src.get(lang) or src["de"]) if src else []
            if fp.get("img"):
                media = R.img_tag(fp["img"], ("(max-width:760px) 90vw, 560px" if pk in C.PANEL_GUIDES else "(max-width:760px) 90vw, 340px"),
                                  cls="fp-photo zoomable",
                                  alt=f"{C.pBrand(p)} {C.fpName(lang, fp)}", width=340)
            else:
                media = PANEL_DRAWN["big" if fp.get("big") else "small"]
            bes = ""
            if ph:
                bes = (f'<div class="fp-right">'
                       f'<{h_bes} class="besond">{e(C.t(lang,"front_bes"))}</{h_bes}>'
                       f'<ul class="besond-list fp-list">'
                       + "".join(f"<li>{e(x)}</li>" for x in ph)
                       + "</ul></div>")
            guide = C.PANEL_GUIDES.get(pk)
            explanation = ""
            if guide:
                copy = guide[lang]
                sections = "".join(f'<div><dt>{e(title)}</dt><dd>{e(text)}</dd></div>'
                                   for title, text in copy['sections'])
                sources = " · ".join(f'<a href="{e(source["url"])}">{e(source["title"])}</a>'
                                     for source in guide['sources'])
                explanation = (f'<div class="fp-guide"><{h_bes}>{e(copy["heading"])}</{h_bes}>'
                               f'<p>{e(copy["intro"])}</p><dl>{sections}</dl>'
                               f'<p class="fp-note">{e(copy["note"])}</p>'
                               f'<p><a href="{e(C.u_page(lang, "processes"))}">{e(copy["processes_label"])}</a></p>'
                               f'<p class="fp-sources">{e(copy["sources_label"])}: {sources}</p></div>')
            out.append(
                f'<div class="fp{" fp-graphic" if guide else ""}{"" if ph else " fp-solo"}"'
                + (f' id="panel-{e(pk.replace("_", "-"))}"' if guide else '') + '>'
                f'<{h_panel} class="fp-title">{e(C.fpName(lang, fp))}</{h_panel}>'
                f'<div class="fp-body"><div class="fp-panel">{media}</div>'
                f"{bes}</div>{explanation}</div>"
            )
    elif not hl:
        feats = C.featOf(p)
        if feats:
            out.append('<div class="featlist">' + "".join(
                f'<div class="fitem"><img src="{C.FEAT[k]["img"]}" width="{C.FEAT[k]["w"]}" '
                f'height="{C.FEAT[k]["h"]}" alt="{e(C.featLabel(lang, k))}" aria-hidden="true" loading="lazy" decoding="async">'
                f'<span>{e(C.featLabel(lang, k))}</span></div>'
                for k in feats
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
        if t.get('source'):
            out.append(f'<p class="spectab-note"><a href="{e(t["source"])}">{e(C.HYPERMIG_CWK[lang]["source_label"])}</a></p>')

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


def media_html(lang, p, nm):
    """Hauptbild mit Miniaturen darunter.

    Ein Klick auf eine Miniatur zeigt das Bild gross - so, wie es Kundschaft von
    jedem Shop kennt. Vorher standen die Zusatzbilder untereinander; das drueckte
    die technischen Daten weit nach unten und niemand sah das Detail gross.

    Ohne JavaScript bleibt alles lesbar: dann sind schlicht alle Bilder
    untereinander sichtbar (siehe noscript-Regel in der Seite).
    """
    # Zeigt das Bild nicht schlicht das Geraet allein, steht darunter, was
    # es wirklich zeigt - siehe data/IMGCAP.json. Ohne Eintrag bleibt es leer.
    bu = C.IMGCAP.get(p["id"]) or {}
    haupt = {"img": p["img"],
             "cap": bu.get(lang) or bu.get("de") or "",
             "alt": f"{C.pFullName(lang, p)}: {C.pDesc(lang, p)}"}
    bilder = [haupt]
    for g in C.galleryOf(lang, p):
        bilder.append({"img": g["img"], "cap": g["cap"], "alt": g["alt"]})

    # Über dem Foto lag früher ein Etikett mit den Schweissverfahren. Es stand im
    # Markup vor dem Bild und wurde davon verdeckt - sichtbar blieb nur ein
    # schwarzer Winkel in der Ecke. Die Verfahren stehen in den technischen
    # Daten und in der Merkmalsliste; auf dem Bild braucht es sie nicht.
    if len(bilder) == 1:
        rahmen = (f'<div class="dimg{R.dimg_klasse(p["img"])}">'
                  + R.img_tag(p["img"], DIMG_SIZES, cls="zoomable",
                              alt=haupt["alt"], eager=True, width=560)
                  + "</div>")
        # Ohne Diaschau gab es hier bisher keine Bildunterschrift. Bei einem
        # Bild, das etwas anderes zeigt als das Geraet allein, muss sie
        # trotzdem darunter stehen.
        if haupt["cap"]:
            return (f'<figure class="dimg-fig">{rahmen}'
                    f'<figcaption>{e(haupt["cap"])}</figcaption></figure>')
        return rahmen

    slides = ""
    for i, b in enumerate(bilder):
        slides += (f'<figure class="galslide{" active" if i == 0 else ""}" '
                   f'id="gs-{e(p["id"])}-{i}" role="tabpanel" '
                   f'aria-labelledby="gt-{e(p["id"])}-{i}">'
                   + f'<div class="dimg{R.dimg_klasse(b["img"])}">'
                   + R.img_tag(b["img"], DIMG_SIZES, cls="zoomable",
                               alt=b["alt"], eager=(i == 0), width=560)
                   + '</div>'
                   + (f'<figcaption>{e(b["cap"])}</figcaption>' if b["cap"] else "")
                   + "</figure>")

    thumbs = ""
    for i, b in enumerate(bilder):
        # Der Miniaturstreifen ist eine Auswahl, keine Navigation: deshalb
        # tablist/tab und nicht Links. Das Bild benennt die Auswahl selbst;
        # der gekuerzte title bleibt nur der zusaetzliche Maus-Tooltip.
        thumbs += (f'<button class="galthumb{" active" if i == 0 else ""}" type="button" '
                   f'role="tab" aria-selected="{"true" if i == 0 else "false"}" '
                   f'id="gt-{e(p["id"])}-{i}" tabindex="{0 if i == 0 else -1}" '
                   f'aria-controls="gs-{e(p["id"])}-{i}" data-i="{i}" '
                   f'title="{e(b["alt"][:110])}">'
                   + R.img_tag(b["img"], "84px", alt=b["alt"], width=84)
                   + "</button>")

    return (f'<div class="dmedia" data-gal>'
            f'<div class="galstage">'
            f'<button class="galnav prev" type="button" data-step="-1" '
            f'aria-label="{e(C.t(lang, "gal_prev"))}">‹</button>'
            f'{slides}'
            f'<button class="galnav next" type="button" data-step="1" '
            f'aria-label="{e(C.t(lang, "gal_next"))}">›</button></div>'
            f'<div class="galthumbs" role="tablist" '
            f'aria-label="{e(C.t(lang, "gal_label"))}">{thumbs}</div>'
            f'</div>')


def opt_html(lang, p):
    """Optionen als eigene Liste - nicht als Aufzaehlungspunkt unter den
    Besonderheiten. Was im Lieferumfang steckt und was dazubestellt wird, darf
    eine Kundschaft nicht erst aus einem Fliesstext heraussuchen muessen."""
    opts = C.optionsOf(lang, p)
    if not opts:
        return ""
    rows = ""
    for o in opts:
        t = o.get("t") if isinstance(o, dict) else str(o)
        sub = o.get("s") if isinstance(o, dict) else ""
        rows += (f'<li><span class="ot">{e(t)}</span>'
                 + (f'<span class="os">{e(sub)}</span>' if sub else "") + "</li>")
    return (f'<h3 class="opth">{e(C.t(lang,"tab_opt"))}</h3>'
            f'<ul class="optlist">{rows}</ul>'
            f'<p class="optnote">{e(C.t(lang,"opt_note"))}</p>')


def karten(lang, ids, mit_marke=False):
    """Ein Raster aus Produktkarten – fuer beide Richtungen der Zuordnung.

    mit_marke: die Kennzeile nennt auch bei MAHE die Marke. Gebraucht im
    Abschnitt "Ebenfalls interessant", wo das neue MAHE-Geraet neben der
    gebrauchten Oerlikon steht - dort ist "MAHE · Plasma TIG" gegen
    "Occasion · Mikroplasma" genau der Unterschied, der zaehlt.
    """
    cards = ""
    for pid in ids:
        a = C.BY_ID[pid]
        alt = C.pFullName(lang, a)
        im = R.img_tag(a["img"], "(max-width:760px) 40vw, 180px", alt=alt)
        # Im MAHE-Katalog heisst die Karte nach dem Geraet. Eine Fremdmarke
        # traegt ihren Namen, und eine Occasion sagt in der Kennzeile, dass
        # sie gebraucht ist - sonst stuende neben dem neuen MAHE-Geraet eine
        # Karte, die wie ein zweites Neugeraet aussieht.
        titel = C.pName(lang, a) if C.istMahe(a) else C.pFullName(lang, a)
        kennzeile = C.vtT(lang, a["vt"])
        if a["cat"] == "occasion":
            kennzeile = f"{C.catT(lang, C.CAT_BY_ID['occasion'])} · {kennzeile}"
        elif mit_marke:
            kennzeile = f"{C.pBrand(a)} · {kennzeile}"
        cards += (
            f'<a class="acccard" href="{e(C.u_prod(lang, a))}">'
            f'<div class="im">{im}</div>'
            f'<div class="bd"><div class="vt">{e(kennzeile)}</div><h3>{e(titel)}</h3>'
            f'<p>{e(C.pDesc(lang, a))}</p></div></a>'
        )
    return f'<div class="accgrid">{cards}</div>'


def accessory_context_html(lang, p):
    """Qualified family links, not new compatibility entries in ACC.json.

    P.json names MMS 3000 for WK 300 and HyperMIG X for DVL 420.
    SUBCATEGORY_GUIDES.json explains the configuration details to supply.
    The MMS destination also covers MMS 2000, so retain the 3000 qualifier.
    """
    related = {"wk300": "mms", "dvl420": "hypermig-x"}
    device_id = related.get(p["id"])
    if not device_id:
        return ""
    device = C.BY_ID[device_id]
    link = (f'<a href="{e(C.u_prod(lang, device))}">'
            f'{e(C.pName(lang, device))}</a>')
    text = e(C.t(lang, f'accessory_context_{p["id"]}')).format(device=link)
    return f'<p class="prod-intro accessory-context">{text}</p>'


def acc_html(lang, p):
    """Der Reiter an vierter Stelle – je nachdem, was das Produkt ist.

    Ein Geraet fuehrt sein Zubehoer auf. Ein Zubehoerteil fuehrt umgekehrt die
    Geraete auf, an die es gehoert; frueher stand dort auf 43 Seiten nur der
    Hinweis, es sei kein Zubehoer hinterlegt.
    """
    acc = C.relatedAcc(p)
    if acc:
        return karten(lang, acc)
    zu = C.geraeteZu(p)
    if zu:
        return (f'<p class="fitsnote">{e(C.t(lang,"fits_note"))}</p>'
                + karten(lang, zu))
    # Weder das eine noch das andere: der Reiter entfaellt. Der Satz, der hier
    # stand, war auf einem Ersatzkabel ausserdem falsch - es ist kein Geraet.
    return ""


def occ_text_html(lang, p):
    """Beschreibung und Fragen einer Occasion (data/OCCTEXT.json).

    Sichtbar unter den Reitern, nicht in einem Reiter: Wer die Seite liest,
    soll den Text sehen, ohne zu klicken. Die Fragen werden mit faq_block
    gesetzt (h2-Abschnitt, h3-Fragen) und stehen zusaetzlich als FAQPage im
    JSON-LD.
    """
    ot = C.occText(lang, p)
    if not ot:
        return ""
    teile = "".join(
        f'<h2>{e(a["h"])}</h2>' + "".join(f"<p>{e(x)}</p>" for x in a["p"])
        for a in ot.get("abschnitte", []))
    fragen = (R.faq_block(lang, ot["faq"], h=C.t(lang, "occ_faq_h"))
              if ot.get("faq") else "")
    return f'<div class="otext">{teile}{fragen}</div>'


def verwandt_html(lang, p):
    """Karten zu verwandten Produkten (data/VERWANDT.json), z. B. das neue
    MAHE-Geraet unter der Occasion derselben Technik und umgekehrt."""
    ids = C.verwandt(p)
    if not ids:
        return ""
    return (f'<div class="verwandt"><h2 class="sec-h">{e(C.t(lang, "verwandt_h"))}</h2>'
            f'{karten(lang, ids, mit_marke=True)}</div>')


def dl_html(lang, p):
    items = ""
    for d in dls_for(p):
        items += (
            f'<a class="dlitem" href="{e(d["u"])}" target="_blank" rel="noopener">'
            f'<div class="ico">{e(d["k"])}</div>'
            f'<div class="nm">{e(d["t"].get(lang) or d["t"]["de"])}'
            f'<span>{e(d["s"].get(lang) or d["s"]["de"])}</span></div>'
            f'<span class="arw" aria-hidden="true">↓</span></a>'
        )
    return f'<div class="dlrow">{items}</div>'


def clip(s, n):
    """Kürzt eine meta description an der Wortgrenze.

    Google schneidet den Ausschnitt nach Pixelbreite ab, in der Praxis bei
    etwa 155 bis 160 Zeichen. Der Aufrufwert stand auf 165 - damit lagen 179
    von 345 Seiten darüber und wurden in der Anzeige abgeschnitten. 155 lässt
    Luft: das angehängte " …" kommt noch dazu.

    Gemessen wird am **maskierten** Text, nicht am rohen. Vorher wurde vor dem
    Maskieren gekürzt: aus einem Apostroph wurde danach `&#x27;`, aus einem
    Zeichen also sechs. Bei „Câble d'électrode" wuchs die fertige Angabe so auf
    161 Zeichen, obwohl hier 155 gezählt worden waren. Ahrefs hat das am
    03.09.2026 als „Meta-Beschreibung zu lang" gemeldet.
    """
    s = " ".join(s.split())
    if len(e(s)) <= n:
        return s
    # So weit zurueckgehen, bis auch die maskierte Fassung passt.
    grenze = n
    while grenze > 40:
        cut = s[:grenze]
        leer = cut.rfind(" ")
        gekuerzt = (cut[:leer] if leer > 0 else cut).rstrip(" ,.;:–-") + " …"
        if len(e(gekuerzt)) <= n:
            return gekuerzt
        grenze -= 4
    return s[:grenze]


# --------------------------------------------------------------------------
# Seiten
# --------------------------------------------------------------------------

def hero_folien(lang):
    """Die Folien des Bandes, gesteuert von core.HERO_SLIDES.

    Frueher standen beide Folien fest im Markup, samt zweier Punkte darunter.
    Eine Folie wegzunehmen hiess: drei Stellen aendern und hoffen, dass die
    Punkte dazu passen. Jetzt entscheidet eine Liste, und alles andere folgt -
    auch die Zaehlung "Folie 1 von 2" in der Beschriftung fuer Screenreader.
    """
    n = len(C.HERO_SLIDES)
    aus = []
    for k, name in enumerate(C.HERO_SLIDES):
        srcset, src, w, h = R._hero(name)
        hell = " light" if name != "hero" else ""
        aktiv = " active" if k == 0 else ""
        # Die erste Folie ist das LCP-Element und wird vorgeladen; jede weitere
        # holt der Browser mit niedriger Prioritaet, aber sie muss geholt
        # werden: unter visibility:hidden wuerde loading="lazy" gar nichts tun.
        prio = ('fetchpriority="high"' if k == 0
                else 'loading="eager" fetchpriority="low"')
        # Der Alt-Text stand in allen drei Sprachfassungen auf Deutsch. Er ist
        # das, was ein Screenreader vorliest und was in der Bildersuche zaehlt.
        alt_txt = C.t(lang, "hero_alt" if name == "hero" else "hero2_alt",
                      marke=C.BRAND, site=C.t(lang, "site_name"))
        txt = ""
        if name == "hero":
            txt = (f'<div class="hero-txt hero-mobile-copy">'
                   f'<span class="hk">{e(C.t(lang,"hero_weld_kicker"))}</span>'
                   f'<h2>{e(C.t(lang,"hero_weld_title"))}</h2>'
                   f'<p>{e(C.t(lang,"hero_weld_sub"))}</p>'
                   f'<a class="btn pri" href="{e(C.u_prod(lang, C.BY_ID["hypermig-x"]))}">'
                   f'{e(C.t(lang,"hero_weld_cta"))}</a></div>')
        elif name == "hero-mpt":
            txt = (f'<div class="hero-txt">'
                   f'<span class="hk">{e(C.t(lang,"hero2_kicker"))}</span>'
                   f'<h2>{e(C.t(lang,"hero2_title"))}</h2>'
                   f'<p>{e(C.t(lang,"hero2_sub"))}</p>'
                   f'<a class="btn pri" href="{e(C.u_prod(lang, C.BY_ID["mpt-3001"]))}">'
                   f'{e(C.t(lang,"hero2_cta"))}</a></div>')
        aus.append(
            f'<div class="hero-slide{hell}{aktiv}" role="group" '
            f'aria-roledescription="slide" '
            f'aria-label="{e(C.t(lang, "hero_slide", n=k+1, m=n))}">'
            f'<div class="hero-inner">'
            f'<img class="hero-photo" src="{src}" srcset="{srcset}" sizes="100vw" '
            f'width="{w}" height="{h}" {prio} decoding="async" '
            f'alt="{e(alt_txt)}" data-fb="/assets/img/{name}.jpg">'
            f'{txt}</div></div>')
    return "".join(aus)


def hero_band(lang):
    """Das Band. Bei nur einer Folie ohne Punkte und ohne data-hero - das
    Skript steigt bei weniger als zwei Folien ohnehin aus, aber ohne die
    Auszeichnung als Karussell liest ein Screenreader es gar nicht erst als
    solches vor."""
    n = len(C.HERO_SLIDES)
    if n < 2:
        return (f'<section class="hero">{hero_folien(lang)}</section>')
    punkte = "".join(
        f'<button class="hdot{" active" if k == 0 else ""}" type="button" '
        f'aria-pressed="{"true" if k == 0 else "false"}" data-i="{k}" '
        f'aria-label="{e(C.t(lang, "hero_slide", n=k+1, m=n))}"></button>'
        for k in range(n))
    return (f'<section class="hero" data-hero aria-roledescription="carousel" '
            f'aria-label="{e(C.t(lang,"site_name"))}">'
            f'{hero_folien(lang)}'
            f'<div class="hero-dots" role="group" '
            f'aria-label="{e(C.t(lang,"gal_label"))}">{punkte}</div>'
            # WCAG 2.2.2: Inhalt, der sich von selbst bewegt und laenger als
            # fuenf Sekunden laeuft, braucht eine Moeglichkeit zum Anhalten.
            # Die Punkte schalten nur um, sie halten nicht an.
            f'<button class="hpause" type="button" data-hpause '
            f'aria-label="{e(C.t(lang,"slide_pause"))}">'
            f'<span aria-hidden="true">❙❙</span></button>'
            f'</section>')


def kachel_zusatz(lang, c):
    """Occasion-Modellreihen aus dem Katalog, keine aktuelle Lagerzusage.

    Eine Modellreihe kann Einzelgeraete verschiedener Hersteller umfassen.
    Deshalb hier keine pauschale Marke aus dem Katalogeintrag voranstellen.
    """
    if c["id"] != "occasion":
        return ""
    namen = [C.pName(lang, p) for p in C.P if p["cat"] == "occasion"]
    if not namen:
        return ""
    return " " + e(C.t(lang, "occ_aktuell", liste=", ".join(namen)))


def home_featured(lang):
    """Catalogue highlights with localized product links and no image footnotes."""
    slides, dots = [], []
    for i, pid in enumerate(C.HOME_FEATURED):
        product = C.BY_ID[pid]
        wide = pid == 'mpt-3001'
        details = [C.vtT(lang, product['vt'])]
        detail = product['specs'].get('Arbeitsbereich' if wide else 'Netz')
        if detail:
            details.append(C.trV(lang, detail))
        picture = R.img_tag(product['img'],
                            # object-fit:contain caps the 280px-high picture at
                            # 498px of visible width; its full grid cell is wider.
                            '(max-width:640px) min(calc(100vw - 88px), 356px), '
                            '(max-width:1150px) min(calc(50vw - 72px), 462px), 498px' if wide else
                            '(max-width:640px) 45vw, (max-width:1150px) 320px, 350px',
                            alt=C.pFullName(lang, product), width=620 if wide else 440,
                            eager=i == 0, low_priority=i > 0)
        slides.append(
            f'<div class="hero-slide volt-feature-slide{ " volt-feature-wide" if wide else ""}{" active" if i == 0 else ""}" '
            f'role="group" aria-roledescription="slide" '
            f'aria-label="{e(C.t(lang,"hero_slide",n=i+1,m=len(C.HOME_FEATURED)))}" '
            f'data-product="{e(pid)}" data-slide-title="{e(C.pName(lang,product))}">'
            f'<a class="volt-home-product" href="{e(C.u_prod(lang,product))}">'
            f'<figure class="volt-product-plinth">{picture}</figure>'
            f'<div class="volt-home-product-label"><h2>{e(C.pName(lang,product))}</h2>'
            f'<p class="volt-feature-facts">{e(" · ".join(details))}</p><p>{e(C.t(lang,"poa"))}</p>'
            f'<span class="volt-text-link">{e(C.t(lang,"volt_device_view"))} '
            '<span aria-hidden="true">→</span></span></div></a></div>')
        dots.append(f'<button class="hdot{" active" if i == 0 else ""}" type="button" data-i="{i}" '
                    f'aria-pressed="{"true" if i == 0 else "false"}" '
                    f'aria-label="{e(C.pFullName(lang,product))}"></button>')
    return (f'<div class="volt-feature-carousel" data-hero="products" data-interval="3000" '
            f'role="region" aria-roledescription="carousel" aria-label="{e(C.t(lang,"volt_featured_label"))}">'
            f'<div class="volt-feature-stage">{"".join(slides)}</div>'
            '<div class="volt-feature-controls"><div class="volt-feature-actions">'
            f'<button type="button" class="volt-feature-button" data-hero-step="-1" aria-label="{e(C.t(lang,"volt_feature_prev"))}"><span aria-hidden="true">‹</span></button>'
            f'<button type="button" class="volt-feature-button" data-hpause aria-label="{e(C.t(lang,"slide_pause"))}"><span aria-hidden="true">❙❙</span></button>'
            f'<button type="button" class="volt-feature-button" data-hero-step="1" aria-label="{e(C.t(lang,"volt_feature_next"))}"><span aria-hidden="true">›</span></button></div>'
            f'<div class="volt-feature-dots">{"".join(dots)}</div></div>'
            '<span class="sr-only" data-hero-status role="status" aria-live="polite"></span></div>')


def page_home(lang):
    url, alts = C.u_home(lang), C.alternates("home")
    applications = ''.join(
        f'<a class="volt-application" href="{e(C.editorial_target(lang, item["target"])[1])}">'
        f'<span class="volt-application-number" aria-hidden="true">{i:02d}</span>'
        f'<h3>{e(item[lang]["title"])}</h3><p>{e(item[lang]["description"])}</p>'
        '<span class="volt-application-arrow" aria-hidden="true">→</span></a>'
        for i, item in enumerate(C.HOME_APPLICATIONS, 1))
    cards = ""
    for i, c in enumerate(C.CATS, 1):
        n = len(C.products_of(c["id"]))
        cards += (
            f'<a class="cat" href="{e(C.u_cat(lang, c["id"]))}">'
            f'<div class="idx">{i:02d} · {n} {e(C.t(lang,"devices",n=n))}</div>'
            f'<div class="pk" aria-hidden="true">{C.PK[c["pk"]]}</div>'
            f'<h3>{e(C.catT(lang, c))}</h3><p>{e(C.catD(lang, c))}{kachel_zusatz(lang, c)}</p>'
            f'<div class="go">{e(C.t(lang,"card_open"))}</div></a>'
        )
    faq6 = C.EX[lang]["faq"][:6]
    spotlights = ''
    for pid in ('theta-60', 'hypercleaner-st'):
        product = C.BY_ID[pid]
        spotlights += (f'<a class="volt-spotlight" href="{e(C.u_prod(lang, product))}">'
                       + R.img_tag(product['img'], '(max-width:700px) 45vw, 300px',
                                   alt=C.pFullName(lang, product), width=300)
                       + f'<div><h2>{e(C.pName(lang, product))}</h2>'
                       f'<p>{e(C.t(lang,"poa"))}</p><span class="volt-text-link">'
                       f'{e(C.t(lang,"volt_device_view"))} <span aria-hidden="true">→</span></span></div></a>')
    body = f"""
<section class="volt-home-hero"><div class="wrap volt-home-grid">
  <div class="volt-home-copy">
    <p class="p-eyebrow">{e(C.t(lang,'site_name'))} · MAHE</p>
    <h1><span>{e(C.t(lang,'volt_headline_1'))}</span> <span>{e(C.t(lang,'volt_headline_2'))}</span></h1>
    <p class="volt-disciplines">{e(C.t(lang,'volt_disciplines'))}</p>
    <p class="volt-home-support">{e(C.t(lang,'cro_hero_support'))}</p>
    <div class="cta-row"><a class="btn pri" href="{e(C.u_products(lang))}">{e(C.t(lang,'hero_cta2'))} <span aria-hidden="true">→</span></a>
      <a class="btn ghost" href="{e(C.u_page(lang,'contact'))}">{e(C.t(lang,'hero_cta1'))}</a></div>
  </div>
  {home_featured(lang)}
</div></section>
<div class="wrap"><a class="volt-service-link" href="{e(C.u_service(lang))}">{R.design_icon('repair')}<span>{e(C.t(lang,'volt_service_title'))}</span><span aria-hidden="true">→</span></a></div>
<section class="volt-applications"><div class="wrap">
  <h2>{e(C.t(lang,'applications_title'))}</h2>
  <p class="sub">{e(C.t(lang,'applications_intro'))}</p>
  <div class="volt-application-grid">{applications}</div>
</div></section>
<div class="wrap volt-spotlights">{spotlights}</div>

<section class="intro"><div class="wrap">
  <h2>{e(C.t(lang,'home_h1'))}</h2>
  <p class="lead">{e(C.t(lang,'hero_lead'))}</p>
</div></section>

{R.usp_row(lang, service_links=True)}
{R.ref_block(lang)}
{training_block(lang)}

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
    ld = R.ld_reviews(lang) + [R.ld_org(lang), R.ld_website(lang),
          R.ld_webpage(lang, url, C.t(lang, "home_title"), C.t(lang, "home_desc"),
                       {"@type": ["WebPage", "CollectionPage"]}),
          R.ld_faq_subset(lang, faq6, url)]
    return url, R.document(
        lang, title=C.t(lang, "home_title"), desc=C.t(lang, "home_desc"),
        url=url, alts=alts, jsonld_blocks=ld, body=body)


def page_products(lang):
    url, alts = C.u_products(lang), C.alternates("products")
    n = len(C.P)
    title = C.t(lang, "all_title")
    desc = clip(C.t(lang, "all_desc", n=n), 155)
    chips = '<div class="chips">' + "".join(
        f'<a class="chip" href="{e(C.u_cat(lang, c["id"]))}">{e(C.catT(lang, c))}</a>'
        for c in C.CATS) + "</div>"
    body = (
        R.cbar(lang, crumb_items=[(C.t(lang, "nav_home"), C.u_home(lang)),
                                  (C.t(lang, "nav_products"), None)],
               h1=C.t(lang, "all_h1"), desc=C.t(lang, "all_lead"), chips=chips)
        + '<div class="catalog"><div class="wrap">'
        + f'<div class="cathead"><h2>{e(C.t(lang,"sec_all"))}</h2>'
          f'<span class="count">{n} {e(C.t(lang,"items",n=n))} · {e(C.t(lang,"poa"))}</span></div>'
        + R.pgrid(lang, C.P) + "</div></div>"
    )
    ld = [R.ld_org(lang),
          R.ld_webpage(lang, url, title, desc, {"@type": "CollectionPage"}),
          R.ld_breadcrumb([(C.t(lang, "nav_home"), C.u_home(lang)),
                           (C.t(lang, "nav_products"), url)]),
          R.ld_itemlist(lang, C.P, C.t(lang, "all_h1"))]
    return url, R.document(lang, title=title, desc=desc, url=url, alts=alts,
                           jsonld_blocks=ld, body=body)


def editorial_links(lang, refs, current=None):
    targets = [C.editorial_target(lang, ref) for ref in refs]
    items = ''.join(f'<li><a href="{e(url)}">{e(label)}</a></li>'
                    for label, url in targets if url != current)
    return (f'<nav class="guide-links" aria-label="{e(C.t(lang, "guide_links_label"))}">'
            f'<ul>{items}</ul></nav>') if items else ''


def product_guide(lang, p):
    guide = C.PRODUCT_GUIDES.get(p['id'])
    if not guide:
        return ''
    copy = guide[lang]
    checks = ''.join(f'<li>{e(text)}</li>' for text in copy['checks'])
    return (f'<section class="buying-guide product-guide" data-selection-guide="{e(p["id"])}">'
            f'<h2>{e(C.t(lang, "product_guide_title", name=C.pName(lang, p) if C.istMahe(p) else C.pFullName(lang, p)))}</h2>'
            f'<p>{e(copy["intro"])}</p><ul class="selection-checks">{checks}</ul>'
            + editorial_links(lang, guide['links'], C.u_prod(lang, p)) + '</section>')


def company_navigation(lang, current):
    return (f'<section class="company-navigation"><h2>{e(C.t(lang, "company_links_title"))}</h2>'
            + editorial_links(lang, C.GUIDE_LINKS['company'], current) + '</section>')


def buying_guide(lang, cid):
    guide = C.BUYING_GUIDE[cid][lang]
    criteria = ''.join(f'<dt>{e(title)}</dt><dd>{e(text)}</dd>' for title, text in guide['criteria'])
    return (f'<section class="buying-guide"><h2>{e(guide["title"])}</h2>'
            f'<p>{e(guide["intro"])}</p><dl>{criteria}</dl>'
            + editorial_links(lang, C.GUIDE_LINKS['categories'][cid])
            + f'<a class="btn ghost" href="{e(C.u_page(lang, "contact"))}">{e(C.t(lang, "consult"))}</a></section>')


def category_comparison(lang, cid, sub):
    row = next((item for item in C.CATEGORY_COMPARISONS if (item['cat'], item['sub']) == (cid, sub)), None)
    if not row:
        return ''
    copy, ident = row['copy'][lang], 'compare-' + row['id']
    head = ''.join(f'<th scope="col">{e(C.trK(lang, key))}</th>' for key in row['fields'])
    body = ''
    for pid in row['products']:
        product = C.BY_ID[pid]
        cells = ''.join(f'<td>{e(C.trV(lang, product["specs"][key]))}</td>' for key in row['fields'])
        body += (f'<tr><th scope="row"><a href="{e(C.u_prod(lang, product))}">'
                 f'{e(C.pFullName(lang, product))}</a></th>{cells}</tr>')
    return (f'<div class="catalog-comparison"><h3 id="{e(ident)}">{e(copy["title"])}</h3>'
            f'<p>{e(copy["note"])}</p><div class="spectab-scroll" tabindex="0" role="region" '
            f'aria-labelledby="{e(ident)}"><table class="spectab">'
            f'<caption class="sr-only">{e(copy["title"])}</caption><thead><tr>'
            f'<th scope="col">{e(C.t(lang,"spec_model"))}</th>{head}</tr></thead>'
            f'<tbody>{body}</tbody></table></div></div>')


def subcategory_guide(lang, cid, sub):
    guide = C.SUBCATEGORY_GUIDES[cid][sub][lang]
    criteria = ''.join(f'<dt>{e(title)}</dt><dd>{e(text)}</dd>'
                       for title, text in guide['criteria'])
    return (f'<section class="buying-guide"><h2>{e(C.t(lang, "subcategory_guide_title"))}</h2>'
            f'<dl>{criteria}</dl>' + category_comparison(lang, cid, sub)
            + editorial_links(lang, C.GUIDE_LINKS['subcategories'][cid][sub])
            + f'<a class="btn ghost" href="{e(category_contact_url(lang, cid, sub))}">{e(C.t(lang, "consult"))}</a></section>')


def category_contact_url(lang, cid, sub=None):
    topic = C.category_topic(cid, sub)
    return C.u_page(lang, 'contact') + ('?topic=' + topic if topic else '')


def category_consultation(lang, cid, sub=None):
    topic = C.category_topic(cid, sub)
    if not topic:
        return ''
    copy = C.INQUIRY_TOPICS[topic]['copy'][lang]
    return (f'<section class="selection-contact" aria-labelledby="selectionHeading">'
            f'<div><h2 id="selectionHeading">{e(copy["heading"])}</h2>'
            f'<p>{e(copy["hint"])}</p></div><a class="btn ghost" '
            f'href="{e(category_contact_url(lang,cid,sub))}">{e(C.t(lang,"cro_selection_cta"))}'
            ' <span aria-hidden="true">→</span></a></section>')


def page_cat(lang, c, sub=None):
    cid = c["id"]
    if sub:
        url = C.u_sub(lang, cid, sub)
        alts = C.alternates("sub", cat_id=cid, sub=sub)
        items = C.products_of(cid, sub)
        marke = C.catBrand(cid)
        h1 = f"{C.subT(lang, sub)} · {marke}" if marke else C.subT(lang, sub)
        # Die MAHE-Vorlagen tragen den Markennamen im Titel. Fuer eine
        # Kategorie mit Fremdfabrikaten gibt es eigene - sonst stuende ueber
        # den gebrauchten Oerlikon-Anlagen "MAHE Mikroplasma kaufen".
        occ = cid == "occasion"
        title = C.t(lang, "sub_title_occ" if occ else "sub_title_tpl",
                    sub=C.subT(lang, sub), cat=C.catT(lang, c), n=len(items))
        desc = clip(C.t(lang, "sub_desc_occ" if occ else "sub_desc_tpl",
                        sub=C.subT(lang, sub), n=len(items)), 155)
        lead = C.SUBCATEGORY_GUIDES[cid][sub][lang]['intro']
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
        # Wie bei den Produkten: von der ausfuehrlichsten Variante abwaerts,
        # bis der Titel unter 68 Zeichen bleibt. Ohne diese Stufe war
        # "Apparecchi di pulizia · acquistare MAHE Pulizia in Svizzera |
        # VES-TECH" 70 Zeichen lang - Google haette hinten abgeschnitten. Die
        # kurze Fassung laesst den Hinweis auf die erste Unterkategorie weg;
        # er steht ohnehin als Chip auf der Seite.
        occ = cid == "occasion"
        if occ:
            title = C.t(lang, "cat_title_occ", cat=C.catT(lang, c))
            desc = clip(C.t(lang, "cat_desc_occ", cat=C.catT(lang, c),
                            n=len(items), subs=subs_txt), 155)
        else:
            title = C.t(lang, "cat_title_tpl", cat=C.catT(lang, c),
                        sub_hint=C.subT(lang, c["subs"][0]))
            if len(title) > 68:
                title = C.t(lang, "cat_title_tpl_kurz", cat=C.catT(lang, c))
            desc = clip(C.t(lang, "cat_desc_tpl", cat=C.catT(lang, c),
                            n=len(items), subs=subs_txt), 155)
        lead = C.catD(lang, c)
        crumb = [(C.t(lang, "nav_home"), C.u_home(lang)),
                 (C.t(lang, "nav_products"), C.u_products(lang)),
                 (C.catT(lang, c), None)]

    search_copy = C.search_landing(lang, cid, sub)
    if search_copy:
        title, desc, h1 = (search_copy[key] for key in ('title', 'description', 'h1'))

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
        + category_consultation(lang, cid, sub)
        + f'<div class="cathead"><h2>{e(C.subT(lang, sub) if sub else C.t(lang,"sec_all"))}</h2>'
          f'<span class="count">{len(items)} {e(C.t(lang,"items",n=len(items)))} · {e(C.t(lang,"poa"))}</span></div>'
        + R.pgrid(lang, items)
        + (subcategory_guide(lang, cid, sub) if sub else buying_guide(lang, cid)) + "</div></div>"
    )
    # Die Vorschau muss zur gefilterten Kategorie passen: das allgemeine
    # HyperMIG-Herobild ist z. B. fuer Plasma oder Reinigung irrefuehrend.
    # Die bestehende Katalogreihenfolge macht die Auswahl sprachunabhaengig.
    preview = next((R.img_abs(p["img"], 1000) for p in items if p.get("img")), None)
    page_type = {"@type": "CollectionPage"}
    if preview:
        page_type["primaryImageOfPage"] = {"@type": "ImageObject", "url": preview}
    ld = [R.ld_org(lang),
          R.ld_webpage(lang, url, title, desc, page_type),
          R.ld_breadcrumb(crumb[:-1] + [(crumb[-1][0], url)]),
          R.ld_itemlist(lang, items, h1)]
    return url, R.document(lang, title=title, desc=desc, url=url, alts=alts,
                           jsonld_blocks=ld, body=body, og_image=preview)


def panel_spotlight(lang, p):
    """Visible preview of the confirmed X panel; complete guide stays in its tab."""
    if 'hypermig_x_graphic' not in C.fpAssign(p):
        return ''
    panel = C.FP['hypermig_x_graphic']
    features = ''.join(
        f'<div>{R.design_icon(icon)}<div><h3>{e(title)}</h3><p>{e(text)}</p></div></div>'
        for icon, (title, text) in zip(('screen', 'control', 'job'), C.t(lang, 'volt_panel_features')))
    return (f'<section class="volt-panel-feature" aria-labelledby="volt-panel-title">'
            f'<div class="volt-panel-copy"><h2 id="volt-panel-title">{e(C.t(lang,"volt_panel_title"))}</h2>'
            f'<p>{e(C.t(lang,"volt_panel_intro"))}</p>'
            f'<a class="volt-text-link" href="#panel-hypermig-x-graphic">{e(C.t(lang,"volt_panel_more"))} <span aria-hidden="true">→</span></a></div>'
            '<div class="volt-panel-image">'
            + R.img_tag(panel['img'], '(max-width:700px) 85vw, 450px',
                        cls='zoomable', alt=C.fpName(lang, panel), width=450)
            + f'</div><div class="volt-panel-benefits">{features}</div></section>')


def page_product(lang, p):
    url = C.u_prod(lang, p)
    alts = C.alternates("prod", p=p)
    c = C.CAT_BY_ID[p["cat"]]
    # Reviewed names and complete snippets; no generic category chain or
    # clipping halfway through a technical statement. Model names stay intact.
    nm = C.pName(lang, p)
    search_copy = C.PRODUCT_SEO[p['id']][lang]
    title, desc = search_copy['title'], search_copy['description']
    crumb = [(C.t(lang, "nav_home"), C.u_home(lang)),
             (C.t(lang, "nav_products"), C.u_products(lang)),
             (C.catT(lang, c), C.u_cat(lang, p["cat"])),
             (C.subT(lang, p["sub"]), C.u_sub(lang, p["cat"], p["sub"])),
             (nm, None)]

    # Gebrauchtmaschinen bekommen einen eigenen Einleitungssatz. Der normale
    # verspricht die Abwicklung der Garantie - die gibt es bei einer
    # gebrauchten Anlage nicht, und ein Versprechen, das niemand einloesen
    # kann, waere eine Taeuschung ueber die Beschaffenheit.
    intro_key = "prod_intro_occ_tpl" if p["cat"] == "occasion" else "prod_intro_tpl"
    if p.get("models"):
        intro_key = "prod_intro_occ_models"
    # Was an einer Gebrauchtmaschine gemacht wurde, ist die wichtigste Angabe
    # auf der Seite - wichtiger als jede technische Zeile. Sie steht deshalb
    # nicht im Fliesstext, sondern als eigener Block direkt unter der
    # Einleitung, und zusaetzlich als condition im oeffentlichen Produktkatalog.
    zt = C.zustandText(lang, p)
    zustand_block = (
        f'<p class="zustand"><b>{e(C.t(lang, "zustand_h"))}</b> {e(zt)}</p>'
        if zt else "")
    has_panel = bool(C.fpAssign(p))
    tab1 = C.t(lang, "tab_feat") if has_panel else C.t(lang, "highlights")
    tabs = [("feat", tab1), ("tech", C.t(lang, "tab_tech"))]
    if C.optionsOf(lang, p):
        tabs.append(("opt", C.t(lang, "tab_opt")))
    # Der Reiter heisst nach dem, was er zeigt: beim Geraet das Zubehoer,
    # beim Zubehoerteil die Geraete, an die es gehoert.
    acc_titel = (C.t(lang, "tab_acc") if C.relatedAcc(p)
                 else C.t(lang, "tab_fits") if C.geraeteZu(p)
                 else C.t(lang, "tab_acc"))
    tabs += [("acc", acc_titel), ("dl", C.t(lang, "tab_dl"))]
    panes = {
        "feat": front_html(lang, p),
        "tech": spec_html(lang, p),
        "opt": opt_html(lang, p),
        "acc": acc_html(lang, p),
        "dl": dl_html(lang, p),
    }
    # Reiter ohne Inhalt gar nicht erst anlegen.
    #
    # Am 14.08.2026 nachgezaehlt: auf 48 der 77 Produktseiten war die
    # Fronteingabe leer - der Hersteller veroeffentlicht zu diesen Geraeten
    # keine Besonderheiten. Der Reiter stand trotzdem da, war der zuerst
    # geoeffnete, und wer die Seite aufrief, sah als Erstes eine leere Flaeche.
    # Fuer eine Suchmaschine war der erste Inhaltsblock jeder zweiten
    # Produktseite leer und auf allen gleich - das half beim Eindruck, diese
    # Seiten seien untereinander austauschbar, nicht.
    tabs = [(k, n) for k, n in tabs if (panes.get(k) or "").strip()]
    tabbar = "".join(
        f'<button class="tabbtn{" active" if i == 0 else ""}" type="button" role="tab" '
        f'id="tb-{k}" aria-controls="tab-{k}" aria-selected="{"true" if i == 0 else "false"}" '
        f'tabindex="{0 if i == 0 else -1}" data-tab="{k}">{e(n)}</button>' for i, (k, n) in enumerate(tabs))
    panehtml = "".join(
        f'<section class="tabpane{" active" if i == 0 else ""}" id="tab-{k}" role="tabpanel" '
        f'aria-labelledby="tb-{k}"><h2 class="sr-only">{e(n)}</h2>{panes[k]}</section>'
        for i, (k, n) in enumerate(tabs))

    # Bei MAHE steht die Marke im Kicker, die Ueberschrift ist der Gerätename;
    # so ist der ganze Katalog gebaut. Eine Fremdmarke traegt sie in der h1,
    # denn "PlasmaFix 51" allein sagt nicht, wessen Anlage das ist, und
    # gesucht wird "oerlikon plasmafix 51" und nie das Wort allein.
    h1 = nm if C.istMahe(p) else C.pFullName(lang, p)
    context = accessory_context_html(lang, p)
    context = f"\n      {context}" if context else ""
    selection = product_guide(lang, p)
    selection = f"\n  {selection}" if selection else ""
    facts = quickfacts_html(lang, p) if panes['tech'].strip() else ''
    body = f"""
<div class="detail"><div class="wrap">
  {R.crumbs(lang, crumb)}
  <div class="dgrid">
    <div class="volt-product-media">{media_html(lang, p, nm)}</div>
    <div class="dinfo" data-inquiry-product="{e(p['id'])}">
      <p class="kicker">{e(search_copy['type'] if C.istMahe(p) else C.catT(lang, c))} · {e(C.pBrand(p))}</p>
      <h1>{e(h1)}</h1>
      <p class="lead">{e(C.pDesc(lang, p))}</p>{context}
      <div class="pmeta">
        <div class="m"><span class="lab">{e(C.t(lang,'availability'))}</span>
          <span class="val ok">{R.inquiry_availability(lang, p)}</span></div>
        <div class="m"><span class="lab">{e(C.t(lang,'brand'))}</span>
          <span class="val">{e(C.pBrand(p))}</span></div>
        <div class="m"><span class="lab">{e(C.t(lang,'artno'))}</span>
          <span class="val">{e(p['id'].upper())}</span></div>
      </div>
      {facts}
      <div class="poa-box"><span class="p">{e(C.t(lang,'poa'))}</span>
        <span class="s">{e(C.t(lang, 'poa_sub_occ' if p["cat"] == "occasion" else 'poa_sub'))}</span></div>
{R.inquiry_product_choices(lang, p)}
      <div class="dactions">
        <button class="btn pri" type="button" data-add="{e(p['id'])}" data-name="{e(nm)}"
                data-url="{e(url)}" data-img="{e(R.thumb(p))}">{e(C.t(lang,'to_inquiry'))}</button>
        <a class="btn ghost" data-product-consult="{e(p['id'])}" href="{e(C.u_page(lang,'contact'))}?product={e(p['id'])}">{e(C.t(lang,'consult'))}</a>
      </div>
      <nav class="product-quick-contact" aria-label="{e(C.t(lang,'cro_mobile_label'))}">
        <span>{e(nm)}</span>
        <a class="btn pri" data-product-consult="{e(p['id'])}" href="{e(C.u_page(lang,'contact'))}?product={e(p['id'])}">{e(C.t(lang,'cro_offer'))}</a>
        <a class="btn ghost" href="tel:{e(C.COMPANY['phone_href'])}">{e(C.t(lang,'cro_call'))}</a>
      </nav>
      {procs_block(lang, p)}
      <p class="prod-intro">{e(C.t(lang, intro_key, name=nm, marke=C.pBrand(p),
                                       de_marke=C.markeMitPraeposition(lang, p)))}</p>
{zustand_block}
    </div>
  </div>
{panel_spotlight(lang, p)}
{R.inquiry_unit_cards(lang, p)}
  <div class="tabs">
    <div class="tabbar" role="tablist" aria-label="{e(nm)}">{tabbar}</div>
    {panehtml}
  </div>{selection}
{occ_text_html(lang, p)}
{verwandt_html(lang, p)}

  <p class="backlink"><a href="{e(C.u_cat(lang, p['cat']))}">← {e(C.t(lang,'back_to_cat'))}</a></p>
</div></div>
"""
    # primaryImageOfPage war auf jeder Produktseite das Titelbild der
    # Startseite - die Vorlage fuer alle WebPage-Knoten kennt nur dieses.
    # Auf einer Produktseite ist das Hauptbild das Produktfoto.
    ld = [R.ld_org(lang), R.ld_catalog_item(lang, p),
          R.ld_webpage(lang, url, title, desc, {
              "@type": "ItemPage",
              "mainEntity": {"@id": C.abs_url(url) + "#product"},
              "primaryImageOfPage": {"@type": "ImageObject",
                                     "url": R.img_abs(p["img"], 1000)}}),
          R.ld_breadcrumb(crumb[:-1] + [(nm, url)])]
    ot = C.occText(lang, p)
    if ot and ot.get("faq"):
        ld.append(R.ld_faq_subset(lang, ot["faq"], url))
    return url, R.document(lang, title=title, desc=desc, url=url, alts=alts,
                           jsonld_blocks=ld, body=body, og_type="product",
                           og_image=R.product_social_image(lang, p))


def process_followup(lang):
    """Context after the MAHE procedures; Oerlikon stays a separate topic."""
    def label(key):
        text = C.t(lang, key)
        return text if lang == 'de' else text.lower()

    links = {
        'automation': (C.u_service(lang, 'auto'), label('foot_auto')),
        'calibration': (C.u_service(lang, 'calib'), label('foot_calib')),
        'microplasma': (C.u_sub(lang, 'occasion', 'Mikroplasma'),
                       C.subT(lang, 'Mikroplasma') if lang == 'de'
                       else C.subT(lang, 'Mikroplasma').lower()),
    }
    replacements = {key: f'<a href="{e(url)}">{e(text)}</a>'
                    for key, (url, text) in links.items()}
    # Escape every literal text fragment; only these fixed links add markup.
    service = e(C.t(lang, 'process_followup_service')).format_map(replacements)
    micro = e(C.t(lang, 'process_followup_micro')).format_map(replacements)
    return (f'<section class="buying-guide"><h2>{e(C.t(lang, "process_followup_title"))}</h2>'
            f'<p>{service}</p><p>{micro}</p></section>')


def process_overview(lang):
    """All 19 entries remain visible, linked to their full technical explanations."""
    groups = ''
    for group in C.PROCESS_GUIDE['groups']:
        cards = ''
        for process in C.PROC:
            if process['group'] != group['id']:
                continue
            symbol_key = 'coldrootforce' if process['id'] in ('hyperforce', 'hypercold', 'hyperroot') else process['ic']
            feature = C.FEAT.get(symbol_key) if symbol_key else None
            symbol = (f'<img src="{e(feature["img"])}" width="{feature["w"]}" height="{feature["h"]}" '
                      f'alt="{e(C.featLabel(lang,symbol_key))}" loading="lazy" decoding="async">') if feature else ''
            cards += (f'<article class="volt-process-card{ " volt-process-no-symbol" if not feature else ""}"><div class="volt-process-symbol">{symbol}</div><div>'
                      f'<h3>{e(process["n"][lang].split(" · ")[0])}</h3><p>{e(process["d"][lang])}</p>'
                      f'<a class="volt-text-link" href="#{e(process["id"])}">{e(C.t(lang,"volt_process_detail"))} '
                      '<span aria-hidden="true">→</span></a></div></article>')
        groups += (f'<section class="volt-process-group" id="overview-{e(group["id"])}" '
                   f'aria-labelledby="overview-title-{e(group["id"])}">'
                   f'<h2 id="overview-title-{e(group["id"])}">{e(group["n"][lang].split(" · ")[0])}</h2>'
                   f'<div class="volt-process-grid">{cards}</div></section>')
    links = ''.join(f'<a class="chip" href="#overview-{e(g["id"])}">{e(g["n"][lang].split(" · ")[0])}</a>'
                    for g in C.PROCESS_GUIDE['groups'])
    return (f'<div class="wrap volt-process-overview"><nav class="chips" aria-label="{e(C.t(lang,"volt_process_overview"))}">'
            f'{links}</nav>{groups}</div>')


def page_processes(lang):
    url, alts = C.u_page(lang, "processes"), C.alternates("page", key="processes")
    guide = C.PROCESS_GUIDE[lang]
    groups = C.PROCESS_GUIDE['groups']
    jump = '<a href="#vergleich">' + e(guide['compare_title']) + '</a>'
    jump += ''.join(f'<a href="#{e(g["anchor"])}">{e(g["n"][lang].split(" · ")[0])}</a>' for g in groups)
    jump += '<a href="#parameter">' + e(guide['glossary_title']) + '</a>'
    rows = ''.join(
        f'<tr><th scope="row"><a href="#{e(r["target"])}">{e(r["n"])}</a></th>'
        f'<td>{e(r["principle"])}</td><td>{e(r["focus"])}</td></tr>' for r in guide['comparison'])
    compare = (f'<section id="vergleich" class="process-section"><h2 id="vergleich-title">{e(guide["compare_title"])}</h2>'
               f'<p class="process-table-hint">{e(guide["table_hint"])}</p>'
               f'<div class="process-table" role="region" aria-labelledby="vergleich-title" tabindex="0">'
               f'<table><caption>{e(guide["compare_caption"])}</caption><thead><tr>'
               f'<th scope="col">{e(guide["compare_mode"])}</th>'
               f'<th scope="col">{e(guide["compare_principle"])}</th>'
               f'<th scope="col">{e(guide["compare_focus"])}</th></tr></thead><tbody>{rows}</tbody></table></div></section>')
    toc = ''
    for group in groups:
        links = ''.join(f'<li><a href="#{e(p["id"])}">{e(p["n"][lang])}</a></li>'
                        for p in C.PROC if p['group'] == group['id'])
        toc += f'<div><h3>{e(group["n"][lang].split(" · ")[0])}</h3><ul>{links}</ul></div>'
    toc = (f'<nav id="inhalt" class="process-toc" aria-labelledby="process-toc-title">'
           f'<h2 id="process-toc-title">{e(guide["jump_label"])}</h2><div class="process-toc-cols">{toc}</div></nav>')
    sections = ''
    for group in groups:
        articles = ''
        for index, process in enumerate(C.PROC, 1):
            if process['group'] != group['id']:
                continue
            feature = C.FEAT.get(process['ic']) if process['ic'] else None
            symbol = (f'<img class="process-symbol" src="{e(feature["img"])}" width="{feature["w"]}" '
                      f'height="{feature["h"]}" alt="{e(C.featLabel(lang, process["ic"]))}" loading="lazy" decoding="async">') if feature else ''
            products = ''.join(f'<li><a href="{e(C.u_prod(lang, C.BY_ID[pid]))}">{e(C.pFullName(lang, C.BY_ID[pid]))}</a></li>' for pid in process['products'])
            articles += (f'<article id="{e(process["id"])}" class="process-article" aria-labelledby="title-{e(process["id"])}">'
                         f'<div class="process-article-head"><span class="process-number" aria-hidden="true">{index:02d}</span>'
                         f'<h3 id="title-{e(process["id"])}">{e(process["n"][lang])}</h3>{symbol}</div>'
                         f'<div class="process-copy"><p class="process-summary">{e(process["d"][lang])}</p>'
                         f'<div class="process-principle"><h4>{e(guide["principle_label"])}</h4><p>{e(process["principle"][lang])}</p></div>'
                         f'<div><h4>{e(guide["use_label"])}</h4><p>{e(process["use"][lang])}</p></div>'
                         f'<div><h4>{e(guide["setup_label"])}</h4><p>{e(process["setup"][lang])}</p></div>'
                         f'<div class="process-products"><span>{e(guide["products_label"])}</span><ul>{products}</ul></div></div></article>')
        sections += (f'<section id="{e(group["anchor"])}" class="process-section"><div class="process-section-head">'
                     f'<h2>{e(group["n"][lang])}</h2><p>{e(group["d"][lang])}</p></div>{articles}'
                     f'<a class="process-back" href="#inhalt">↑ {e(guide["back_top"])}</a></section>')
    glossary = ''.join(f'<div><dt>{e(item["n"])}</dt><dd>{e(item["d"])}</dd></div>' for item in guide['glossary'])
    glossary = f'<section id="parameter" class="process-section"><h2>{e(guide["glossary_title"])}</h2><dl class="process-glossary">{glossary}</dl></section>'
    faq = ''.join(f'<details class="faq"><summary><h3>{e(item["q"])}</h3></summary><div class="faq-a"><p>{e(item["a"])}</p></div></details>' for item in guide['faq'])
    faq = f'<section class="process-section"><h2>{e(guide["faq_title"])}</h2><div class="faqlist">{faq}</div></section>'
    sources = ''.join(f'<li><a href="{e(source["url"])}" target="_blank" rel="noopener">{e(source["n"][lang])}</a></li>' for source in C.PROCESS_GUIDE['sources'])
    sources = f'<section class="process-sources"><h2>{e(guide["sources_title"])}</h2><p>{e(guide["sources_intro"])}</p><ul>{sources}</ul></section>'
    contact = (f'<section class="process-contact"><div><h2>{e(guide["contact_title"])}</h2><p>{e(guide["contact_text"])}</p></div>'
               f'<a class="btn pri" href="{e(C.u_page(lang, "contact"))}">{e(guide["contact_button"])} →</a></section>')
    body = (R.cbar(lang, crumb_items=[(C.t(lang, "nav_home"), C.u_home(lang)), (C.t(lang, "n_process"), None)],
                   h1=C.t(lang, "verf_h1"), desc=C.t(lang, "verf_sub"), artwork='welding')
            + process_overview(lang)
            + '<div class="catalog"><div class="wrap process-guide">'
            + f'<section class="process-intro"><h2>{e(guide["intro_title"])}</h2><p>{e(guide["intro"])}</p>'
            + f'<p class="process-availability">{e(guide["availability"])}</p></section>'
            + f'<nav class="process-jump" aria-label="{e(guide["jump_label"])}">{jump}</nav>'
            + compare + toc + sections + glossary + faq + contact + sources + process_followup(lang) + '</div></div>')
    ld = [R.ld_org(lang), R.ld_webpage(lang, url, C.t(lang, "verf_title"), C.t(lang, "verf_desc")),
          R.ld_breadcrumb([(C.t(lang, "nav_home"), C.u_home(lang)), (C.t(lang, "n_process"), url)]),
          R.ld_faq_subset(lang, guide['faq'], url)]
    return url, R.document(lang, title=C.t(lang, "verf_title"), desc=C.t(lang, "verf_desc"),
                           url=url, alts=alts, jsonld_blocks=ld, body=body)


def page_downloads(lang):
    url, alts = C.u_page(lang, "downloads"), C.alternates("page", key="downloads")
    items = "".join(
        f'<a class="dlitem" href="{e(d["u"])}" target="_blank" rel="noopener">'
        f'<div class="ico">{e(d["k"])}</div><div class="nm">{e(d["t"].get(lang) or d["t"]["de"])}'
        f'<span>{e(d["s"].get(lang) or d["s"]["de"])}</span></div>'
        f'<span class="arw" aria-hidden="true">↓</span></a>' for d in C.DLS)
    body = (R.cbar(lang, crumb_items=[(C.t(lang, "nav_home"), C.u_home(lang)),
                                      (C.t(lang, "n_downloads"), None)],
                   h1=C.t(lang, "dl_h1"), desc=C.t(lang, "dl_sub"))
            + f'<div class="catalog"><div class="wrap">'
              f'<div class="dlrow dlrow-weit">{items}</div></div></div>')
    ld = [R.ld_org(lang), R.ld_webpage(lang, url, C.t(lang, "dl_title"), C.t(lang, "dl_desc")),
          R.ld_breadcrumb([(C.t(lang, "nav_home"), C.u_home(lang)),
                           (C.t(lang, "n_downloads"), url)])]
    return url, R.document(lang, title=C.t(lang, "dl_title"), desc=C.t(lang, "dl_desc"),
                           url=url, alts=alts, jsonld_blocks=ld, body=body)


def page_contact(lang):
    ws = C.WORKSHOP
    url, alts = C.u_page(lang, "contact"), C.alternates("page", key="contact")
    co = C.COMPANY
    body = (R.cbar(lang, crumb_items=[(C.t(lang, "nav_home"), C.u_home(lang)),
                                      (C.t(lang, "n_contact"), None)],
                   h1=C.t(lang, "k_h1"), desc=C.t(lang, "k_desc"), artwork='diagnostics', compact_mobile=True)
            + f"""<div class="catalog"><div class="wrap kontaktwrap">
  <div class="contact-main">
  <form class="form kform" id="kontaktForm" action="{e(C.u_page(lang,'contact'))}" method="post" aria-labelledby="inquiryHeading" novalidate>
    <h2 id="inquiryHeading">{e(C.t(lang,'cro_form_title'))}</h2>
    <p class="form-intro">{e(C.t(lang,'cro_form_intro'))}</p>
    {R.inquiry_topic_selector(lang)}
    <div class="inquiry-context" data-inquiry-context hidden></div>
    <label for="kName">{e(C.t(lang,'f_name'))}</label>
    <input id="kName" name="name" type="text" required autocomplete="organization" maxlength="120">
    <label for="kMail">{e(C.t(lang,'f_mail'))}</label>
    <input id="kMail" name="email" type="email" required autocomplete="email" maxlength="254" autocapitalize="none" spellcheck="false">
    <label for="kTel">{e(C.t(lang,'k_tel'))}</label>
    <input id="kTel" name="phone" type="tel" autocomplete="tel" maxlength="80" placeholder="+41 …">
    <label for="kMsg">{e(C.t(lang,'k_msg'))}</label>
    <textarea id="kMsg" name="message" rows="5" maxlength="5000" required></textarea>
    {R.inquiry_qualification(lang, 'k')}
    <input type="checkbox" name="botcheck" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
    {R.inquiry_next_steps(lang)}
    {R.form_note(lang)}
    <button class="send" type="submit">{e(C.t(lang,'f_send'))}</button>
    <p class="fstatus" role="status" aria-live="polite"></p>
  </form>
  {R.inquiry_summary(lang, 'kontaktForm')}
  <noscript><p>{e(C.t(lang,'form_nojs'))} <a href="mailto:{e(co['email'])}">{e(co['email'])}</a></p></noscript>
  <section class="contact-direct" aria-labelledby="whatsappHeading">
    <h2 id="whatsappHeading">{e(C.t(lang,'whatsapp_title'))}</h2>
    <p>{e(C.t(lang,'whatsapp_note'))}</p>
    {R.whatsapp_link(lang, button=True)}
  </section>
  </div>
  <aside class="kinfo">
    {R.design_icon('repair')}
    <p class="p-eyebrow">{e(C.t(lang,'volt_contact_title'))}</p>
    <h2>{e(co['owner'])}</h2>
    <p class="volt-owner-role">{e(C.t(lang,'site_name'))} · {e(C.t(lang,'volt_sole_trader'))}</p>
    <address>
      <a class="accent" href="tel:{co['phone_href']}">{e(co['phone'])}</a><br>
      <a class="accent" href="mailto:{co['email']}">{co['email']}</a><br><br>
      {e(C.t(lang,'hours_lbl'))}:<br>{e(C.t(lang,'hours'))}
    </address>
    <div class="korte">
      <div>
        <span class="kot">{e(C.t(lang,'addr_bill'))}</span>
        <address>{e(co['street'])}<br>{co['zip']} {e(co['city'])}<br>{e(C.land(lang))}</address>
      </div>
      <div>
        <span class="kot">{e(C.t(lang,'addr_shop'))}</span>
        <address>{e(ws['street'])}<br>{ws['zip']} {e(ws['city'])}<br>{e(C.land(lang))}</address>
        <p class="kohint">{e(C.t(lang,'addr_shop_note'))}
          <a href="{ws['partner_url']}" rel="noopener" target="_blank">{e(ws['partner'])}</a><br>
          {e(C.t(lang,'addr_shop_hint'))}</p>
      </div>
    </div>
  </aside>
</div></div>""")
    ld = [R.ld_org(lang),
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
    ld = [R.ld_org(lang), R.ld_faq(lang),
          R.ld_webpage(lang, url, C.t(lang, "faq_title"), C.t(lang, "faq_desc")),
          R.ld_breadcrumb([(C.t(lang, "nav_home"), C.u_home(lang)),
                           (C.t(lang, "nav_faq"), url)])]
    return url, R.document(lang, title=C.t(lang, "faq_title"), desc=C.t(lang, "faq_desc"),
                           url=url, alts=alts, jsonld_blocks=ld, body=body)


def page_search(lang):
    url, alts = C.u_page(lang, "search"), C.alternates("page", key="search")
    popular = C.SEARCH_POPULAR[lang]
    chips = "".join(f'<a class="chip" href="{e(url)}?q={e(x)}">{e(x)}</a>' for x in popular)
    body = (R.cbar(lang, crumb_items=[(C.t(lang, "nav_home"), C.u_home(lang)),
                                      (C.t(lang, "c_search"), None)],
                   h1=C.t(lang, "search_h1"), desc=C.t(lang, "search_lead"),
                   chips=f'<div class="chips">{chips}</div>')
            + f"""<div class="catalog"><div class="wrap">
  <form class="bigsearch" role="search" action="{e(url)}" method="get" id="pageSearchForm">
    <input id="pq" name="q" type="search" maxlength="120" placeholder="{e(C.t(lang,'search_ph'))}"
           aria-label="{e(C.t(lang,'c_search'))}" spellcheck="false" autocapitalize="none" enterkeyhint="search">
    <button type="submit">{e(C.t(lang,'search_btn'))}</button>
  </form>
  <div class="cathead"><h2 id="srTitle">{e(C.t(lang,'search_h1'))}</h2>
    <span class="count" id="srCount"></span></div>
  <div id="srResults"></div>
  <noscript><p class="noacc">{e(C.t(lang,'search_lead'))}
    <a href="{e(C.u_products(lang))}">{e(C.t(lang,'nav_all_products'))}</a></p></noscript>
</div></div>""")
    ld = [R.ld_org(lang), R.ld_webpage(lang, url, C.t(lang, "search_title"), C.t(lang, "search_desc"),
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

# Servicebereich: Uebersicht plus drei Unterseiten. Schluessel -> (Textpraefix,
# Beschriftung in UI.json). Die Aufteilung ist keine Kosmetik: "Schweissgeraet
# reparieren", "Schweissgeraet kalibrieren" und "Schweissautomation" sind drei
# verschiedene Suchen, und eine Seite kann nur fuer eine davon die beste
# Antwort sein. Vorher zeigten alle drei Links auf die Kontaktseite.
SERVICE = {
    "repair": ("svc_repair", "foot_diag"),
    "calib":  ("svc_calib",  "foot_calib"),
    "auto":   ("svc_auto",   "foot_auto"),
}


def page_service(lang, key=None):
    """key=None -> Uebersicht, sonst repair|calib|auto."""
    heim = (C.t(lang, "nav_home"), C.u_home(lang))
    hub_nav, hub_url = C.t(lang, "foot_service"), C.u_service(lang)

    if key is None:
        url, alts = hub_url, C.alternates("service")
        praefix, nav = "svc", hub_nav
        krumen = [heim, (hub_nav, None)]
        krumen_ld = [heim, (hub_nav, url)]
        karten = "".join(
            f'<a class="usp" href="{e(C.u_service(lang, k))}">'
            f'{R.design_icon(k)}<div><h2>{e(h)}</h2><p>{e(p)}</p></div><span class="volt-card-arrow" aria-hidden="true">→</span></a>'
            for k, h, p in C.EX[lang]["svc_items"])
        inhalt = (f'<section class="usps"><div class="wrap">'
                  f'<div class="usprow">{karten}</div></div></section>')
        steps = ''.join(f'<li><span class="volt-step-number" aria-hidden="true">{i:02d}</span>'
                        f'<div><h3>{e(h)}</h3><p>{e(text)}</p></div></li>'
                        for i, (h, text) in enumerate(C.t(lang, 'volt_steps'), 1))
        inhalt += (f'<section class="wrap volt-service-steps"><h2>{e(C.t(lang,"volt_steps_title"))}</h2>'
                   f'<ol>{steps}</ol></section>')
        inhalt += training_block(lang)
        values = {key:e(value) for key, value in {
            'ws_street':C.WORKSHOP['street'], 'ws_zip':C.WORKSHOP['zip'],
            'ws_city':C.WORKSHOP['city'], 'partner':C.WORKSHOP['partner'],
            'url_contact':C.u_page(lang, 'contact'),
            'url_repair':C.u_service(lang, 'repair'),
            'url_calib':C.u_service(lang, 'calib'),
            'url_auto':C.u_service(lang, 'auto')}.items()}
        inhalt += ('<div class="catalog"><div class="wrap textwrap legal">'
                   + ''.join(f'<section><h2>{e(h)}</h2>{text.format(**values)}</section>'
                             for h, text in C.EX[lang]['svc_body'])
                   + '</div></div>')
    else:
        praefix, navkey = SERVICE[key]
        nav = C.t(lang, navkey)
        url, alts = C.u_service(lang, key), C.alternates("service", key=key)
        krumen = [heim, (hub_nav, hub_url), (nav, None)]
        krumen_ld = [heim, (hub_nav, hub_url), (nav, url)]
        # Der Text bringt sein eigenes <p>/<ul> mit, wie bei den Rechtstexten.
        inhalt = ('<div class="catalog"><div class="wrap textwrap legal">'
                  + "".join(f"<section><h2>{e(h)}</h2>{b}</section>"
                            for h, b in C.EX[lang][f"{praefix}_body"])
                  + "</div></div>")

    title, desc = C.t(lang, f"{praefix}_title"), C.t(lang, f"{praefix}_desc")
    body = (R.cbar(lang, crumb_items=krumen,
                   h1=C.t(lang, 'volt_service_title') if key is None else C.t(lang, f"{praefix}_h1"),
                   desc=C.t(lang, f"{praefix}_lead"), artwork='diagnostics')
            + inhalt
            + '<div class="wrap"><section class="buying-guide service-guide">'
              f'<h2>{e(C.t(lang,"service_links_title"))}</h2>'
            + editorial_links(lang, C.GUIDE_LINKS['services'][key or 'overview'], url)
            + '</section></div>'
            + f'<section class="service-inquiry wrap"><h2>{e(C.t(lang,"inquiry_service_cta_title"))}</h2>'
              f'<p>{e(C.t(lang,"inquiry_service_cta_note"))}</p>'
              f'<a class="btn pri" href="{e(C.u_page(lang,"contact"))}?service={e(key or "overview")}">{e(C.t(lang,"inquiry_service_cta"))}</a></section>')

    ld = [R.ld_org(lang), R.ld_webpage(lang, url, title, desc),
          R.ld_breadcrumb(krumen_ld)]
    # Eine Dienstleistung ist kein Produkt: Service statt Product, und ohne
    # Preis - hier gilt dieselbe Regel wie im Katalog.
    ld.append({
        "@type": "Service",
        "@id": C.abs_url(url) + "#service",
        "name": C.t(lang, f"{praefix}_h1"),
        "description": desc,
        "serviceType": nav,
        "provider": {"@id": f"{C.SITE}/#organization"},
        "areaServed": [{"@type": "Country", "name": C.land(lang)},
                       {"@type": "Country", "name": "Liechtenstein"}],
        # serviceLocation erwartet einen Place. Ein blosser @id-Verweis auf den
        # Organization-Knoten liess Validatoren den Typ nicht erkennen; und
        # sachlich richtig ist ohnehin die Werkstatt in Herisau, nicht die
        # Rechnungsadresse in Bronschhofen - dort wird gearbeitet.
        "availableChannel": {
            "@type": "ServiceChannel",
            "serviceUrl": C.abs_url(url),
            "servicePhone": C.COMPANY["phone"],
            "serviceLocation": {
                "@type": "Place",
                "name": f"{C.COMPANY['name']} · {C.t(lang, 'foot_service')}",
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": C.WORKSHOP["street"],
                    "postalCode": C.WORKSHOP["zip"],
                    "addressLocality": C.WORKSHOP["city"],
                    "addressRegion": C.WORKSHOP["region"],
                    "addressCountry": "CH",
                },
                "geo": {"@type": "GeoCoordinates",
                        "latitude": C.WORKSHOP["lat"], "longitude": C.WORKSHOP["lon"]},
            },
        },
    })
    return url, R.document(lang, title=title, desc=desc, url=url, alts=alts,
                           jsonld_blocks=ld, body=body)


def page_legal(lang, kind):
    tkey, navkey, robots = LEGAL[kind]
    url, alts = C.u_page(lang, kind), C.alternates("page", key=kind)
    nav = C.t(lang, navkey)
    # Der Text bringt sein eigenes <p>/<ul> mit – Rechtstexte brauchen Listen,
    # und eine Liste in einem <p> waere kaputtes HTML.
    runtime = C.t(lang, 'privacy_runtime')
    if C.ga4_measurement_id():
        runtime = '<p>' + e(C.t(lang, 'privacy_runtime_ga4')) + '</p>' + runtime.split('</p>', 1)[1]
    purposes = ''
    if C.analytics_enabled():
        purposes += '<li>' + e(C.t(lang, 'privacy_analytics_purpose')) + '</li>'
        runtime += '<p>' + e(C.t(lang, 'privacy_analytics_common')) + '</p>'
        if C.cloudflare_analytics_token():
            runtime += '<p>' + e(C.t(lang, 'privacy_analytics_cloudflare')) + '</p>'
        if C.ahrefs_analytics_key():
            runtime += '<p>' + e(C.t(lang, 'privacy_analytics_ahrefs')) + '</p>'
        if C.ga4_measurement_id():
            runtime += '<p>' + e(C.t(lang, 'privacy_analytics_ga4')) + '</p>'
    else:
        runtime += '<p>' + e(C.t(lang, 'privacy_analytics_off')) + '</p>'
    if C.newsletter_forms():
        purposes += '<li>' + e(C.t(lang, 'privacy_newsletter_purpose')) + '</li>'
        runtime += '<p>' + e(C.t(lang, 'privacy_newsletter')) + '</p>'
    delivery = C.t(lang, 'privacy_delivery_direct' if C.web3forms_key() else 'privacy_delivery_mail')
    def body_text(body):
        return (body.replace('{runtime_privacy}', runtime)
                .replace('{runtime_optional_purposes}', purposes)
                .replace('{runtime_delivery}', delivery)
                .replace('{runtime_summary}', C.t(lang, 'privacy_summary'))
                .replace('{privacy_url}', C.u_page(lang, 'privacy')))
    secs = "".join(
        f"<section><h2>{e(h)}</h2>{b if b.lstrip().startswith('<') else '<p>' + b + '</p>'}</section>"
        for h, b in ((h, body_text(b)) for h, b in C.EX[lang][f"{tkey}_body"]))
    if kind == 'imprint':
        secs += company_navigation(lang, url)
    body = (R.cbar(lang, crumb_items=[(C.t(lang, "nav_home"), C.u_home(lang)), (nav, None)],
                   h1=C.t(lang, f"{tkey}_h1"), desc="")
            + f'<div class="catalog"><div class="wrap textwrap legal">{secs}</div></div>')
    title, desc = C.t(lang, f"{tkey}_title"), C.t(lang, f"{tkey}_desc")
    ld = [R.ld_org(lang), R.ld_webpage(lang, url, title, desc),
          R.ld_breadcrumb([(C.t(lang, "nav_home"), C.u_home(lang)), (nav, url)])]
    return url, R.document(lang, title=title, desc=desc, url=url, alts=alts,
                           jsonld_blocks=ld, body=body, robots=robots)


def page_about(lang):
    """Die Seite ueber das Unternehmen.

    Warum es sie gibt: die Search Console zeigte am 14.08.2026 bei 518
    Impressionen eine mittlere Position von 41 - die Website wird gefunden,
    aber weit hinten. Fuer ein junges Einzelunternehmen fehlt Google vor allem
    das, was es "wer steht dahinter" nennt: eine Seite, die Inhaber, Werkstatt,
    Herstellerprogramm und Pruefverfahren an einer Stelle nennt und mit dem
    Impressum, der Kontaktseite und den Serviceseiten zusammenhaengt.

    Alles darauf ist nachpruefbar. Erfundene Kundenstimmen stehen bewusst nicht
    da - sie waeren nach UWG Art. 3 Abs. 1 lit. b irrefuehrend und liessen sich
    von jeder interessierten Person widerlegen.
    """
    url, alts = C.u_page(lang, "about"), C.alternates("page", key="about")
    nav = C.t(lang, "nav_about")
    werte = dict(
        owner=C.COMPANY["owner"], street=C.COMPANY["street"], zip=C.COMPANY["zip"],
        city=C.COMPANY["city"], region_name=C.regionName(lang, C.COMPANY["region"]),
        hours=C.zeiten(lang), partner=C.WORKSHOP["partner"],
        ws_street=C.WORKSHOP["street"], ws_zip=C.WORKSHOP["zip"],
        ws_city=C.WORKSHOP["city"], ws_region_name=C.regionName(lang, C.WORKSHOP["region"]),
        url_kalib=C.u_service(lang, "calib"),
        url_repair=C.u_service(lang, "repair"),
        url_automation=C.u_service(lang, "auto"),
        # Historische Herstellererklaerung mit ausdruecklichem Geltungsbereich.
        url_dl=DL_EN1090["u"],
    )
    secs = "".join(
        f"<section><h2>{e(h)}</h2>{b.format(**werte)}</section>"
        for h, b in C.EX[lang]["about_body"])
    secs += company_navigation(lang, url)
    body = (R.cbar(lang, crumb_items=[(C.t(lang, "nav_home"), C.u_home(lang)), (nav, None)],
                   h1=C.t(lang, "about_h1"), desc=C.t(lang, "about_lead"))
            + training_block(lang, on_about=True)
            + f'<div class="catalog"><div class="wrap textwrap legal">{secs}</div></div>')
    title, desc = C.t(lang, "about_title"), C.t(lang, "about_desc")
    ld = [R.ld_org(lang), *R.ld_about(lang, url, title, desc),
          R.ld_breadcrumb([(C.t(lang, "nav_home"), C.u_home(lang)), (nav, url)])]
    return url, R.document(lang, title=title, desc=desc, url=url, alts=alts,
                           jsonld_blocks=ld, body=body)


def page_404(lang=C.DEFAULT_LANG):
    url, alts = "/404.html", C.alternates("home")
    body = f"""<div class="cbar"><div class="wrap">
  <h1>{e(C.t(lang,'err404_h1'))}</h1><p class="desc">{e(C.t(lang,'err404_lead'))}</p>
  <p class="cta-zeile"><a class="btn pri" href="/">{e(C.t(lang,'err404_cta'))}</a></p>
</div></div>"""
    return url, R.document(lang, title=C.t(lang, "err404_title"), desc=C.t(lang, "err404_lead"),
                           url="/", alts=alts, jsonld_blocks=[R.ld_org(lang)], body=body,
                           robots="noindex,follow", adressierbar=False)
