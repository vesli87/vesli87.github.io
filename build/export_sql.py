#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Den Katalog als SQL-Datenbank ausgeben.  Aufruf:

    python3 build/export_sql.py katalog.sql      # SQL-Text
    python3 build/export_sql.py katalog.sqlite   # fertige SQLite-Datei

Die Website hat keine Datenbank - sie wird aus den JSON-Dateien in data/
erzeugt und liegt danach als fertiges HTML auf dem Server. Fuer eine Sicherung
ist das gut (nichts kann kaputtgehen, was nicht auch im Git steht), fuer alles
andere nicht: man kann den Bestand nicht abfragen, nicht in ein Warenwirtschafts-
oder Shopsystem einlesen und niemandem eine Tabelle schicken.

Diese Datei schliesst die Luecke. Sie schreibt denselben Bestand, den die Seiten
zeigen, in ein relationales Schema - in allen drei Sprachen, mit den fertig
uebersetzten Texten, so wie sie auch im HTML stehen.

Massgeblich bleiben die JSON-Dateien. Der Dump ist eine Ableitung: er wird nie
zurueckgelesen, sondern jedes Mal neu erzeugt. Wer etwas aendern will, aendert
data/*.json und baut neu.

Preise stehen hier so wenig wie auf der Website - es gibt keine Spalte dafuer.
"""

import pathlib
import sqlite3
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import core as C  # noqa: E402

SPRACHEN = ("de", "fr", "it")

SCHEMA = """
CREATE TABLE kategorie (
  id        TEXT PRIMARY KEY,
  position  INTEGER NOT NULL
);
CREATE TABLE kategorie_text (
  kategorie_id  TEXT NOT NULL REFERENCES kategorie(id),
  sprache       TEXT NOT NULL,
  name          TEXT NOT NULL,
  beschreibung  TEXT,
  PRIMARY KEY (kategorie_id, sprache)
);
CREATE TABLE produkt (
  id              TEXT PRIMARY KEY,
  kategorie_id    TEXT NOT NULL REFERENCES kategorie(id),
  unterkategorie  TEXT,
  bild            TEXT,
  position        INTEGER NOT NULL
);
CREATE TABLE produkt_text (
  produkt_id    TEXT NOT NULL REFERENCES produkt(id),
  sprache       TEXT NOT NULL,
  name          TEXT NOT NULL,
  beschreibung  TEXT,
  verfahren     TEXT,
  url           TEXT,
  PRIMARY KEY (produkt_id, sprache)
);
CREATE TABLE produkt_technik (
  produkt_id  TEXT NOT NULL REFERENCES produkt(id),
  sprache     TEXT NOT NULL,
  position    INTEGER NOT NULL,
  merkmal     TEXT NOT NULL,
  wert        TEXT,
  PRIMARY KEY (produkt_id, sprache, position)
);
CREATE TABLE produkt_besonderheit (
  produkt_id  TEXT NOT NULL REFERENCES produkt(id),
  sprache     TEXT NOT NULL,
  position    INTEGER NOT NULL,
  text        TEXT NOT NULL,
  PRIMARY KEY (produkt_id, sprache, position)
);
CREATE TABLE produkt_option (
  produkt_id  TEXT NOT NULL REFERENCES produkt(id),
  sprache     TEXT NOT NULL,
  position    INTEGER NOT NULL,
  titel       TEXT NOT NULL,
  zusatz      TEXT,
  PRIMARY KEY (produkt_id, sprache, position)
);
CREATE TABLE produkt_dokument (
  produkt_id  TEXT NOT NULL REFERENCES produkt(id),
  sprache     TEXT NOT NULL,
  position    INTEGER NOT NULL,
  titel       TEXT NOT NULL,
  untertitel  TEXT,
  url         TEXT NOT NULL,
  PRIMARY KEY (produkt_id, sprache, position)
);
CREATE TABLE produkt_bild (
  produkt_id      TEXT NOT NULL REFERENCES produkt(id),
  sprache         TEXT NOT NULL,
  position        INTEGER NOT NULL,
  datei           TEXT NOT NULL,
  alt_text        TEXT,
  bildunterschrift TEXT,
  PRIMARY KEY (produkt_id, sprache, position)
);
CREATE TABLE oberflaechentext (
  schluessel  TEXT NOT NULL,
  sprache     TEXT NOT NULL,
  text        TEXT NOT NULL,
  PRIMARY KEY (schluessel, sprache)
);
CREATE TABLE angaben (
  schluessel  TEXT PRIMARY KEY,
  wert        TEXT
);
CREATE INDEX idx_produkt_kategorie ON produkt(kategorie_id);
CREATE INDEX idx_text_sprache      ON produkt_text(sprache);
"""


def stand():
    """Commit und Datum, damit man einem Dump ansieht, wovon er stammt."""
    def git(*a):
        try:
            return subprocess.run(["git", "-C", str(C.ROOT)] + list(a),
                                  capture_output=True, text=True,
                                  timeout=15).stdout.strip()
        except Exception:
            return ""
    return git("rev-parse", "HEAD"), git("log", "-1", "--format=%cI")


def fuellen(db):
    db.executescript(SCHEMA)

    for i, c in enumerate(C.CATS):
        db.execute("INSERT INTO kategorie VALUES (?,?)", (c["id"], i))
        for s in SPRACHEN:
            db.execute("INSERT INTO kategorie_text VALUES (?,?,?,?)",
                       (c["id"], s, C.catT(s, c), C.catD(s, c)))

    for i, p in enumerate(C.P):
        db.execute("INSERT INTO produkt VALUES (?,?,?,?,?)",
                   (p["id"], p["cat"], p.get("sub"), p.get("img"), i))
        for s in SPRACHEN:
            db.execute("INSERT INTO produkt_text VALUES (?,?,?,?,?,?)",
                       (p["id"], s, C.pName(s, p), C.pDesc(s, p),
                        " · ".join(C.verfahrenOf(s, p)), C.u_prod(s, p)))

            for n, (k, v) in enumerate(p.get("specs", {}).items()):
                db.execute("INSERT INTO produkt_technik VALUES (?,?,?,?,?)",
                           (p["id"], s, n, C.trK(s, k), C.trV(s, v)))

            for n, t in enumerate(C.highlightsOf(s, p) or []):
                db.execute("INSERT INTO produkt_besonderheit VALUES (?,?,?,?)",
                           (p["id"], s, n, t))

            for n, o in enumerate(C.optionsOf(s, p)):
                db.execute("INSERT INTO produkt_option VALUES (?,?,?,?,?)",
                           (p["id"], s, n, o.get("t", ""), o.get("s")))

            # DLDEV haelt die Uebersetzungen selbst, deshalb hier direkt
            for n, d in enumerate(C.DLDEV.get(p["id"], [])):
                db.execute("INSERT INTO produkt_dokument VALUES (?,?,?,?,?,?)",
                           (p["id"], s, n,
                            (d.get("t") or {}).get(s, ""),
                            (d.get("s") or {}).get(s), d["u"]))

            for n, g in enumerate(C.galleryOf(s, p)):
                db.execute("INSERT INTO produkt_bild VALUES (?,?,?,?,?,?)",
                           (p["id"], s, n, g["img"], g["alt"], g["cap"]))

    for k, v in C.UI.items():
        if not isinstance(v, dict):
            continue
        for s in SPRACHEN:
            if v.get(s):
                db.execute("INSERT INTO oberflaechentext VALUES (?,?,?)", (k, s, v[s]))

    commit, datum = stand()
    co = C.COMPANY
    for k, v in [("firma", co["name"]), ("inhaber", co.get("owner", "")),
                 ("adresse", f"{co['street']}, {co['zip']} {co['city']}"),
                 ("telefon", co["phone"]), ("email", co["email"]),
                 ("domain", C.SITE), ("commit", commit), ("stand", datum),
                 ("produkte", str(len(C.P))), ("sprachen", ", ".join(SPRACHEN)),
                 ("preise", "keine - Preis auf Anfrage, so wie auf der Website")]:
        db.execute("INSERT INTO angaben VALUES (?,?)", (k, v))
    db.commit()


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__.strip().splitlines()[2].strip())
    ziel = pathlib.Path(sys.argv[1])

    if ziel.suffix in (".sqlite", ".db", ".sqlite3"):
        if ziel.exists():
            ziel.unlink()
        db = sqlite3.connect(ziel)
        fuellen(db)
    else:
        db = sqlite3.connect(":memory:")
        fuellen(db)
        with ziel.open("w", encoding="utf-8") as f:
            f.write("-- VES-TECH Swiss - Katalog als SQL\n"
                    "-- Erzeugt von build/export_sql.py aus data/*.json.\n"
                    "-- Massgeblich sind die JSON-Dateien, nicht dieser Dump.\n"
                    "-- Einlesen:  sqlite3 katalog.sqlite < katalog.sql\n\n")
            for zeile in db.iterdump():
                f.write(zeile + "\n")

    n = db.execute("SELECT count(*) FROM produkt").fetchone()[0]
    z = sum(db.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
            for t in ("produkt_text", "produkt_technik", "produkt_besonderheit",
                      "produkt_option", "produkt_dokument", "produkt_bild",
                      "oberflaechentext"))
    print(f"{ziel.name}: {n} Produkte, {z} uebersetzte Zeilen, "
          f"{ziel.stat().st_size/1024:.0f} kB")


if __name__ == "__main__":
    main()
