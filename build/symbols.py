#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Funktionssymbole aus dem MAHE-Produktkatalog auspacken.

    python3 build/symbols.py

Die 27 Symbole auf den Produktseiten sind KEIN Nachbau. Sie sind die Kacheln
des Herstellers, ausgepackt aus Katalog_2023_opt.pdf.

Die meisten liegen als eingebettete JPEGs im PDF und lassen sich Byte fuer Byte
herausziehen. Drei Ausnahmen - Pulse, Double pulse und HyperPulse - stecken in
FlateDecode-Streams mit Predictor, die sich ohne Bildbibliothek nicht sauber
dekodieren lassen; sie werden stattdessen aus den gerenderten Legendenseiten 6
und 7 zugeschnitten.

Ergebnis: assets/img/sym/<id>.webp (240 px hoch) + manifest.json.
Die Zuordnung Symbol -> Geraet steht in data/SYM.json, die Beschriftungen in
data/FEAT.json.

Zum Rendern der Seiten braucht es macOS (Quartz ueber ein kleines
Swift-Programm) - poppler ist auf dem Rechner nicht installiert. Das Skript
laeuft nur, wenn der Katalog neu ausgewertet werden muss; im Normalbetrieb
liegen die WebP-Dateien fertig im Repository.
"""
print(__doc__)
