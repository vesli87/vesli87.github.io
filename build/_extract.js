function makePlaceholder(name){
  const t=(name||'MAHE').toUpperCase().replace(/[<>&']/g,' ');
  const svg='<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400">'+
    '<rect width="400" height="400" fill="#f4f4f2"/>'+
    '<rect x="1" y="1" width="398" height="398" fill="none" stroke="#e0e0da" stroke-width="2"/>'+
    '<text x="200" y="176" font-family="Arial,sans-serif" font-size="28" font-weight="bold" fill="#141414" text-anchor="middle">'+t+'</text>'+
    '<text x="200" y="212" font-family="Arial,sans-serif" font-size="15" fill="#F1531C" text-anchor="middle" letter-spacing="4">M A H E</text>'+
    '<text x="200" y="244" font-family="Arial,sans-serif" font-size="12" fill="#9A9A9F" text-anchor="middle">Produktbild</text></svg>';
  return 'data:image/svg+xml;utf8,'+encodeURIComponent(svg);
}
function imgFail(el,name,path){
  // 1. Versuch war lokal (images/). Schlaegt das fehl -> automatisch von mahe-online.de laden.
  if(path && el.dataset.step!=='remote'){el.dataset.step='remote';el.src=REMOTE+path;return;}
  // 2. Auch remote nicht erreichbar (z.B. blockierte Vorschau) -> saubere Namens-Kachel.
  el.onerror=null;el.src=makePlaceholder(name);
}
const PLACE=makePlaceholder('MAHE');

/* ---------- Piktogramme ---------- */
const PK={
  mig:'<svg viewBox="0 0 48 48" fill="none"><rect x="7" y="9" width="20" height="15" rx="3" stroke="#141414" stroke-width="3" stroke-linejoin="round"/><path d="M27 16 h6 a4 4 0 0 1 4 4 v1" stroke="#141414" stroke-width="3" stroke-linecap="round"/><path d="M37 21 l4 4" stroke="#141414" stroke-width="3" stroke-linecap="round"/><circle cx="24" cy="35" r="5" fill="#F1531C"/><path d="M24 35 l-7 6 M24 35 l8 5 M24 35 l-2 9" stroke="#F1531C" stroke-width="2.4" stroke-linecap="round" opacity=".55"/></svg>',
  plasma:'<svg viewBox="0 0 48 48" fill="none"><path d="M17 6 h14 l-4 13 h-6 z" stroke="#141414" stroke-width="3" stroke-linejoin="round"/><path d="M24 19 V31" stroke="#F1531C" stroke-width="4" stroke-linecap="round"/><path d="M6 38 h36" stroke="#141414" stroke-width="3" stroke-linecap="round"/><path d="M24 31 l-5 6 M24 31 l5 6" stroke="#F1531C" stroke-width="2.4" stroke-linecap="round"/></svg>',
  clean:'<svg viewBox="0 0 48 48" fill="none"><path d="M18 6 L21.5 16.5 L32 20 L21.5 23.5 L18 34 L14.5 23.5 L4 20 L14.5 16.5 Z" fill="#F1531C"/><path d="M35 26 L37 32 L43 34 L37 36 L35 42 L33 36 L27 34 L33 32 Z" fill="#141414"/></svg>',
  gear:'<svg viewBox="0 0 48 48" fill="none"><circle cx="20" cy="20" r="6.5" stroke="#141414" stroke-width="3"/><path d="M20 8 v4 M20 28 v4 M8 20 h4 M28 20 h4 M11.5 11.5 l3 3 M25.5 25.5 l3 3 M28.5 11.5 l-3 3 M14.5 25.5 l-3 3" stroke="#141414" stroke-width="3" stroke-linecap="round"/><circle cx="34" cy="34" r="6" fill="#F1531C"/><circle cx="34" cy="34" r="1.8" fill="#fff"/></svg>'
};

/* ---------- Kategorien ---------- */
const CATS=[
  {id:'schweissgeraete',t:'Schweissgeräte',pk:'mig',d:'MIG/MAG, WIG/TIG, MMA und Plasma-TIG – Hochleistungsstromquellen von MAHE mit Upgrade-Technologie.',
   subs:['MIG / MAG','WIG / TIG','MMA','Plasma TIG']},
  {id:'plasmaschneiden',t:'Plasmaschneiden',pk:'plasma',d:'Theta Plasmaschneidinverter mit HSC-Technologie – von 15 mm bis 80 mm Schneidleistung, als Hand- und Automationsversion.',
   subs:['Theta','Theta Automation']},
  {id:'reinigung',t:'Reinigungsgeräte',pk:'clean',d:'Elektrolytisches Reinigen und Polieren von Schweissnähten, Signieren von Metall und automatische Dosierung.',
   subs:['Cleaner','Signiergeräte','Dosiersystem','Elektrolyte']},
  {id:'zubehoer',t:'Zubehör',pk:'gear',d:'Fahrwagen, Wasserkühlung, Drahtvorschubkoffer, Fernbedienungen und Werkstattausrüstung – abgestimmt auf jede MAHE-Serie.',
   subs:['Fahrwagen','Wasserkühlung','Drahtvorschubkoffer','Fernbedienungen','Werkstattausrüstung','Kabel','Brenner']}
];

/* ---------- Produkte (echte MAHE-Daten) ---------- */
/* ---------- Bildquelle ----------
   USE_LOCAL = true  -> Bilder aus dem lokalen Ordner "images/" (empfohlen, nachdem du sie heruntergeladen hast)
   USE_LOCAL = false -> Bilder direkt von mahe-online.de (Hotlink)
   Die Bilddateien im Ordner "images/" heissen exakt wie bei MAHE, z.B. STT30-300x300.png            */
const USE_LOCAL=false;
const REMOTE='https://mahe-online.de/wp-content/uploads/';
const LOCAL='images/';
const IMG=''; // Platzhalter – die Produkte speichern nur den relativen Pfad
var EMBED={};/*EMBED-MARKER*/
function SRC(path){var fn=path.split('/').pop(); if(EMBED[fn])return EMBED[fn]; return USE_LOCAL?LOCAL+fn:REMOTE+path;}
function fullImg(path){return path.replace(/-[0-9]+x[0-9]+(\.[a-zA-Z]+)$/,'$1');}
const P=[
  // ---- MIG/MAG ----
  {id:'hypermig-x',cat:'schweissgeraete',sub:'MIG / MAG',vt:'MIG/MAG',name:'HyperMIG X',img:'2022/03/Bild-der-Hypers.png',
   desc:'Voll ausgestattete Puls-MIG/MAG-Serie mit HyperForce und MIS spritzerfreiem Schweissen.',
   specs:{'Verfahren':'MIG/MAG · HyperPuls · Doppelpuls · MMA · WIG','Strombereich':'10 – 420 A','Netz':'3~ 400 V · 50/60 Hz','Netzabsicherung':'25 A','Leerlaufspannung':'76 V','Einschaltdauer':'45 % @ 400 A · 60 % @ 360 A','Kühlung':'luft-/wassergekühlt','Antrieb':'4-Rollen','Betriebsart':'Synergic / JOB (99)','Schutzklasse':'IP23','Gewicht':'bis 103 kg (WWK)'}},
  {id:'ecomig',cat:'schweissgeraete',sub:'MIG / MAG',vt:'MIG/MAG',name:'EcoMIG Digital / Analog',img:'2023/03/EcoMig-spolu-1.png',
   desc:'Ultrakompakte, stufenlose MIG/MAG-Schweissinverter für einfache Bedienung.',
   specs:{'Verfahren':'MIG/MAG','Strombereich':'bis 300 A','Netz':'3~ 400 V','Antrieb':'4-Rollen','Ausführung':'Kompakt/fahrbar','Bedienung':'Digital oder Analog'}},
  {id:'mms',cat:'schweissgeraete',sub:'MIG / MAG',vt:'MIG/MAG',name:'MMS 2000 / 3000',img:'2026/03/MMS3000_X_MMS2000-300x202.png',
   desc:'Mobile, leichte MIG/MAG-Schweissmaschine für Montage und Werkstatt.',
   specs:{'Verfahren':'MIG/MAG','Einsatz':'Montage / Werkstatt','Bauart':'tragbar','Serie':'MMS 2000 · MMS 3000'}},
  // ---- WIG ----
  {id:'omega-ax',cat:'schweissgeraete',sub:'WIG / TIG',vt:'WIG AC/DC',name:'Omega AX',img:'2026/01/Omega220AX-Pro-300x300.png',
   desc:'Mobile AC/DC WIG-Schweissmaschine für Aluminium und Stahl.',
   specs:{'Verfahren':'WIG AC/DC','Strombereich':'bis 220 A','Netz':'1~ 230 V','Zündung':'HF','Bauart':'mobil'}},
  {id:'beta-dx',cat:'schweissgeraete',sub:'WIG / TIG',vt:'WIG DC',name:'Beta DX',img:'2026/01/Beta220DX_Pro-300x300.png',
   desc:'Mobile WIG DC Schweissmaschine für Stahl und Chromstahl.',
   specs:{'Verfahren':'WIG DC','Strombereich':'bis 220 A','Netz':'1~ 230 V','Bauart':'mobil'}},
  {id:'hypertig-ax',cat:'schweissgeraete',sub:'WIG / TIG',vt:'WIG AC/DC',name:'HyperTIG AX',img:'2024/06/IMGP5943-226x300.png',
   desc:'Leistungsstarke WIG AC/DC Stromquelle für den industriellen Einsatz.',
   specs:{'Verfahren':'WIG AC/DC','Strombereich':'bis 350 A','Netz':'3~ 400 V','Kühlung':'wassergekühlt (CWK)'}},
  {id:'hypertig-dx',cat:'schweissgeraete',sub:'WIG / TIG',vt:'WIG DC',name:'HyperTIG DX',img:'2024/06/IMGP5957-229x300.png',
   desc:'Leistungsstarke WIG DC Stromquelle für hohe Abschmelzleistung.',
   specs:{'Verfahren':'WIG DC','Strombereich':'bis 400 A','Netz':'3~ 400 V','Kühlung':'wassergekühlt'}},
  {id:'beta-digital',cat:'schweissgeraete',sub:'WIG / TIG',vt:'WIG',name:'Beta digital',img:'2021/04/Beta-Digital-300-261x300.png',
   desc:'Mobile digitale WIG-Schweissmaschine mit Programmspeicher.',
   specs:{'Verfahren':'WIG DC','Strombereich':'bis 300 A','Netz':'3~ 400 V','Bedienung':'digital'}},
  {id:'hypertig-acdc',cat:'schweissgeraete',sub:'WIG / TIG',vt:'WIG AC/DC',name:'HyperTIG AC/DC',img:'2020/03/hypertig-ac-dc-cwk-300x300.png',
   desc:'Leistungsstarke AC/DC Stromquelle für höchste Anforderungen.',
   specs:{'Verfahren':'WIG AC/DC','Strombereich':'bis 600 A','Netz':'3~ 400 V','Kühlung':'wassergekühlt (CWK)'}},
  // ---- MMA ----
  {id:'i-1600',cat:'schweissgeraete',sub:'MMA',vt:'MMA',name:'i-1600',img:'2020/03/i-1600-300x300.png',
   desc:'Einfach zu bedienender, robuster Elektrodeninverter.',
   specs:{'Verfahren':'MMA (Elektrode)','Netz':'1~ 230 V','Bauart':'tragbar','Bedienung':'einfach'}},
  {id:'delta',cat:'schweissgeraete',sub:'MMA',vt:'MMA',name:'Delta',img:'2019/10/Delta-300x300.png',
   desc:'Multifunktions-Elektrodeninverter für Werkstatt und Baustelle.',
   specs:{'Verfahren':'MMA · WIG-Lift','Netz':'230/400 V','Bauart':'tragbar'}},
  {id:'delta-digital',cat:'schweissgeraete',sub:'MMA',vt:'MMA',name:'Delta Digital',img:'2019/10/deltadigital-300x300.png',
   desc:'Digitaler Multifunktions-Inverter für den Profi.',
   specs:{'Verfahren':'MMA · WIG','Bedienung':'digital','Speicher':'JOB-Programme'}},
  {id:'delta-digital-ds',cat:'schweissgeraete',sub:'MMA',vt:'MMA',name:'Delta Digital DS',img:'2020/03/delta-digital-ds-300x300.png',
   desc:'Multiprozess-Stromquelle, entwickelt für das Unterwasserschweissen.',
   specs:{'Verfahren':'MMA · Unterwasser','Bedienung':'digital','Einsatz':'Diving / Offshore'}},
  // ---- Plasma TIG ----
  {id:'plasma-tig',cat:'schweissgeraete',sub:'Plasma TIG',vt:'Plasma TIG',name:'PlasmaTIG',img:'2019/10/plasmatig-300x300.png',
   desc:'Mikroplasma- und Plasmastromquelle für feinste Schweissungen.',
   specs:{'Verfahren':'Plasma / Mikroplasma','Strombereich':'20 – 400 A','Einsatz':'Feinblech bis Industrie'}},
  // ---- Plasmaschneiden / Theta ----
  {id:'theta-40',cat:'plasmaschneiden',sub:'Theta',vt:'Plasma Cut',name:'Theta 40',img:'2020/03/theta-40-300x300.png',
   desc:'Leichtes 230-V-Plasmaschneidgerät für die Werkstatt.',
   specs:{'Verfahren':'Plasmaschneiden','Schneidleistung':'bis 15 mm','Netz':'1~ 230 V','Bauart':'tragbar'}},
  {id:'theta-60',cat:'plasmaschneiden',sub:'Theta',vt:'Plasma Cut',name:'Theta 60 HSC',img:'2020/03/theta-60-hsc-300x300.png',
   desc:'Leistungsstarker Plasmaschneidinverter mit HSC-Technologie.',
   specs:{'Verfahren':'Plasmaschneiden','Schneidleistung':'bis 40 mm','Technologie':'HSC','Netz':'3~ 400 V'}},
  {id:'theta-120',cat:'plasmaschneiden',sub:'Theta',vt:'Plasma Cut',name:'Theta 120 HSC',img:'2020/03/theta-120-hsc-300x300.png',
   desc:'Industrieller Plasmaschneidinverter mit HSC-Technologie.',
   specs:{'Verfahren':'Plasmaschneiden','Schneidleistung':'bis 55 mm','Technologie':'HSC','Netz':'3~ 400 V'}},
  {id:'theta-180',cat:'plasmaschneiden',sub:'Theta',vt:'Plasma Cut',name:'Theta 180 HSC',img:'2022/06/IMGP5680-258x300.png',
   desc:'Stärkster Theta-Plasmaschneidinverter mit HSC-Technologie.',
   specs:{'Verfahren':'Plasmaschneiden','Schneidleistung':'bis 80 mm','Technologie':'HSC','Netz':'3~ 400 V'}},
  // ---- Reinigung ----
  {id:'minicleaner',cat:'reinigung',sub:'Cleaner',vt:'Cleaner',name:'MiniReiniger',img:'2020/03/minicleaner-300x300.png',
   desc:'Wirtschaftlicher Inverter, speziell für den mobilen Einsatz.',
   specs:{'Verfahren':'Elektrolyt-Reinigung','Einsatz':'mobil','Werkstoff':'Chromstahl'}},
  {id:'hypercleaner-st',cat:'reinigung',sub:'Cleaner',vt:'Cleaner',name:'HyperCleaner ST',img:'2025/07/HyperCleanerST_SET_NEW-300x191.png',
   desc:'Leistungsstarker 1200-W-Inverter für hervorragende Reinigungsergebnisse.',
   specs:{'Leistung':'1200 W','Verfahren':'Elektrolyt-Reinigung','Lieferung':'als Set'}},
  {id:'hypercleaner-speed',cat:'reinigung',sub:'Cleaner',vt:'Cleaner',name:'HyperCleaner ST Speed',img:'2020/11/HyperCleaner-ST-Plus_SET-300x219.png',
   desc:'Leistungsstarker 2500-W-Inverter für schnelle Reinigung.',
   specs:{'Leistung':'2500 W','Verfahren':'Elektrolyt-Reinigung','Lieferung':'als Set'}},
  {id:'hypercleaner-plus',cat:'reinigung',sub:'Cleaner',vt:'Cleaner',name:'HyperCleaner ST Plus',img:'2020/11/HyperCleaner-ST-Plus_SET-300x219.png',
   desc:'Leistungsstarker 4000-W-Inverter für den Industrieeinsatz.',
   specs:{'Leistung':'4000 W','Verfahren':'Elektrolyt-Reinigung','Lieferung':'als Set'}},
  {id:'hypercleaner-ct200',cat:'reinigung',sub:'Cleaner',vt:'WIG + Cleaner',name:'HyperCleaner CT 200',img:'2021/04/HyperCleaner-CT200-SET-300x189.png',
   desc:'Kombiniertes WIG-Schweiss- und Reinigungsgerät.',
   specs:{'Verfahren':'WIG + Reinigung','Kombi':'2-in-1','Lieferung':'als Set'}},
  // ---- Zubehör: Fahrwagen ----
  {id:'stt30',cat:'zubehoer',sub:'Fahrwagen',vt:'Fahrwagen',name:'STT 30',img:'2020/03/STT30-300x300.png',
   desc:'Fahrwagen mit Gasflaschenhalter für WIG- und MIG-Geräte.',
   specs:{'Für':'i-TIG, Beta, Omega, MMS','Maße (LxBxH)':'625×600×1050 mm','Gewicht':'22 kg','Gasflasche':'ja'}},
  {id:'stt35',cat:'zubehoer',sub:'Fahrwagen',vt:'Fahrwagen',name:'STT 35',img:'2021/05/STT35-200x300.png',
   desc:'Fahrwagen ohne Gasflaschenhalter für MMA und Plasma.',
   specs:{'Für':'Delta, Delta Digital, Theta','Maße (LxBxH)':'700×600×1050 mm','Gewicht':'21 kg','Gasflasche':'nein'}},
  {id:'mpf02',cat:'zubehoer',sub:'Fahrwagen',vt:'Fahrwagen',name:'MPF 02',img:'2023/03/IMGP5689-e1678778035688-219x300.png',
   desc:'Fahrwagen mit Gasflaschenhalter für alle tragbaren Geräte.',
   specs:{'Für':'Delta, i-TIG, Beta, Omega, MMS, Theta','Maße (LxBxH)':'840×450×710 mm','Gewicht':'21 kg','Gasflasche':'ja'}},
  {id:'mhct01',cat:'zubehoer',sub:'Fahrwagen',vt:'Fahrwagen',name:'MHCT 01',img:'2020/09/Fahrwagen-fur-Cleaner-206x300.png',
   desc:'Fahrwagen speziell für Reinigungsgeräte.',
   specs:{'Für':'HyperCleaner','Maße (LxBxH)':'380×415×700 mm','Gewicht':'16 kg'}},
  // ---- Zubehör: Wasserkühlung ----
  {id:'wk200',cat:'zubehoer',sub:'Wasserkühlung',vt:'Kühlung',name:'WK 200',img:'2020/03/wk200-300x300.png',
   desc:'Universalkühler mit 230-V-Schuko-Steckdose und Wassermangel-Abschaltung.',
   specs:{'Typ':'Universalkühler','Steckdose':'230 V Schuko','Schutz':'Wassermangel-Abschaltung'}},
  {id:'wk300',cat:'zubehoer',sub:'Wasserkühlung',vt:'Kühlung',name:'WK 300',img:'2020/03/wk300-300x300.png',
   desc:'Wasserkühlgerät für die MMS-3000-Serie.',
   specs:{'Für':'MMS 3000 Serie','Typ':'Wasserkühlgerät'}},
  {id:'wk350',cat:'zubehoer',sub:'Wasserkühlung',vt:'Kühlung',name:'WK 350',img:'2020/03/wk350-300x300.png',
   desc:'Wasserkühlgerät für Beta digital und Omega 400-V-Linie.',
   specs:{'Für':'Beta digital · Omega 400 V','Typ':'Wasserkühlgerät'}},
  // ---- Zubehör: Drahtvorschub ----
  {id:'dvs410',cat:'zubehoer',sub:'Drahtvorschubkoffer',vt:'Vorschub',name:'DVS 410',img:'2022/03/DVS410-320x220.png',
   desc:'Leichter Drahtvorschubkoffer für die HyperMIG-X-Serie.',
   specs:{'Für':'HyperMIG X','Bauart':'leicht / tragbar'}},
  {id:'dvl420',cat:'zubehoer',sub:'Drahtvorschubkoffer',vt:'Vorschub',name:'DVL 420',img:'2024/09/DVL420-300x238.png',
   desc:'Vollmetall-Horizontalvorschubkoffer für die HyperMIG-X-Serie.',
   specs:{'Für':'HyperMIG X','Gehäuse':'Vollmetall','Bauart':'horizontal'}},
  // ---- Zubehör: Fernbedienungen ----
  {id:'frc5',cat:'zubehoer',sub:'Fernbedienungen',vt:'Fernregler',name:'FRC 5',img:'2020/03/frc5-300x300.png',
   desc:'Fussfernregler für alle MAHE WIG-Geräte.',
   specs:{'Typ':'Fussfernregler','Für':'MAHE WIG'}},
  {id:'rc5',cat:'zubehoer',sub:'Fernbedienungen',vt:'Fernregler',name:'RC 5',img:'2020/03/rc5-300x300.png',
   desc:'Handfernregler für alle MAHE WIG- und MMA-Geräte.',
   specs:{'Typ':'Handfernregler','Für':'MAHE WIG · MMA'}},
  {id:'rc15',cat:'zubehoer',sub:'Fernbedienungen',vt:'Fernregler',name:'RC 15',img:'2020/03/rc15-300x300.png',
   desc:'Handfernregler mit Up/Down- und Start/Stopp-Taste.',
   specs:{'Typ':'Handfernregler','Funktion':'Up/Down · Start/Stopp'}},
  {id:'rc100',cat:'zubehoer',sub:'Fernbedienungen',vt:'Fernregler',name:'RC 100',img:'2020/03/rc100-300x300.png',
   desc:'Handfernregler für alle MAHE WIG- und MMA-Geräte.',
   specs:{'Typ':'Handfernregler','Für':'MAHE WIG · MMA'}},
  {id:'rc100ds',cat:'zubehoer',sub:'Fernbedienungen',vt:'Fernregler',name:'RC 100 DS',img:'2020/03/rc100ds-300x300.png',
   desc:'Handfernregler speziell für Delta-Digital-DS-Maschinen.',
   specs:{'Typ':'Handfernregler','Für':'Delta Digital DS'}},
  // ---- Theta Automation ----
  {id:'theta-60-aut',cat:'plasmaschneiden',sub:'Theta Automation',vt:'Plasma AUT',name:'Theta 60 AUT',img:'2020/03/theta-120-hsc-300x300.png',
   desc:'Automations-Plasmaschneidinverter mit HSC-Technologie für den Maschineneinbau.',
   specs:{'Verfahren':'Plasmaschneiden · Automation','Schneidleistung':'bis 40 mm','Technologie':'HSC','Schnittstelle':'CNC / Automation'}},
  {id:'theta-120-aut',cat:'plasmaschneiden',sub:'Theta Automation',vt:'Plasma AUT',name:'Theta 120 AUT',img:'2020/03/theta-120-hsc-300x300.png',
   desc:'Automations-Plasmaschneidinverter mit HSC-Technologie für den Maschineneinbau.',
   specs:{'Verfahren':'Plasmaschneiden · Automation','Schneidleistung':'bis 55 mm','Technologie':'HSC','Schnittstelle':'CNC / Automation'}},
  // ---- Signiergeräte ----
  {id:'hcs1',cat:'reinigung',sub:'Signiergeräte',vt:'Signieren',name:'HCS 1',img:'2020/12/HCS-1-SET-300x248.png',
   desc:'Ökonomisches elektrolytisches Signiergerät, speziell für den mobilen Einsatz.',
   specs:{'Verfahren':'Elektrolyt-Signieren','Einsatz':'mobil','Lieferung':'Set mit Koffer'}},
  // ---- Dosiersystem ----
  {id:'mlf100',cat:'reinigung',sub:'Dosiersystem',vt:'Dosierung',name:'MLF 100',img:'2026/01/MLF100_A-300x136.png',
   desc:'Gerät zur automatischen Dosierung von Reinigungsflüssigkeit.',
   specs:{'Funktion':'automatische Dosierung','Medium':'Reinigungsflüssigkeit','Einsatz':'HyperCleaner-Serie'}},
  // ---- Werkstattausrüstung ----
  {id:'mcu1',cat:'zubehoer',sub:'Werkstattausrüstung',vt:'Kalibrierung',name:'MCU 1',img:'2019/10/mcu11-300x300.png',
   desc:'MAHE Kalibriergerät für Kalibrier- und Validierarbeiten – grosse Volt-/Ampere-Anzeigen, leicht.',
   specs:{'Funktion':'Kalibrieren / Validieren','Anzeige':'Volt & Ampere (gross)','Gewicht':'16,5 kg'}},
  {id:'usb2in1',cat:'zubehoer',sub:'Werkstattausrüstung',vt:'Programmierung',name:'USB 2in1 Programmierer',img:'2019/10/usb2in1programmer-300x300.png',
   desc:'Programmiergerät für Micro-Controller und MAHE-Schnittstellen, inkl. USB-Software.',
   specs:{'Funktion':'Controller-Programmierung','Schnittstelle':'USB / MAHE','Software':'inklusive'}},
  // ---- Reinigung: Elektrolyte (Mittel) ----
  {id:'r1',cat:'reinigung',sub:'Elektrolyte',vt:'Reinigung',name:'Reinigungselektrolyt Rapid R1',img:'2022/05/1850002-210x300.png',
   desc:'Schnelles Reinigungselektrolyt für Chromstahl-Schweissnähte.',
   specs:{'Typ':'Reinigung (Rapid)','Werkstoff':'Chromstahl','Gebinde':'0,5 / 1,0 / 5,0 L','Sicherheitsdatenblatt':'R1'}},
  {id:'rp1',cat:'reinigung',sub:'Elektrolyte',vt:'Reinigung',name:'Reinigungselektrolyt RP1 Pastös',img:'2022/05/1851002-210x300.png',
   desc:'Pastöses Reinigungselektrolyt für senkrechte Flächen und Überkopf.',
   specs:{'Typ':'Reinigung (pastös)','Werkstoff':'Chromstahl','Gebinde':'0,5 / 1,0 / 5,0 L','Sicherheitsdatenblatt':'RP1'}},
  {id:'p1',cat:'reinigung',sub:'Elektrolyte',vt:'Polieren',name:'Polierelektrolyt P1',img:'2022/05/1852002-210x300.png',
   desc:'Elektrolyt zum Elektropolieren und Beizen von Edelstahl.',
   specs:{'Typ':'Polieren / Beizen','Werkstoff':'Edelstahl','Gebinde':'0,5 / 1,0 / 5,0 L','Sicherheitsdatenblatt':'P1'}},
  {id:'n1',cat:'reinigung',sub:'Elektrolyte',vt:'Neutralisieren',name:'Neutralit N1',img:'2022/05/1855002-210x300.png',
   desc:'Neutralisierer zum Abstoppen und Neutralisieren nach dem Reinigen.',
   specs:{'Typ':'Neutralisierer','Anwendung':'nach Reinigung','Gebinde':'1,0 / 5,0 L','Sicherheitsdatenblatt':'N1'}},
  {id:'m1',cat:'reinigung',sub:'Elektrolyte',vt:'Signieren',name:'Signierelektrolyt M1',img:'2022/05/1853001-127x300.png',
   desc:'Elektrolyt zum elektrochemischen Signieren und Markieren von Metall.',
   specs:{'Typ':'Signieren','Anwendung':'Markieren','Gebinde':'0,1 / 0,5 / 1,0 L','Sicherheitsdatenblatt':'M1'}},
  // ---- Zubehör: Kabel ----
  {id:'elektrodenkabel',cat:'zubehoer',sub:'Kabel',vt:'Kabel',name:'Elektrodenkabel 10 mm²',img:'2021/06/1801001-300x214.png',
   desc:'Elektrodenkabel für Cleaner- und MMA-Geräte.',
   specs:{'Querschnitt':'10 mm²','Längen':'3 / 6 / 10 m','Farbe':'blau'}},
  {id:'massekabel',cat:'zubehoer',sub:'Kabel',vt:'Kabel',name:'Massekabel 10 mm²',img:'2021/06/1802001-300x214.png',
   desc:'Massekabel mit Klemme für Cleaner- und MMA-Geräte.',
   specs:{'Querschnitt':'10 mm²','Längen':'3 / 6 / 10 m','Farbe':'schwarz'}},
  // ---- Zubehör: Brenner ----
  {id:'mf405w',cat:'zubehoer',sub:'Brenner',vt:'Brenner',name:'MF405W',img:'2021/05/MIG_Brenner-292x300.png',
   desc:'Wassergekühlter MIG/MAG-Brenner für die HyperMIG X Serie.',
   specs:{'Typ':'MIG/MAG wassergekühlt','Länge':'4 m','Option':'wahlweise mit Up/Down'}},
  {id:'mf240w',cat:'zubehoer',sub:'Brenner',vt:'Brenner',name:'MF240W',img:'2021/05/MIG_Brenner-292x300.png',
   desc:'Wassergekühlter MIG/MAG-Brenner für kleinere Leistungsklassen.',
   specs:{'Typ':'MIG/MAG wassergekühlt','Länge':'4 m','Option':'wahlweise mit Up/Down'}}
];

/* ---------- State ---------- */
let cart=[];
/* ================= i18n ================= */
let LANG='de';
const UI={"de": {"hours": "Mo–Fr 07:30–17:30", "search_ph": "Gerät oder Verfahren suchen (z.B. HyperMIG)", "search_btn": "Suchen", "inquiry": "ANFRAGE", "menu_title": "MENÜ · MAHE PROGRAMM", "m_inquire": "TECHNIK ANFRAGEN", "m_all": "ALLE GERÄTE", "n_service": "Service", "n_downloads": "Downloads", "n_warranty": "Garantie", "n_process": "Verfahren", "n_contact": "Kontakt", "hero_pre": "Ihr direkter Techniker für ", "hero_acc": "Schweisstechnik & Automation.", "hero_lead": "Diagnose, Reparatur, Kalibrierung und Automation für Schweissgeräte und industrielle Prozesse – persönlich, nachvollziehbar und mit Blick auf die Elektronik.", "hero_cta1": "Technik direkt anfragen →", "hero_cta2": "MAHE Systeme ansehen", "prog_eyebrow": "MAHE GERÄTEPROGRAMM", "prog_h2": "Direkt zum richtigen Verfahren.", "prog_sub": "Alle MAHE-Schweiss-, Schneid-, Reinigungs- und Automationssysteme in einer klaren Übersicht – geordnet nach Verfahren, so wie es der Schweisser im Kopf hat. Preise auf Anfrage.", "card_open": "Programm öffnen →", "devices": "Geräte", "trust_h3": "EN 1090 · geprüft & dokumentiert", "trust_p": "Für tragende Stahl- und Aluminiumbauten liefern wir das komplette Prüf- und Konformitätspaket – abgestimmt auf Ihre MAHE-Anlagen.", "dl": "DOWNLOAD", "dl_cat": "Produktkatalog", "dl_cat_p": "Das komplette MAHE-Programm als PDF.", "svc": "SERVICE", "dl_en": "EN 1090 anfordern", "dl_en_p": "Konformitätspaket für Ihre Anlage.", "c_home": "Home", "c_products": "Produkte", "c_search": "Suche", "chip_all": "Alle", "sec_all": "Alle Geräte", "items": "Artikel", "poa": "Preis auf Anfrage", "inquire": "Anfragen +", "techdata": "Technische Daten", "poa_sub": "Individuelles Angebot inkl. Schweizer Service & Garantieabwicklung.", "to_inquiry": "Zur Anfrageliste +", "consult": "Beratung anfragen", "added": "Zur Anfrageliste hinzugefügt", "already": "Bereits auf der Liste", "cart_title": "Anfrageliste", "cart_empty": "Ihre Anfrageliste ist leer. Fügen Sie Geräte hinzu und senden Sie eine gebündelte Anfrage.", "f_name": "Name / Firma", "f_mail": "E-Mail", "f_msg": "Nachricht (optional)", "f_send": "Anfrage senden →", "k_h1": "Direkter Draht zum Techniker.", "k_desc": "Ein Gerät, das streikt, oder ein Prozess, der schneller laufen soll? Beschreiben Sie kurz Ihre Situation – Sie erhalten eine ehrliche Ersteinschätzung.", "k_tel": "Telefon", "k_msg": "Ihre Nachricht", "foot_brand": "Schweisstechnik & Automation aus Bronschhofen. Verkauf, Service und Automation für das MAHE-Geräteprogramm – aus einer Hand.", "foot_products": "Produkte", "foot_service": "Service", "foot_diag": "Diagnose & Reparatur", "foot_calib": "Kalibrierung", "foot_auto": "Automation", "foot_contact": "Kontakt & Anfahrt", "cookie": "Diese Website verwendet Cookies.", "cookie_more": "Mehr erfahren", "cookie_ok": "Annehmen", "opened_mail": "E-Mail-Programm wird geöffnet …", "no_hits": "Keine Treffer für"}, "fr": {"hours": "Lun–Ven 07:30–17:30", "search_ph": "Rechercher un appareil ou procédé (ex. HyperMIG)", "search_btn": "Rechercher", "inquiry": "DEMANDE", "menu_title": "MENU · GAMME MAHE", "m_inquire": "DEMANDER UN TECHNICIEN", "m_all": "TOUS LES APPAREILS", "n_service": "Service", "n_downloads": "Téléchargements", "n_warranty": "Garantie", "n_process": "Procédés", "n_contact": "Contact", "hero_pre": "Votre technicien direct en ", "hero_acc": "soudage & automation.", "hero_lead": "Diagnostic, réparation, calibrage et automation pour postes de soudage et procédés industriels – proche, transparent et attentif à l’électronique.", "hero_cta1": "Demander un technicien →", "hero_cta2": "Voir les systèmes MAHE", "prog_eyebrow": "GAMME D’APPAREILS MAHE", "prog_h2": "Directement au bon procédé.", "prog_sub": "Tous les systèmes MAHE de soudage, découpe, nettoyage et automation dans une vue claire – classés par procédé, comme le soudeur les a en tête. Prix sur demande.", "card_open": "Ouvrir la gamme →", "devices": "appareils", "trust_h3": "EN 1090 · contrôlé & documenté", "trust_p": "Pour les structures porteuses en acier et aluminium, nous fournissons le dossier complet de contrôle et de conformité – adapté à vos installations MAHE.", "dl": "TÉLÉCHARGER", "dl_cat": "Catalogue produits", "dl_cat_p": "Toute la gamme MAHE en PDF.", "svc": "SERVICE", "dl_en": "Demander EN 1090", "dl_en_p": "Dossier de conformité pour votre installation.", "c_home": "Accueil", "c_products": "Produits", "c_search": "Recherche", "chip_all": "Tous", "sec_all": "Tous les appareils", "items": "articles", "poa": "Prix sur demande", "inquire": "Demander +", "techdata": "Données techniques", "poa_sub": "Offre personnalisée avec service suisse & gestion de la garantie.", "to_inquiry": "Ajouter à la demande +", "consult": "Demander conseil", "added": "Ajouté à la liste de demande", "already": "Déjà sur la liste", "cart_title": "Liste de demande", "cart_empty": "Votre liste de demande est vide. Ajoutez des appareils et envoyez une demande groupée.", "f_name": "Nom / Entreprise", "f_mail": "E-mail", "f_msg": "Message (facultatif)", "f_send": "Envoyer la demande →", "k_h1": "Ligne directe avec le technicien.", "k_desc": "Un appareil en panne ou un procédé à accélérer ? Décrivez brièvement votre situation – vous recevrez une première estimation honnête.", "k_tel": "Téléphone", "k_msg": "Votre message", "foot_brand": "Soudage & automation à Bronschhofen. Vente, service et automation pour la gamme MAHE – d’une seule main.", "foot_products": "Produits", "foot_service": "Service", "foot_diag": "Diagnostic & réparation", "foot_calib": "Calibrage", "foot_auto": "Automation", "foot_contact": "Contact & accès", "cookie": "Ce site utilise des cookies.", "cookie_more": "En savoir plus", "cookie_ok": "Accepter", "opened_mail": "Ouverture du logiciel de messagerie …", "no_hits": "Aucun résultat pour"}, "it": {"hours": "Lun–Ven 07:30–17:30", "search_ph": "Cerca apparecchio o processo (es. HyperMIG)", "search_btn": "Cerca", "inquiry": "RICHIESTA", "menu_title": "MENU · GAMMA MAHE", "m_inquire": "RICHIEDI UN TECNICO", "m_all": "TUTTI GLI APPARECCHI", "n_service": "Assistenza", "n_downloads": "Download", "n_warranty": "Garanzia", "n_process": "Processi", "n_contact": "Contatto", "hero_pre": "Il vostro tecnico diretto per ", "hero_acc": "saldatura & automazione.", "hero_lead": "Diagnosi, riparazione, calibrazione e automazione per saldatrici e processi industriali – diretto, trasparente e attento all’elettronica.", "hero_cta1": "Richiedi un tecnico →", "hero_cta2": "Vedi i sistemi MAHE", "prog_eyebrow": "GAMMA APPARECCHI MAHE", "prog_h2": "Direttamente al processo giusto.", "prog_sub": "Tutti i sistemi MAHE di saldatura, taglio, pulizia e automazione in una panoramica chiara – ordinati per processo, come li ha in mente il saldatore. Prezzi su richiesta.", "card_open": "Apri la gamma →", "devices": "apparecchi", "trust_h3": "EN 1090 · controllato & documentato", "trust_p": "Per strutture portanti in acciaio e alluminio forniamo il pacchetto completo di controllo e conformità – adattato ai vostri impianti MAHE.", "dl": "DOWNLOAD", "dl_cat": "Catalogo prodotti", "dl_cat_p": "L’intera gamma MAHE in PDF.", "svc": "ASSISTENZA", "dl_en": "Richiedi EN 1090", "dl_en_p": "Pacchetto di conformità per il vostro impianto.", "c_home": "Home", "c_products": "Prodotti", "c_search": "Ricerca", "chip_all": "Tutti", "sec_all": "Tutti gli apparecchi", "items": "articoli", "poa": "Prezzo su richiesta", "inquire": "Richiedi +", "techdata": "Dati tecnici", "poa_sub": "Offerta personalizzata con servizio svizzero & gestione garanzia.", "to_inquiry": "Aggiungi alla richiesta +", "consult": "Richiedi consulenza", "added": "Aggiunto alla lista richieste", "already": "Già in lista", "cart_title": "Lista richieste", "cart_empty": "La vostra lista richieste è vuota. Aggiungete apparecchi e inviate una richiesta unica.", "f_name": "Nome / Azienda", "f_mail": "E-mail", "f_msg": "Messaggio (facoltativo)", "f_send": "Invia richiesta →", "k_h1": "Linea diretta con il tecnico.", "k_desc": "Un apparecchio in avaria o un processo da velocizzare? Descrivete brevemente la situazione – riceverete una prima valutazione onesta.", "k_tel": "Telefono", "k_msg": "Il vostro messaggio", "foot_brand": "Saldatura & automazione a Bronschhofen. Vendita, assistenza e automazione per la gamma MAHE – da un unico interlocutore.", "foot_products": "Prodotti", "foot_service": "Assistenza", "foot_diag": "Diagnosi & riparazione", "foot_calib": "Calibrazione", "foot_auto": "Automazione", "foot_contact": "Contatto & come arrivare", "cookie": "Questo sito utilizza cookie.", "cookie_more": "Scopri di più", "cookie_ok": "Accetta", "opened_mail": "Apertura del programma di posta …", "no_hits": "Nessun risultato per"}};
const CATTR={"schweissgeraete": {"t": {"fr": "Postes de soudage", "it": "Saldatrici"}, "d": {"fr": "MIG/MAG, TIG, MMA et Plasma-TIG – sources haute performance MAHE avec technologie Upgrade.", "it": "MIG/MAG, TIG, MMA e Plasma-TIG – generatori ad alte prestazioni MAHE con tecnologia Upgrade."}}, "plasmaschneiden": {"t": {"fr": "Découpe plasma", "it": "Taglio al plasma"}, "d": {"fr": "Inverters de découpe plasma Theta, technologie HSC – de 15 à 80 mm, versions manuelle et automation.", "it": "Inverter di taglio plasma Theta, tecnologia HSC – da 15 a 80 mm, versioni manuale e automazione."}}, "reinigung": {"t": {"fr": "Appareils de nettoyage", "it": "Apparecchi di pulizia"}, "d": {"fr": "Nettoyage et polissage électrolytiques des soudures, marquage du métal et dosage automatique.", "it": "Pulizia e lucidatura elettrolitica delle saldature, marcatura del metallo e dosaggio automatico."}}, "zubehoer": {"t": {"fr": "Accessoires", "it": "Accessori"}, "d": {"fr": "Chariots, refroidissement, dévidoirs, télécommandes et équipement d’atelier – adaptés à chaque série MAHE.", "it": "Carrelli, raffreddamento, trainafili, telecomandi e attrezzatura d’officina – per ogni serie MAHE."}}};
const SUBTR={"WIG / TIG": {"fr": "TIG", "it": "TIG"}, "Cleaner": {"fr": "Nettoyage", "it": "Pulizia"}, "Signiergeräte": {"fr": "Marquage", "it": "Marcatura"}, "Dosiersystem": {"fr": "Dosage", "it": "Dosaggio"}, "Fahrwagen": {"fr": "Chariots", "it": "Carrelli"}, "Wasserkühlung": {"fr": "Refroidissement", "it": "Raffreddamento"}, "Drahtvorschubkoffer": {"fr": "Dévidoirs", "it": "Trainafili"}, "Fernbedienungen": {"fr": "Télécommandes", "it": "Telecomandi"}, "Werkstattausrüstung": {"fr": "Équipement atelier", "it": "Attrezzatura officina"}, "Theta Automation": {"fr": "Theta Automation", "it": "Theta Automation"}};
const PDESC={"hypermig-x": {"fr": "Série pulsée MIG/MAG complète avec HyperForce et soudage sans projections MIS.", "it": "Serie pulsata MIG/MAG completa con HyperForce e saldatura senza spruzzi MIS."}, "ecomig": {"fr": "Poste MIG/MAG à réglage continu, ultra-compact et simple d’utilisation.", "it": "Saldatrice MIG/MAG a regolazione continua, ultracompatta e semplice."}, "mms": {"fr": "Poste MIG/MAG mobile et léger pour le montage et l’atelier.", "it": "Saldatrice MIG/MAG mobile e leggera per montaggio e officina."}, "omega-ax": {"fr": "Poste TIG AC/DC mobile pour l’aluminium et l’acier.", "it": "Saldatrice TIG AC/DC mobile per alluminio e acciaio."}, "beta-dx": {"fr": "Poste TIG DC mobile pour acier et acier inox.", "it": "Saldatrice TIG DC mobile per acciaio e acciaio inox."}, "hypertig-ax": {"fr": "Source TIG AC/DC puissante pour l’usage industriel.", "it": "Generatore TIG AC/DC potente per l’uso industriale."}, "hypertig-dx": {"fr": "Source TIG DC puissante pour un taux de dépôt élevé.", "it": "Generatore TIG DC potente per elevata resa."}, "beta-digital": {"fr": "Poste TIG numérique mobile avec mémoire de programmes.", "it": "Saldatrice TIG digitale mobile con memoria programmi."}, "hypertig-acdc": {"fr": "Source AC/DC puissante pour les exigences les plus élevées.", "it": "Generatore AC/DC potente per le massime esigenze."}, "i-1600": {"fr": "Onduleur à électrode robuste et simple d’utilisation.", "it": "Inverter a elettrodo robusto e semplice da usare."}, "delta": {"fr": "Onduleur à électrode multifonction pour atelier et chantier.", "it": "Inverter a elettrodo multifunzione per officina e cantiere."}, "delta-digital": {"fr": "Onduleur multifonction numérique pour les professionnels.", "it": "Inverter multifunzione digitale per professionisti."}, "delta-digital-ds": {"fr": "Source multiprocédé conçue pour le soudage sous-marin.", "it": "Generatore multiprocesso per la saldatura subacquea."}, "plasma-tig": {"fr": "Source microplasma et plasma pour les soudures les plus fines.", "it": "Generatore microplasma e plasma per saldature finissime."}, "theta-40": {"fr": "Découpeur plasma léger 230 V pour l’atelier.", "it": "Tagliatrice al plasma leggera 230 V per l’officina."}, "theta-60": {"fr": "Découpeur plasma puissant avec technologie HSC.", "it": "Inverter plasma potente con tecnologia HSC."}, "theta-120": {"fr": "Découpeur plasma industriel avec technologie HSC.", "it": "Inverter plasma industriale con tecnologia HSC."}, "theta-180": {"fr": "Le découpeur plasma Theta le plus puissant, technologie HSC.", "it": "L’inverter plasma Theta più potente, tecnologia HSC."}, "minicleaner": {"fr": "Onduleur économique, spécialement conçu pour la mobilité.", "it": "Inverter economico, ideato per l’uso mobile."}, "hypercleaner-st": {"fr": "Onduleur 1200 W puissant pour d’excellents résultats de nettoyage.", "it": "Inverter 1200 W potente per risultati di pulizia eccellenti."}, "hypercleaner-speed": {"fr": "Onduleur 2500 W puissant pour un nettoyage rapide.", "it": "Inverter 2500 W potente per una pulizia rapida."}, "hypercleaner-plus": {"fr": "Onduleur 4000 W puissant pour l’usage industriel.", "it": "Inverter 4000 W potente per l’uso industriale."}, "hypercleaner-ct200": {"fr": "Appareil combiné de soudage TIG et de nettoyage.", "it": "Apparecchio combinato di saldatura TIG e pulizia."}, "stt30": {"fr": "Chariot avec support de bouteille pour appareils TIG et MIG.", "it": "Carrello con supporto bombola per apparecchi TIG e MIG."}, "stt35": {"fr": "Chariot sans support de bouteille pour MMA et plasma.", "it": "Carrello senza supporto bombola per MMA e plasma."}, "mpf02": {"fr": "Chariot avec support de bouteille pour tous les appareils portables.", "it": "Carrello con supporto bombola per tutti gli apparecchi portatili."}, "mhct01": {"fr": "Chariot spécialement conçu pour les appareils de nettoyage.", "it": "Carrello specifico per apparecchi di pulizia."}, "wk200": {"fr": "Refroidisseur universel avec prise 230 V et coupure manque d’eau.", "it": "Refrigeratore universale con presa 230 V e spegnimento mancanza acqua."}, "wk300": {"fr": "Refroidisseur à eau pour la série MMS 3000.", "it": "Refrigeratore ad acqua per la serie MMS 3000."}, "wk350": {"fr": "Refroidisseur à eau pour Beta digital et la ligne Omega 400 V.", "it": "Refrigeratore ad acqua per Beta digital e la linea Omega 400 V."}, "dvs410": {"fr": "Dévidoir léger pour la série HyperMIG X.", "it": "Trainafilo leggero per la serie HyperMIG X."}, "dvl420": {"fr": "Dévidoir horizontal tout métal pour la série HyperMIG X.", "it": "Trainafilo orizzontale tutto metallo per la serie HyperMIG X."}, "frc5": {"fr": "Commande à pédale pour tous les appareils TIG MAHE.", "it": "Comando a pedale per tutti gli apparecchi TIG MAHE."}, "rc5": {"fr": "Télécommande manuelle pour tous les appareils TIG et MMA MAHE.", "it": "Telecomando manuale per tutti gli apparecchi TIG e MMA MAHE."}, "rc15": {"fr": "Télécommande manuelle avec touches Up/Down et Start/Stop.", "it": "Telecomando manuale con tasti Up/Down e Start/Stop."}, "rc100": {"fr": "Télécommande manuelle pour tous les appareils TIG et MMA MAHE.", "it": "Telecomando manuale per tutti gli apparecchi TIG e MMA MAHE."}, "rc100ds": {"fr": "Télécommande manuelle spéciale pour les machines Delta Digital DS.", "it": "Telecomando manuale specifico per le macchine Delta Digital DS."}, "theta-60-aut": {"fr": "Découpeur plasma d’automation, technologie HSC, pour intégration machine.", "it": "Inverter plasma per automazione, tecnologia HSC, per integrazione macchina."}, "theta-120-aut": {"fr": "Découpeur plasma d’automation, technologie HSC, pour intégration machine.", "it": "Inverter plasma per automazione, tecnologia HSC, per integrazione macchina."}, "hcs1": {"fr": "Appareil de marquage électrolytique économique, pour la mobilité.", "it": "Marcatore elettrolitico economico, per l’uso mobile."}, "mlf100": {"fr": "Appareil de dosage automatique du liquide de nettoyage.", "it": "Apparecchio per il dosaggio automatico del liquido di pulizia."}, "mcu1": {"fr": "Calibrateur MAHE pour calibrage et validation, grands affichages Volt/Ampère.", "it": "Calibratore MAHE per calibrazione e validazione, ampi display Volt/Ampere."}, "usb2in1": {"fr": "Programmateur pour micro-contrôleurs et interfaces MAHE, logiciel USB inclus.", "it": "Programmatore per microcontrollori e interfacce MAHE, software USB incluso."}};
const SPECK={"Antrieb": {"fr": "Entraînement", "it": "Trazione"}, "Anzeige": {"fr": "Affichage", "it": "Display"}, "Ausführung": {"fr": "Version", "it": "Versione"}, "Bauart": {"fr": "Type", "it": "Tipo"}, "Bedienung": {"fr": "Commande", "it": "Comando"}, "Betriebsart": {"fr": "Mode", "it": "Modalità"}, "Doppelpuls": {"fr": "Double pulsation", "it": "Doppio impulso"}, "Einsatz": {"fr": "Application", "it": "Impiego"}, "Funktion": {"fr": "Fonction", "it": "Funzione"}, "Für": {"fr": "Pour", "it": "Per"}, "Gasflasche": {"fr": "Bouteille de gaz", "it": "Bombola gas"}, "Gehäuse": {"fr": "Boîtier", "it": "Struttura"}, "Gewicht": {"fr": "Poids", "it": "Peso"}, "Kombi": {"fr": "Combi", "it": "Combi"}, "Kühlung": {"fr": "Refroidissement", "it": "Raffreddamento"}, "Leistung": {"fr": "Puissance", "it": "Potenza"}, "Lieferung": {"fr": "Livraison", "it": "Fornitura"}, "Maße (LxBxH)": {"fr": "Dimensions (LxlxH)", "it": "Dimensioni (LxPxA)"}, "Medium": {"fr": "Fluide", "it": "Fluido"}, "Netz": {"fr": "Réseau", "it": "Rete"}, "Schneidleistung": {"fr": "Capacité de coupe", "it": "Capacità di taglio"}, "Schnittstelle": {"fr": "Interface", "it": "Interfaccia"}, "Schutz": {"fr": "Protection", "it": "Protezione"}, "Serie": {"fr": "Série", "it": "Serie"}, "Software": {"fr": "Logiciel", "it": "Software"}, "Speicher": {"fr": "Mémoire", "it": "Memoria"}, "Steckdose": {"fr": "Prise", "it": "Presa"}, "Strombereich": {"fr": "Plage de courant", "it": "Gamma di corrente"}, "Technologie": {"fr": "Technologie", "it": "Tecnologia"}, "Typ": {"fr": "Type", "it": "Tipo"}, "Verfahren": {"fr": "Procédé", "it": "Processo"}, "Werkstoff": {"fr": "Matériau", "it": "Materiale"}, "Zündung": {"fr": "Amorçage", "it": "Innesco"}};
const SPECV={"4-Rollen": {"fr": "4 galets", "it": "4 rulli"}, "Chromstahl": {"fr": "acier inox", "it": "acciaio inox"}, "Controller-Programmierung": {"fr": "programmation de contrôleur", "it": "programmazione controller"}, "Digital oder Analog": {"fr": "numérique ou analogique", "it": "digitale o analogico"}, "Elektrolyt-Reinigung": {"fr": "nettoyage électrolytique", "it": "pulizia elettrolitica"}, "Elektrolyt-Signieren": {"fr": "marquage électrolytique", "it": "marcatura elettrolitica"}, "Feinblech bis Industrie": {"fr": "tôle fine à industrie", "it": "lamiera fine a industria"}, "Fussfernregler": {"fr": "commande à pédale", "it": "comando a pedale"}, "Handfernregler": {"fr": "télécommande manuelle", "it": "telecomando manuale"}, "HyperCleaner-Serie": {"fr": "série HyperCleaner", "it": "serie HyperCleaner"}, "JOB-Programme": {"fr": "programmes JOB", "it": "programmi JOB"}, "Kalibrieren / Validieren": {"fr": "calibrage / validation", "it": "calibrazione / validazione"}, "Kompakt/fahrbar": {"fr": "compact / mobile", "it": "compatto / mobile"}, "MIG/MAG · Puls · MMA · WIG": {"fr": "MIG/MAG · pulsé · MMA · TIG", "it": "MIG/MAG · pulsato · MMA · TIG"}, "MMA (Elektrode)": {"fr": "MMA (électrode)", "it": "MMA (elettrodo)"}, "MMA · Unterwasser": {"fr": "MMA · sous-marin", "it": "MMA · subacqueo"}, "MMA · WIG": {"fr": "MMA · TIG", "it": "MMA · TIG"}, "MMA · WIG-Lift": {"fr": "MMA · TIG-Lift", "it": "MMA · TIG-Lift"}, "Montage / Werkstatt": {"fr": "montage / atelier", "it": "montaggio / officina"}, "Plasma / Mikroplasma": {"fr": "plasma / microplasma", "it": "plasma / microplasma"}, "Plasmaschneiden": {"fr": "découpe plasma", "it": "taglio al plasma"}, "Plasmaschneiden · Automation": {"fr": "découpe plasma · automation", "it": "taglio plasma · automazione"}, "Reinigungsflüssigkeit": {"fr": "liquide de nettoyage", "it": "liquido di pulizia"}, "Set mit Koffer": {"fr": "kit avec mallette", "it": "set con valigetta"}, "Universalkühler": {"fr": "refroidisseur universel", "it": "refrigeratore universale"}, "Vollmetall": {"fr": "tout métal", "it": "tutto metallo"}, "Volt & Ampere (gross)": {"fr": "Volt & Ampère (grand)", "it": "Volt & Ampere (grande)"}, "WIG + Reinigung": {"fr": "TIG + nettoyage", "it": "TIG + pulizia"}, "WIG AC/DC": {"fr": "TIG AC/DC", "it": "TIG AC/DC"}, "WIG DC": {"fr": "TIG DC", "it": "TIG DC"}, "Wasserkühlgerät": {"fr": "refroidisseur à eau", "it": "refrigeratore ad acqua"}, "Wassermangel-Abschaltung": {"fr": "coupure manque d’eau", "it": "spegnimento mancanza acqua"}, "als Set": {"fr": "en kit", "it": "in set"}, "automatische Dosierung": {"fr": "dosage automatique", "it": "dosaggio automatico"}, "digital": {"fr": "numérique", "it": "digitale"}, "einfach": {"fr": "simple", "it": "semplice"}, "horizontal": {"fr": "horizontal", "it": "orizzontale"}, "inklusive": {"fr": "inclus", "it": "incluso"}, "ja": {"fr": "oui", "it": "sì"}, "nein": {"fr": "non", "it": "no"}, "leicht / tragbar": {"fr": "léger / portable", "it": "leggero / portatile"}, "luft-/wassergekühlt": {"fr": "refroidi air/eau", "it": "raffreddato aria/acqua"}, "mobil": {"fr": "mobile", "it": "mobile"}, "tragbar": {"fr": "portable", "it": "portatile"}, "wassergekühlt": {"fr": "refroidi par eau", "it": "raffreddato ad acqua"}, "wassergekühlt (CWK)": {"fr": "refroidi par eau (CWK)", "it": "raffreddato ad acqua (CWK)"}, "CNC / Automation": {"fr": "CNC / automation", "it": "CNC / automazione"}, "MAHE WIG": {"fr": "MAHE TIG", "it": "MAHE TIG"}, "MAHE WIG · MMA": {"fr": "MAHE TIG · MMA", "it": "MAHE TIG · MMA"}, "MMS 3000 Serie": {"fr": "série MMS 3000", "it": "serie MMS 3000"}, "Montage/Werkstatt": {"fr": "montage / atelier", "it": "montaggio / officina"}};
Object.assign(SUBTR,{'Elektrolyte':{fr:'Électrolytes',it:'Elettroliti'},'Kabel':{fr:'Câbles',it:'Cavi'},'Brenner':{fr:'Torches',it:'Torce'}});
Object.assign(SPECK,{'Gebinde':{fr:'Conditionnement',it:'Confezione'},'Querschnitt':{fr:'Section',it:'Sezione'},'Längen':{fr:'Longueurs',it:'Lunghezze'},'Farbe':{fr:'Couleur',it:'Colore'},'Anwendung':{fr:'Application',it:'Applicazione'},'Sicherheitsdatenblatt':{fr:'Fiche de sécurité',it:'Scheda di sicurezza'}});
Object.assign(SPECV,{'Edelstahl':{fr:'acier inox',it:'acciaio inox'},'blau':{fr:'bleu',it:'blu'},'schwarz':{fr:'noir',it:'nero'}});
Object.assign(PDESC,{'r1':{fr:'Électrolyte de nettoyage rapide pour soudures inox.',it:'Elettrolita di pulizia rapida per saldature inox.'},'rp1':{fr:'Électrolyte de nettoyage pâteux pour surfaces verticales.',it:'Elettrolita di pulizia pastoso per superfici verticali.'},'p1':{fr:'Électrolyte d\u2019électropolissage et de décapage de l\u2019inox.',it:'Elettrolita per elettrolucidatura e decapaggio inox.'},'n1':{fr:'Neutralisant pour stopper et neutraliser après nettoyage.',it:'Neutralizzante per arrestare e neutralizzare dopo la pulizia.'},'m1':{fr:'Électrolyte pour le marquage électrochimique du métal.',it:'Elettrolita per la marcatura elettrochimica del metallo.'},'elektrodenkabel':{fr:'Câble d\u2019électrode pour appareils Cleaner et MMA.',it:'Cavo elettrodo per apparecchi Cleaner e MMA.'},'massekabel':{fr:'Câble de masse avec pince pour Cleaner et MMA.',it:'Cavo di massa con morsetto per Cleaner e MMA.'}});
Object.assign(UI.de,{verf_h1:'MAHE Schweissverfahren',verf_sub:'Die MAHE-Prozesse im Überblick – für tiefen Einbrand, saubere Wurzeln und minimalen Verzug.',dl_h1:'Downloads',dl_sub:'Produktkatalog, Konformitätszertifikat und Sicherheitsdatenblätter der Elektrolyte.'});Object.assign(UI.fr,{verf_h1:'Procédés de soudage MAHE',verf_sub:'Les procédés MAHE en un coup d’œil – pénétration profonde, racines propres, déformation minimale.',dl_h1:'Téléchargements',dl_sub:'Catalogue produits, certificat de conformité et fiches de sécurité des électrolytes.'});Object.assign(UI.it,{verf_h1:'Processi di saldatura MAHE',verf_sub:'I processi MAHE in sintesi – penetrazione profonda, radici pulite, minima deformazione.',dl_h1:'Download',dl_sub:'Catalogo prodotti, certificato di conformità e schede di sicurezza degli elettroliti.'});Object.assign(UI.de,{front_h:'Fronteingabesystem',front_bes:'Besonderheiten'});Object.assign(UI.fr,{front_h:'Interface de commande',front_bes:'Points forts'});Object.assign(UI.it,{front_h:'Interfaccia di comando',front_bes:'Punti di forza'});function t(k){return (UI[LANG]&&UI[LANG][k])||UI.de[k]||k;}
function catT(c){return LANG!=='de'&&CATTR[c.id]?CATTR[c.id].t[LANG]:c.t;}
function catD(c){return LANG!=='de'&&CATTR[c.id]?CATTR[c.id].d[LANG]:c.d;}
function subT(n){return LANG!=='de'&&SUBTR[n]?SUBTR[n][LANG]:n;}
function pDesc(p){return LANG!=='de'&&PDESC[p.id]?PDESC[p.id][LANG]:p.desc;}
function trK(k){return LANG!=='de'&&SPECK[k]?SPECK[k][LANG]:k;}
function trV(v){if(LANG==='de')return v; if(SPECV[v])return SPECV[v][LANG]; if(v.indexOf('bis ')===0)return (LANG==='fr'?'jusqu\u2019à ':'fino a ')+v.slice(4); return v;}

Object.assign(UI.de,{availability:'Verfügbarkeit',avail_val:'Auf Anfrage',brand:'Marke',artno:'Art.-Nr.',tab_tech:'Technische Daten',tab_feat:'Fronteingabe',controls:'Bedienelemente',tab_acc:'Passendes Zubehör',tab_dl:'Downloads',panel_h:'Fronteingabe & Bedienung',panel_p:'Klare Fronteingabe mit VOLT/AMP-Anzeige, JOB-Speicher und direkter Parameterwahl – je nach Modell analog oder digital.',no_acc:'Für dieses Gerät ist kein spezifisches Zubehör hinterlegt.',dl_datasheet:'Datenblatt',dl_manual:'Bedienungsanleitung',dl_soon:'Dokument im Live-Betrieb verknüpfen',highlights:'Besonderheiten'});
Object.assign(UI.fr,{availability:'Disponibilité',avail_val:'Sur demande',brand:'Marque',artno:'Réf.',tab_tech:'Données techniques',tab_feat:'Interface',controls:'Éléments de commande',tab_acc:'Accessoires compatibles',tab_dl:'Téléchargements',panel_h:'Interface & commande',panel_p:'Interface claire avec affichage VOLT/AMP, mémoire JOB et sélection directe des paramètres – analogique ou numérique selon le modèle.',no_acc:'Aucun accessoire spécifique enregistré pour cet appareil.',dl_datasheet:'Fiche technique',dl_manual:'Notice d’utilisation',dl_soon:'Document à lier en production',highlights:'Points forts'});
Object.assign(UI.it,{availability:'Disponibilità',avail_val:'Su richiesta',brand:'Marca',artno:'Cod. art.',tab_tech:'Dati tecnici',tab_feat:'Interfaccia',controls:'Elementi di comando',tab_acc:'Accessori compatibili',tab_dl:'Download',panel_h:'Interfaccia & comando',panel_p:'Interfaccia chiara con display VOLT/AMP, memoria JOB e selezione diretta dei parametri – analogica o digitale secondo il modello.',no_acc:'Nessun accessorio specifico registrato per questo apparecchio.',dl_datasheet:'Scheda tecnica',dl_manual:'Manuale d’uso',dl_soon:'Documento da collegare in produzione',highlights:'Punti di forza'});




/* ---------- Verfahren & Downloads ---------- */
const PROC=[
 {ic:'mig',n:{de:'MIS – Spritzerfrei',fr:'MIS – sans projections',it:'MIS – senza spruzzi'},d:{de:'Nahezu spritzerfreier Lichtbogen mit sehr guter Flanken- und Wurzelerfassung – wenig Nacharbeit.',fr:'Arc quasi sans projections, excellente accroche des flancs et de la racine – peu de reprise.',it:'Arco quasi senza spruzzi, ottima presa su fianchi e radice – poca ripresa.'}},
 {ic:'doppelpuls',n:{de:'Doppelpuls',fr:'Double pulsation',it:'Doppio impulso'},d:{de:'Automatisierter Impulslichtbogen mit WIG-Naht-Optik und einstellbarer Schuppung – ideal für Aluminium.',fr:'Arc pulsé automatisé, aspect TIG et cadence réglable – idéal pour l’aluminium.',it:'Arco pulsato automatizzato, estetica TIG e cadenza regolabile – ideale per l’alluminio.'}},
 {ic:'puls',n:{de:'HyperPuls',fr:'HyperPuls',it:'HyperPuls'},d:{de:'Dynamischer Impulslichtbogen für mehr Produktivität: schneller schweissen, weniger Verzug, ideal für Mehrlagen.',fr:'Arc pulsé dynamique pour plus de productivité : plus rapide, moins de déformation, idéal multipasse.',it:'Arco pulsato dinamico per più produttività: più veloce, meno deformazione, ideale multipasso.'}},
 {ic:'synergy',n:{de:'HyperForce',fr:'HyperForce',it:'HyperForce'},d:{de:'Tief eindringender, druckvoller Lichtbogen mit tiefem Einbrand und perfekter Schweissbadkontrolle.',fr:'Arc puissant et pénétrant, forte pénétration et contrôle parfait du bain.',it:'Arco potente e penetrante, forte penetrazione e controllo perfetto del bagno.'}},
 {ic:'h2o',n:{de:'HyperCold',fr:'HyperCold',it:'HyperCold'},d:{de:'Geringste Wärmeeinbringung – ideal für spaltüberbrückendes, verzugsarmes Schweissen an Dünnblech.',fr:'Apport de chaleur minimal – idéal pour ponter les jeux et souder la tôle fine sans déformation.',it:'Minimo apporto termico – ideale per ponti sui giochi e lamiera fine senza deformazioni.'}},
 {ic:'lift',n:{de:'HyperRoot',fr:'HyperRoot',it:'HyperRoot'},d:{de:'Sichere, kontrollierte Wurzelschweissung mit sauberer Nahtunterseite – auch bei grösseren Spalten.',fr:'Soudage de racine sûr et contrôlé, envers propre – même sur jeux importants.',it:'Saldatura di radice sicura e controllata, rovescio pulito – anche con giochi ampi.'}},
 {ic:'auto',n:{de:'HyperUP',fr:'HyperUP',it:'HyperUP'},d:{de:'Optimiertes Steignahtschweissen (vertikal aufwärts) mit stabiler Schmelzbadkontrolle.',fr:'Soudage en montée (vertical up) optimisé, contrôle stable du bain.',it:'Saldatura in verticale ascendente ottimizzata, controllo stabile del bagno.'}}
];
const DLS=[
 {k:'PDF',t:{de:'Produktkatalog 2023',fr:'Catalogue produits 2023',it:'Catalogo prodotti 2023'},s:{de:'Das komplette MAHE-Geräteprogramm',fr:'Toute la gamme MAHE',it:'L’intera gamma MAHE'},u:'https://mahe-online.de/wp-content/uploads/2023/06/Katalog_2023_opt.pdf'},
 {k:'PDF',t:{de:'EN 1090 Konformitätszertifikat',fr:'Certificat de conformité EN 1090',it:'Certificato di conformità EN 1090'},s:{de:'Konformitätserklärung',fr:'Déclaration de conformité',it:'Dichiarazione di conformità'},u:'http://mahe-online.de/welding/pdf/de/Mahe_Konformations_Zertifikat.pdf'},
 {k:'R1',t:{de:'Sicherheitsdatenblatt Reinigungselektrolyt R1',fr:'Fiche de sécurité électrolyte R1',it:'Scheda di sicurezza elettrolita R1'},s:{de:'HyClean Rapid R1',fr:'HyClean Rapid R1',it:'HyClean Rapid R1'},u:'http://mahe-online.de/welding/pdf/de/HyCleanRapid_R1_DE.pdf'},
 {k:'RP1',t:{de:'Sicherheitsdatenblatt Reinigungselektrolyt RP1',fr:'Fiche de sécurité électrolyte RP1',it:'Scheda di sicurezza elettrolita RP1'},s:{de:'HyClean RP1 Pastös',fr:'HyClean RP1',it:'HyClean RP1'},u:'http://mahe-online.de/welding/pdf/de/HyClean_RP1_DE.pdf'},
 {k:'P1',t:{de:'Sicherheitsdatenblatt Polierelektrolyt P1',fr:'Fiche de sécurité électrolyte P1',it:'Scheda di sicurezza elettrolita P1'},s:{de:'HyCleanPolish P1',fr:'HyCleanPolish P1',it:'HyCleanPolish P1'},u:'http://mahe-online.de/welding/pdf/de/HyCleanPolish_%20P1_DE.pdf'},
 {k:'M1',t:{de:'Sicherheitsdatenblatt Signierelektrolyt M1',fr:'Fiche de sécurité électrolyte M1',it:'Scheda di sicurezza elettrolita M1'},s:{de:'Signierelektrolyt M1',fr:'Électrolyte de marquage M1',it:'Elettrolita di marcatura M1'},u:'http://mahe-online.de/welding/pdf/de/Signierelektrolyt_M1_DE.pdf'},
 {k:'N1',t:{de:'Sicherheitsdatenblatt Neutralisierer N1',fr:'Fiche de sécurité neutralisant N1',it:'Scheda di sicurezza neutralizzante N1'},s:{de:'Neutralyt N1',fr:'Neutralyt N1',it:'Neutralyt N1'},u:'http://mahe-online.de/welding/pdf/de/Neutralyt_N1_DE.pdf'}
];
function renderVerfahren(){
 var g=document.getElementById('procGrid');if(!g)return;g.innerHTML='';
 PROC.forEach(function(p,i){var el=document.createElement('div');el.className='srv';
  el.innerHTML='<div class="no">0'+(i+1)+'</div><div class="pic">'+FEAT[p.ic].svg+'</div><h3>'+(p.n[LANG]||p.n.de)+'</h3><p>'+(p.d[LANG]||p.d.de)+'</p><div class="bar"></div>';
  g.appendChild(el);});
}
function renderDownloads(){
 var g=document.getElementById('dlList');if(!g)return;g.innerHTML='';
 DLS.forEach(function(d){var a=document.createElement('a');a.className='dlitem';a.href=d.u;a.target='_blank';a.rel='noopener';
  a.innerHTML='<div class="ico">'+d.k+'</div><div class="nm">'+(d.t[LANG]||d.t.de)+'<span>'+(d.s[LANG]||d.s.de)+'</span></div><span class="arw">↓</span>';
  g.appendChild(a);});
}

/* ---------- Verfahren-Symbole & Zubehör ---------- */
const FEAT={
 mma:{tile:true,svg:'<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="11" fill="#23457f"/><line x1="10" y1="38" x2="26" y2="22" stroke="#fff" stroke-width="3" stroke-linecap="round"/><rect x="24.5" y="16" width="10" height="5" rx="2" transform="rotate(45 29.5 18.5)" fill="none" stroke="#fff" stroke-width="3"/><path d="M33 13 l2 4 4-2" fill="none" stroke="#ff5a3c" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',de:'MMA',fr:'MMA',it:'MMA'},
 mig:{tile:true,svg:'<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="11" fill="#23457f"/><path d="M11 18 h10 v9 h-4 v9 h-6 z" fill="#fff"/><path d="M21 20 h6 a6 6 0 0 1 6 6 v0 h-3.5 a3 3 0 0 0-3-2.6 H21 z" fill="#fff"/><rect x="31" y="26" width="9" height="3.4" rx="1.2" transform="rotate(42 35 27.7)" fill="#fff"/><path d="M37 33 l3.6 .5 -.5 3.6" fill="none" stroke="#ff5a3c" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',de:'MIG/MAG',fr:'MIG/MAG',it:'MIG/MAG'},
 wig:{tile:true,svg:'<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="11" fill="#23457f"/><path d="M17 11 h14 l-2.4 10 h-9.2 z" fill="#fff"/><rect x="22.4" y="21" width="3.2" height="9" fill="#fff"/><path d="M21.6 30 L24 36.5 L26.4 30 Z" fill="#fff"/><line x1="16" y1="40" x2="32" y2="40" stroke="#ff5a3c" stroke-width="3.4" stroke-linecap="round"/></svg>',de:'WIG/TIG',fr:'TIG',it:'TIG'},
 hf:{tile:true,svg:'<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="11" fill="#23457f"/><path d="M28 8 L16 26 L23 26 L19 40 L34 22 L27 22 L31 8 Z" fill="#ff5a3c" stroke="#fff" stroke-width="1.4" stroke-linejoin="round"/></svg>',de:'HF-Zündung',fr:'Amorçage HF',it:'Innesco HF'},
 lift:{tile:true,svg:'<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="11" fill="#23457f"/><path d="M13 35 h22" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><path d="M24 31 V13" fill="none" stroke="#ff5a3c" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><path d="M18 19 l6 -6 6 6" fill="none" stroke="#ff5a3c" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',de:'Lift Arc',fr:'Lift Arc',it:'Lift Arc'},
 puls:{tile:true,svg:'<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="11" fill="#23457f"/><path d="M8 31 h6 v-14 h6 v14 h6 v-14 h6 v14 h4" fill="none" stroke="#ff5a3c" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',de:'Puls',fr:'Pulsé',it:'Pulsato'},
 doppelpuls:{tile:true,svg:'<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="11" fill="#23457f"/><path d="M7 31 h4 v-11 h4 v11 h4" fill="none" stroke="#ff5a3c" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><path d="M24 31 h4 v-11 h4 v11 h4" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',de:'Doppelpuls',fr:'Double puls.',it:'Doppio imp.'},
 plasma:{tile:true,svg:'<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="11" fill="#23457f"/><path d="M16 10 h16 l-4 12 h-8 z" fill="none" stroke="#fff" stroke-width="3" stroke-linejoin="round"/><path d="M24 22 L19 33 h4 l-2 7 8-12 h-4 l3-5 z" fill="#ff5a3c"/></svg>',de:'Plasma',fr:'Plasma',it:'Plasma'},
 h2o:{tile:true,svg:'<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="11" fill="#23457f"/><path d="M24 10 C24 10 15 20 15 28 a9 9 0 0 0 18 0 C33 20 24 10 24 10 z" fill="none" stroke="#fff" stroke-width="3"/><path d="M20 29 a4 4 0 0 0 4 4" fill="none" stroke="#ff5a3c" stroke-width="2.9" stroke-linecap="round" stroke-linejoin="round"/></svg>',de:'Wasserkühlung',fr:'Refroid. eau',it:'Raffr. acqua'},
 synergy:{tile:true,svg:'<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="11" fill="#23457f"/><path d="M13 21 a12 12 0 0 1 20 -3" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><path d="M33 11 v7 h-7" fill="none" stroke="#ff5a3c" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><path d="M35 27 a12 12 0 0 1 -20 3" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><path d="M15 37 v-7 h7" fill="none" stroke="#ff5a3c" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',de:'Synergie',fr:'Synergie',it:'Sinergia'},
 display:{tile:true,svg:'<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="11" fill="#23457f"/><rect x="11" y="14" width="26" height="16" rx="2" fill="none" stroke="#fff" stroke-width="3"/><path d="M16 20 h9 M16 25 h13" fill="none" stroke="#ff5a3c" stroke-width="2.9" stroke-linecap="round" stroke-linejoin="round"/><path d="M20 34 h8" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',de:'Digital-Display',fr:'Écran num.',it:'Display'},
 rollen:{tile:true,svg:'<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="11" fill="#23457f"/><circle cx="17" cy="18" r="4.4" fill="none" stroke="#fff" stroke-width="3"/><circle cx="31" cy="18" r="4.4" fill="none" stroke="#fff" stroke-width="3"/><circle cx="17" cy="31" r="4.4" fill="none" stroke="#fff" stroke-width="3"/><circle cx="31" cy="31" r="4.4" fill="none" stroke="#fff" stroke-width="3"/><path d="M21.5 18 h5 M21.5 31 h5" fill="none" stroke="#ff5a3c" stroke-width="2.9" stroke-linecap="round" stroke-linejoin="round"/></svg>',de:'4-Rollen',fr:'4 galets',it:'4 rulli'},
 auto:{tile:true,svg:'<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="11" fill="#23457f"/><rect x="15" y="20" width="18" height="13" rx="2.5" fill="none" stroke="#fff" stroke-width="3"/><path d="M24 20 v-5" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><circle cx="24" cy="12.5" r="2.4" fill="#ff5a3c"/><circle cx="20" cy="26.5" r="1.7" fill="#fff"/><circle cx="28" cy="26.5" r="1.7" fill="#fff"/></svg>',de:'Automation',fr:'Automation',it:'Automazione'},
 clean:{tile:true,svg:'<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="11" fill="#23457f"/><path d="M17 12 h14 v7 h-14 z" fill="none" stroke="#fff" stroke-width="3" stroke-linejoin="round"/><path d="M20 19 v16 M24 19 v18 M28 19 v16" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><path d="M34 12 l2 -2 M36 16 l3 -1 M32 9 l1 -3" fill="none" stroke="#ff5a3c" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',de:'Reinigung',fr:'Nettoyage',it:'Pulizia'},
 mark:{tile:true,svg:'<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="11" fill="#23457f"/><path d="M11 34 L26 19 l5 5 L16 39 H11 z" fill="none" stroke="#fff" stroke-width="3" stroke-linejoin="round"/><path d="M26 19 l4 -4 5 5 -4 4" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><path d="M10 39 h9" fill="none" stroke="#ff5a3c" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',de:'Signieren',fr:'Marquage',it:'Marcatura'},
 dose:{tile:true,svg:'<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="11" fill="#23457f"/><path d="M19 10 h10 v4 h-10 z" fill="none" stroke="#fff" stroke-width="3" stroke-linejoin="round"/><path d="M20 14 h8 v7 l3 5 v11 a2 2 0 0 1-2 2 h-10 a2 2 0 0 1-2-2 v-11 l3-5 z" fill="none" stroke="#fff" stroke-width="3" stroke-linejoin="round"/><path d="M21 29 h6" fill="none" stroke="#ff5a3c" stroke-width="2.9" stroke-linecap="round" stroke-linejoin="round"/></svg>',de:'Dosierung',fr:'Dosage',it:'Dosaggio'},
 reinigen:{tile:true,svg:'<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="11" fill="#23457f"/><path d="M0 0 H48 V20 L0 30 Z" fill="#a72b2b"/><g fill="#fff"><rect x="27" y="9" width="5.5" height="15" rx="2" transform="rotate(35 29.7 16.5)"/><path d="M13 35 L21 23 L26 26.3 L18 38.3 Z"/></g></svg>',de:'Reinigen',fr:'Nettoyer',it:'Pulire'},
 beschriften:{tile:true,svg:'<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="11" fill="#23457f"/><path d="M0 0 H48 V20 L0 30 Z" fill="#a72b2b"/><g fill="#fff"><rect x="27" y="9" width="5.5" height="15" rx="2" transform="rotate(35 29.7 16.5)"/><path d="M13 35 L21 23 L26 26.3 L18 38.3 Z"/><circle cx="15.5" cy="36" r="1.7"/></g></svg>',de:'Beschriften',fr:'Marquer',it:'Marcare'},
 polieren:{tile:true,svg:'<svg viewBox="0 0 48 48"><rect width="48" height="48" rx="11" fill="#23457f"/><path d="M0 0 H48 V20 L0 30 Z" fill="#a72b2b"/><g fill="#fff"><rect x="27" y="9" width="5.5" height="15" rx="2" transform="rotate(35 29.7 16.5)"/><path d="M13 35 L21 23 L26 26.3 L18 38.3 Z"/><path d="M33 25 l1 3 3 1 -3 1 -1 3 -1-3 -3-1 3-1 z"/></g></svg>',de:'Polieren',fr:'Polir',it:'Lucidare'}
};
const PANEL_SVG='<svg width="150" height="96" viewBox="0 0 150 96"><rect x="1" y="1" width="148" height="94" rx="6" fill="#202024" stroke="#2A2A2E"/><rect x="14" y="16" width="42" height="22" rx="3" fill="#0C0C0D" stroke="#333"/><rect x="18" y="20" width="34" height="14" rx="2" fill="#3a0d05"/><text x="35" y="31" font-family="Arial" font-size="9" fill="#F1531C" text-anchor="middle">VOLT</text><rect x="94" y="16" width="42" height="22" rx="3" fill="#0C0C0D" stroke="#333"/><rect x="98" y="20" width="34" height="14" rx="2" fill="#3a0d05"/><text x="115" y="31" font-family="Arial" font-size="9" fill="#F1531C" text-anchor="middle">AMP</text><circle cx="35" cy="62" r="11" fill="#151517" stroke="#3a3a3e"/><circle cx="35" cy="62" r="3" fill="#F1531C"/><circle cx="115" cy="62" r="11" fill="#151517" stroke="#3a3a3e"/><circle cx="115" cy="62" r="3" fill="#888"/><rect x="66" y="20" width="18" height="12" rx="2" fill="#151517" stroke="#333"/><rect x="66" y="52" width="18" height="12" rx="2" fill="#151517" stroke="#333"/></svg>';
function featLabel(k){var f=FEAT[k];return f?(f[LANG]||f.de):k;}
function deriveFeat(p){
  var s=(p.vt+' '+p.name+' '+Object.values(p.specs).join(' ')).toLowerCase();var f=[];
  if(/mig/.test(s))f.push('mig');
  if(/mma|elektrode/.test(s))f.push('mma');
  if(/wig|tig/.test(s))f.push('wig');
  if(/doppelpuls/.test(s))f.push('doppelpuls'); else if(/puls/.test(s))f.push('puls');
  if(/plasma/.test(s))f.push('plasma');
  if(/wasser|cwk/.test(s))f.push('h2o');
  if(/synerg/.test(s))f.push('synergy');
  if(/digital/.test(s))f.push('display');
  if(/rollen/.test(s))f.push('rollen');
  if(/automation|cnc/.test(s))f.push('auto');
  if(/reinig|cleaner/.test(s))f.push('clean');
  if(/signier/.test(s))f.push('mark');
  if(/dosier/.test(s))f.push('dose');
  if(p.sub==='WIG / TIG'&&f.indexOf('hf')<0)f.push('hf');
  if((p.sub==='WIG / TIG'||p.sub==='MMA')&&f.indexOf('lift')<0)f.push('lift');
  if(p.cat==='reinigung'){
    if(p.sub==='Cleaner')f=['reinigen','polieren','beschriften'];
    else if(p.id==='p1')f=['polieren'];
    else if(p.id==='m1'||p.sub==='Signiergeräte')f=['beschriften'];
    else f=['reinigen'];
  }
  return f.filter((x,i)=>f.indexOf(x)===i);
}
function isWater(p){return /wasser|cwk|wwk/i.test((p.name+' '+Object.values(p.specs).join(' ')));}
function relatedAcc(p){
 if(p.cat==='zubehoer')return [];
 var ids=[];
 if(p.id==='hypermig-x')ids=['dvs410','dvl420','wk350'];
 else if(p.sub==='MIG / MAG')ids=(p.id==='mms')?['stt30','mpf02','wk300']:['stt30','mpf02','wk200'];
 else if(p.sub==='WIG / TIG')ids=isWater(p)?['wk350','stt30','mpf02','frc5']:['stt30','mpf02','frc5','rc5'];
 else if(p.sub==='MMA')ids=['stt35','mpf02','rc5','rc100'];
 else if(p.sub==='Plasma TIG')ids=['mpf02','rc100'];
 else if(p.cat==='plasmaschneiden')ids=['stt35','mpf02'];
 else if(p.cat==='reinigung'&&p.sub==='Cleaner')ids=['r1','rp1','p1','m1','mhct01','elektrodenkabel'];
 else if(p.cat==='reinigung'&&p.sub==='Elektrolyte')ids=['hypercleaner-st','minicleaner','mhct01'];
 else if(p.cat==='reinigung')ids=['mhct01','r1'];
 return ids.filter(function(id){return P.find(function(x){return x.id===id})}).slice(0,6);
}

/* ---------- Besonderheiten (echte MAHE-Funktionen) & Materialien ---------- */
const HL={
 mig_hyper:{de:['MIG/MAG-Schweissen & MIG-Löten','HyperForce, HyperRoot, HyperCold','HyperPuls & HyperSpeedPuls','Doppelpuls mit WIG-Naht-Optik','MMA-Elektrode & Fugenhobeln','WIG Lift Arc','Digital Synergy geregelt','Spritzerfreier Lichtbogen','4-Rollen-Antrieb','Fernbedienung anschliessbar','JOB-Modus mit 99 Programmen','Upgrade-fähig · 100% recycelbar'],
  fr:['Soudage MIG/MAG & brasage MIG','HyperForce, HyperRoot, HyperCold','HyperPuls & HyperSpeedPuls','Double pulsation, aspect TIG','Électrode MMA & gougeage','TIG Lift Arc','Régulation Digital Synergy','Arc sans projections','Entraînement 4 galets','Télécommande raccordable','Mode JOB, 99 programmes','Évolutif · 100% recyclable'],
  it:['Saldatura MIG/MAG & brasatura MIG','HyperForce, HyperRoot, HyperCold','HyperPuls & HyperSpeedPuls','Doppio impulso, estetica TIG','Elettrodo MMA & scriccatura','TIG Lift Arc','Regolazione Digital Synergy','Arco senza spruzzi','Trazione a 4 rulli','Telecomando collegabile','Modo JOB, 99 programmi','Aggiornabile · 100% riciclabile']},
 mig_std:{de:['Stufenlose MIG/MAG-Regelung','Synergie-Kennlinien','MMA-Elektrode möglich','4-Rollen-Antrieb','Kompakt & fahrbar','Robust für Werkstatt & Montage'],
  fr:['Réglage continu MIG/MAG','Courbes synergiques','Électrode MMA possible','Entraînement 4 galets','Compact & mobile','Robuste atelier & montage'],
  it:['Regolazione continua MIG/MAG','Curve sinergiche','Elettrodo MMA possibile','Trazione a 4 rulli','Compatto & mobile','Robusto per officina & montaggio']},
 wig:{de:['Hochfrequenz-Impulsschweissen','HyperSpot Punktschweissen','ActiveSpot Heftfunktion','Hyper ARC Active Regelung','Mix-TIG-Schweissen','WIG DC & MMA','Strom-Modulation einstellbar','Digitale Anzeige','Fernbedienung','Synergy-Einstellungen','JOB-Modus'],
  fr:['Soudage pulsé haute fréquence','Pointage HyperSpot','Fonction ActiveSpot','Régulation Hyper ARC Active','Soudage Mix-TIG','TIG DC & MMA','Modulation de courant réglable','Affichage numérique','Télécommande','Réglages Synergy','Mode JOB'],
  it:['Saldatura pulsata ad alta frequenza','Puntatura HyperSpot','Funzione ActiveSpot','Regolazione Hyper ARC Active','Saldatura Mix-TIG','TIG DC & MMA','Modulazione di corrente regolabile','Display digitale','Telecomando','Impostazioni Synergy','Modo JOB']},
 wig_acdc:{de:['Hochfrequenz-Impulsschweissen','HyperSpot Punktschweissen','ActiveSpot Heftfunktion','Hyper ARC Active Regelung','Mix-TIG-Schweissen','AC/DC – Aluminium & Stahl','MAHE-MIX-PULSE','Strom-Modulation einstellbar','Digitale Anzeige','Leistungsstarke Wasserkühlung','Fernbedienung','JOB-Modus'],
  fr:['Soudage pulsé haute fréquence','Pointage HyperSpot','Fonction ActiveSpot','Régulation Hyper ARC Active','Soudage Mix-TIG','AC/DC – aluminium & acier','MAHE-MIX-PULSE','Modulation de courant réglable','Affichage numérique','Refroidissement eau puissant','Télécommande','Mode JOB'],
  it:['Saldatura pulsata ad alta frequenza','Puntatura HyperSpot','Funzione ActiveSpot','Regolazione Hyper ARC Active','Saldatura Mix-TIG','AC/DC – alluminio & acciaio','MAHE-MIX-PULSE','Modulazione di corrente regolabile','Display digitale','Raffreddamento ad acqua potente','Telecomando','Modo JOB']},
 mma:{de:['MMA-Elektrodenschweissen','WIG Lift Arc (DC)','Hot-Start – sichere Zündung','Arc Force – stabiler Lichtbogen','Anti-Stick – kein Festkleben','Übertemperaturschutz','Generatortauglich','Robust & einfach zu bedienen'],
  fr:['Soudage à l’électrode MMA','TIG Lift Arc (DC)','Hot-Start – amorçage sûr','Arc Force – arc stable','Anti-Stick – pas de collage','Protection surtempérature','Compatible groupe électrogène','Robuste & simple'],
  it:['Saldatura a elettrodo MMA','TIG Lift Arc (DC)','Hot-Start – innesco sicuro','Arc Force – arco stabile','Anti-Stick – niente incollaggio','Protezione sovratemperatura','Compatibile con generatore','Robusto & semplice']},
 plasmatig:{de:['Mikroplasma- & Plasma-Schweissen','Feinste Schweissungen ab geringstem Strom','Stabiler, gebündelter Plasmastrahl','Für Feinblech bis Industrie','HF-Zündung','Pilotlichtbogen'],
  fr:['Soudage microplasma & plasma','Soudures très fines dès un courant minimal','Jet plasma stable et concentré','Tôle fine à industrie','Amorçage HF','Arc pilote'],
  it:['Saldatura microplasma & plasma','Saldature finissime da corrente minima','Getto plasma stabile e concentrato','Lamiera fine a industria','Innesco HF','Arco pilota']},
 theta:{de:['Plasmaschneiden mit HSC-Technologie','Sauberer, schneller Trennschnitt','Pilotlichtbogen – kontaktloses Zünden','Für alle leitenden Metalle','Gittertrennen möglich','Digitale Anzeige','Übertemperaturschutz','Hand- oder Automationsbetrieb'],
  fr:['Découpe plasma technologie HSC','Coupe nette et rapide','Arc pilote – amorçage sans contact','Tous métaux conducteurs','Découpe de grilles possible','Affichage numérique','Protection surtempérature','Mode manuel ou automation'],
  it:['Taglio plasma tecnologia HSC','Taglio netto e veloce','Arco pilota – innesco senza contatto','Tutti i metalli conduttivi','Taglio di grigliati possibile','Display digitale','Protezione sovratemperatura','Modo manuale o automazione']},
 cleaner:{de:['Elektrolytisches Reinigen & Polieren','Für Chromstahl-Schweissnähte','Ohne chemische Beize','Mobil einsetzbar'],
  fr:['Nettoyage & polissage électrolytiques','Pour soudures inox','Sans décapage chimique','Utilisable en mobilité'],
  it:['Pulizia & lucidatura elettrolitica','Per saldature inox','Senza decapaggio chimico','Utilizzo mobile']}
};
const HL_CLEAN={
 'minicleaner':{de:['Kompakte Inverter-Stromquelle','MAHE Pinsel-Schutz-System','Reinigen, Polieren und Markieren','Synergieprogramm für alle Verfahren','Umweltfreundlich und sicher reinigen'],fr:['Source inverter compacte','Système de protection de pinceau MAHE','Nettoyer, polir et marquer','Programme synergique pour tous les procédés','Nettoyage écologique et sûr'],it:['Generatore inverter compatto','Sistema di protezione pennello MAHE','Pulire, lucidare e marcare','Programma sinergico per tutti i processi','Pulizia ecologica e sicura']},
 'hypercleaner-st':{de:['Leistungsstarke 1200 Watt Inverter-Stromquelle','MAHE Pinsel-Schutz-System','Reinigen, Polieren und Markieren','Synergieprogramm für alle Verfahren','Umweltfreundlich und sicher reinigen'],fr:['Source inverter puissante 1200 W','Système de protection de pinceau MAHE','Nettoyer, polir et marquer','Programme synergique pour tous les procédés','Nettoyage écologique et sûr'],it:['Generatore inverter potente 1200 W','Sistema di protezione pennello MAHE','Pulire, lucidare e marcare','Programma sinergico per tutti i processi','Pulizia ecologica e sicura']},
 'hypercleaner-speed':{de:['Leistungsstarke 2400 Watt Inverter-Stromquelle','MAHE Pinsel-Schutz-System','Reinigen, Polieren, Markieren und Galvanisieren','Synergieprogramme für alle Verfahren','Umweltfreundlich und sicher reinigen'],fr:['Source inverter puissante 2400 W','Système de protection de pinceau MAHE','Nettoyer, polir, marquer et galvaniser','Programmes synergiques pour tous les procédés','Nettoyage écologique et sûr'],it:['Generatore inverter potente 2400 W','Sistema di protezione pennello MAHE','Pulire, lucidare, marcare e galvanizzare','Programmi sinergici per tutti i processi','Pulizia ecologica e sicura']},
 'hypercleaner-plus':{de:['Leistungsstarke 4000 Watt Inverter-Stromquelle','MAHE Pinsel-Schutz-System','Reinigen, Polieren, Markieren und Galvanisieren','Synergieprogramme für alle Verfahren','Umweltfreundlich und sicher reinigen'],fr:['Source inverter puissante 4000 W','Système de protection de pinceau MAHE','Nettoyer, polir, marquer et galvaniser','Programmes synergiques pour tous les procédés','Nettoyage écologique et sûr'],it:['Generatore inverter potente 4000 W','Sistema di protezione pennello MAHE','Pulire, lucidare, marcare e galvanizzare','Programmi sinergici per tutti i processi','Pulizia ecologica e sicura']},
 'hypercleaner-ct200':{de:['Kombigerät: WIG-Schweissen und Reinigen','MAHE Pinsel-Schutz-System','Reinigen, Polieren und Markieren','Synergieprogramm für alle Verfahren','Umweltfreundlich und sicher reinigen'],fr:['Appareil combiné : soudage TIG et nettoyage','Système de protection de pinceau MAHE','Nettoyer, polir et marquer','Programme synergique pour tous les procédés','Nettoyage écologique et sûr'],it:['Apparecchio combinato: saldatura TIG e pulizia','Sistema di protezione pennello MAHE','Pulire, lucidare e marcare','Programma sinergico per tutti i processi','Pulizia ecologica e sicura']}
};
function highlightsOf(p){
 if(p.cat==='reinigung'&&p.sub==='Cleaner'&&HL_CLEAN[p.id])return HL_CLEAN[p.id][LANG]||HL_CLEAN[p.id].de;
 var fam=null;
 if(p.id==='hypermig-x')fam='mig_hyper';
 else if(p.sub==='MIG / MAG')fam='mig_std';
 else if(p.sub==='WIG / TIG')fam=/ac\/dc/i.test(p.vt)?'wig_acdc':'wig';
 else if(p.sub==='MMA')fam='mma';
 else if(p.sub==='Plasma TIG')fam='plasmatig';
 else if(p.cat==='plasmaschneiden')fam='theta';
 else if(p.cat==='reinigung'&&p.sub==='Cleaner')fam='cleaner';
 if(!fam)return null;
 return HL[fam][LANG]||HL[fam].de;
}
const MAT_LABEL={ST:{de:'Stahl',fr:'Acier',it:'Acciaio'},SS:{de:'INOX',fr:'INOX',it:'INOX'},AL:{de:'Aluminium',fr:'Aluminium',it:'Alluminio'}};
function matLabel(m){return MAT_LABEL[m]?(MAT_LABEL[m][LANG]||MAT_LABEL[m].de):m;}
function matOf(p){
 if(p.sub==='MIG / MAG')return ['ST','SS','AL'];
 if(p.sub==='WIG / TIG')return /ac\/dc/i.test(p.vt)?['ST','SS','AL']:['ST','SS'];
 if(p.sub==='MMA')return ['ST','SS'];
 if(p.sub==='Plasma TIG')return ['ST','SS','AL'];
 if(p.cat==='plasmaschneiden')return ['ST','SS','AL'];
 if(p.cat==='reinigung'&&p.sub==='Cleaner')return ['SS'];
 return [];
}


/* ---------- Fronteingabesysteme (echte MAHE-Panels) ---------- */
const CTRL={
 VOLT:{de:'VOLT-Anzeige – Schweissspannung & Lichtbogenlänge',fr:'Affichage VOLT – tension & longueur d’arc',it:'Display VOLT – tensione & lunghezza arco'},
 AMP:{de:'AMPERE-Anzeige – Schweissstrom & Drahtgeschwindigkeit',fr:'Affichage AMP – courant & vitesse fil',it:'Display AMP – corrente & velocità filo'},
 MENU:{de:'MENU – Parameterliste & Feineinstellung',fr:'MENU – liste de paramètres & réglage fin',it:'MENU – lista parametri & regolazione fine'},
 JOB:{de:'JOB – 99 Programme speichern & abrufen',fr:'JOB – 99 programmes mémoriser & rappeler',it:'JOB – 99 programmi salva & richiama'},
 MODE:{de:'Synergy / Manuell – automatische oder freie Einstellung',fr:'Synergy / Manuel – automatique ou libre',it:'Synergy / Manuale – automatico o libero'},
 PROC:{de:'Prozesswahl – MIG/MAG, Puls, MMA, WIG',fr:'Choix du procédé – MIG/MAG, pulsé, MMA, TIG',it:'Scelta processo – MIG/MAG, pulsato, MMA, TIG'},
 WIRE:{de:'Drahtmaterial & -durchmesser (0,8–2,0 mm)',fr:'Matériau & diamètre du fil (0,8–2,0 mm)',it:'Materiale & diametro filo (0,8–2,0 mm)'},
 GAS:{de:'Gastest – Ventil zum Einstellen des Gasflusses',fr:'Test gaz – vanne pour régler le débit',it:'Test gas – valvola per il flusso'},
 TAKT:{de:'2-Takt / 4-Takt – Brennertaster-Funktion',fr:'2 temps / 4 temps – fonction gâchette',it:'2 tempi / 4 tempi – funzione pulsante'},
 ARC:{de:'Lichtbogenlänge – Feinkorrektur im Synergy-Modus',fr:'Longueur d’arc – correction fine en Synergy',it:'Lunghezza arco – correzione fine in Synergy'},
 BURN:{de:'Drahtrückbrand – Kraterfüllung am Nahtende',fr:'Retour de fil – remplissage en fin de cordon',it:'Ritorno filo – riempimento a fine cordone'},
 WIG_HF:{de:'HF-Zündung / Lift Arc – berührungslos oder Kontakt',fr:'Amorçage HF / Lift Arc',it:'Innesco HF / Lift Arc'},
 WIG_PULS:{de:'Puls-Funktion – Frequenz & Balance',fr:'Fonction pulsée – fréquence & balance',it:'Funzione impulso – frequenza & balance'},
 WIG_SLOPE:{de:'Up-/Down-Slope – Strom-Anstieg & -Absenkung',fr:'Slope montée/descente du courant',it:'Slope salita/discesa corrente'},
 WIG_GAS:{de:'Gas-Vor-/Nachströmzeit',fr:'Pré-/post-gaz',it:'Pre-/post-gas'},
 MMA_HOT:{de:'Hot Start – erleichtertes Zünden der Elektrode',fr:'Hot Start – amorçage facilité',it:'Hot Start – innesco facilitato'},
 MMA_ARC:{de:'Arc Force – dynamische Lichtbogen-Stabilität',fr:'Arc Force – stabilité dynamique',it:'Arc Force – stabilità dinamica'},
 MMA_STICK:{de:'Anti-Stick – verhindert Festkleben der Elektrode',fr:'Anti-Stick – évite le collage',it:'Anti-Stick – evita l’incollaggio'},
 THETA_CUR:{de:'Schneidstrom – stufenlos einstellbar',fr:'Courant de coupe – réglable',it:'Corrente di taglio – regolabile'},
 THETA_AIR:{de:'Luftdruck-Anzeige & Regelung',fr:'Pression d’air – affichage & réglage',it:'Pressione aria – display & regolazione'},
 THETA_PILOT:{de:'Pilotlichtbogen – Schneiden ohne Kontakt',fr:'Arc pilote – coupe sans contact',it:'Arco pilota – taglio senza contatto'},
 CL_POWER:{de:'Leistungsstufe – an Werkstoff angepasst',fr:'Niveau de puissance',it:'Livello di potenza'},
 CL_MODE:{de:'Reinigen / Polieren / Signieren – Betriebsart',fr:'Nettoyer / polir / marquer – mode',it:'Pulire / lucidare / marcare – modo'}
};
const FP={
 hyper:{n:'HX – Hyper Front Panel',big:true,img:'2022/03/HyperMIG_HX_Frontpanel-300x172.png',tl:{de:'Volldigitale Bedienung mit HyperPuls, HyperForce, Doppelpuls und 99 JOB-Programmen.',fr:'Commande entièrement numérique avec HyperPuls, HyperForce, double pulsation et 99 programmes JOB.',it:'Comando completamente digitale con HyperPuls, HyperForce, doppio impulso e 99 programmi JOB.'},ctrl:['VOLT','AMP','MENU','JOB','MODE','PROC','WIRE','GAS','TAKT','ARC','BURN']},
 ecopuls:{n:'EX – EcoPuls Front Panel',big:true,img:'2022/03/HyperMIG_EX_Frontpanel.-300x172.png',tl:{de:'Digitale Puls-Bedienung mit Impuls, Doppelpuls und JOB-Speicher.',fr:'Commande numérique pulsée avec impulsion, double pulsation et mémoire JOB.',it:'Comando digitale pulsato con impulso, doppio impulso e memoria JOB.'},ctrl:['VOLT','AMP','MENU','JOB','MODE','PROC','WIRE','GAS','TAKT','ARC']},
 ecomig:{n:'EX – EcoMIG Front Panel',big:true,img:'2022/03/HyperMIG_EX_Frontpanel.-300x172.png',tl:{de:'Einfache digitale Synergie-Bedienung für MIG/MAG, MMA und WIG Lift.',fr:'Commande synergique numérique simple pour MIG/MAG, MMA et TIG Lift.',it:'Comando sinergico digitale semplice per MIG/MAG, MMA e TIG Lift.'},ctrl:['VOLT','AMP','MENU','JOB','MODE','PROC','WIRE','GAS','TAKT']},
 wig:{n:'WIG DC – Bedienpanel',big:false,tl:{de:'WIG-DC-Panel mit HF-Zündung, HyperSpot, Puls und Slope-Steuerung.',fr:'Panneau TIG DC avec amorçage HF, HyperSpot, pulsé et slopes.',it:'Pannello TIG DC con innesco HF, HyperSpot, impulso e slope.'},ctrl:['VOLT','AMP','WIG_HF','WIG_PULS','WIG_SLOPE','WIG_GAS','TAKT']},
 wig_acdc:{n:'WIG AC/DC – Bedienpanel',big:false,tl:{de:'AC/DC-Panel mit HF-Zündung, HyperSpot, MAHE-MIX-PULSE und AC-Balance/Frequenz.',fr:'Panneau AC/DC avec amorçage HF, HyperSpot, MAHE-MIX-PULSE et balance/fréquence AC.',it:'Pannello AC/DC con innesco HF, HyperSpot, MAHE-MIX-PULSE e balance/frequenza AC.'},ctrl:['VOLT','AMP','WIG_HF','WIG_PULS','WIG_SLOPE','WIG_GAS','TAKT']},
 mma:{n:'MMA-Bedienpanel',big:false,tl:{de:'MMA-Panel mit Hot Start, Arc Force und Anti-Stick.',fr:'Panneau MMA avec Hot Start, Arc Force et Anti-Stick.',it:'Pannello MMA con Hot Start, Arc Force e Anti-Stick.'},ctrl:['VOLT','AMP','MMA_HOT','MMA_ARC','MMA_STICK']},
 theta:{n:'Plasma-Bedienpanel',big:false,tl:{de:'Plasma-Panel mit Schneidstrom, Luftdruck und Pilotlichtbogen.',fr:'Panneau plasma avec courant de coupe, pression d’air et arc pilote.',it:'Pannello plasma con corrente di taglio, pressione aria e arco pilota.'},ctrl:['THETA_CUR','THETA_AIR','THETA_PILOT','TAKT']},
 cleaner:{n:'Cleaner-Bedienpanel',big:false,tl:{de:'Cleaner-Panel mit Leistungsstufen und Betriebsartwahl.',fr:'Panneau Cleaner avec niveaux de puissance et choix du mode.',it:'Pannello Cleaner con livelli di potenza e scelta du mode.'},ctrl:['CL_POWER','CL_MODE']},
 steel:{n:'SX – Steel Front Panel',big:true,img:'2023/01/HyperMIG_SX_Frontpanel-300x172.png',tl:{de:'Stahl-optimiertes Panel mit HyperCold, HyperRoot und HyperForce.',fr:'Panneau optimisé acier avec HyperCold, HyperRoot et HyperForce.',it:'Pannello ottimizzato acciaio con HyperCold, HyperRoot e HyperForce.'},ctrl:['VOLT','AMP','MENU','JOB','MODE','PROC','WIRE','GAS','TAKT']},
 steelpuls:{n:'SX – Steel Puls Front Panel',big:true,img:'2023/01/HyperMIG_SX_Frontpanel-300x172.png',tl:{de:'Stahl-Puls-Panel mit HyperPuls, HyperUP und HyperForce.',fr:'Panneau acier pulsé avec HyperPuls, HyperUP et HyperForce.',it:'Pannello acciaio pulsato con HyperPuls, HyperUP e HyperForce.'},ctrl:['VOLT','AMP','MENU','JOB','MODE','PROC','WIRE','GAS','TAKT','ARC']}
};
function fpAssign(p){
 if(p.id==='hypermig-x')return['ecomig','ecopuls','hyper','steel','steelpuls'];
 if(p.sub==='MIG / MAG')return['ecomig','ecopuls'];
 if(p.sub==='WIG / TIG')return[/ac\/dc/i.test(p.vt)?'wig_acdc':'wig'];
 if(p.sub==='Plasma TIG')return['wig'];
 if(p.sub==='MMA')return['mma'];
 if(p.cat==='plasmaschneiden')return['theta'];
 return[];
}
function panelSVG(big){
 return '<svg viewBox="0 0 330 220" width="'+(big?400:340)+'" style="max-width:100%;height:auto">'+
 '<rect x="3" y="3" width="324" height="214" rx="16" fill="#c9ccd2" stroke="#adb1b9" stroke-width="2"/><rect x="11" y="11" width="308" height="198" rx="11" fill="none" stroke="#b6b9c1" stroke-width="2"/><rect x="24" y="24" width="42" height="42" rx="7" fill="#6c7079"/><rect x="27" y="27" width="36" height="36" rx="5" fill="#41454d"/><circle cx="80" cy="33" r="3.2" fill="#ff6a1f"/><path d="M89 29 l10 7" stroke="#41454d" stroke-width="2" stroke-linecap="round"/><circle cx="80" cy="52" r="3.2" fill="#c2c5cc"/><rect x="89" y="50" width="14" height="3.4" rx="1" fill="#41454d"/><rect x="112" y="24" width="42" height="42" rx="7" fill="#6c7079"/><rect x="115" y="27" width="36" height="36" rx="5" fill="#41454d"/><path d="M122 48 q0 -11 8 -10 q1 -5 6 -3 q1 -4 5 -1 q4 -1 4 6 q4 4 -1 10 q-5 6 -14 4 q-9 -2 -8 -6z" fill="#cfd2d7"/><circle cx="166" cy="33" r="3.2" fill="#c2c5cc"/><text x="174" y="36" font-family="Arial" font-size="8" fill="#41454d">2T</text><circle cx="166" cy="52" r="3.2" fill="#c2c5cc"/><text x="174" y="55" font-family="Arial" font-size="8" fill="#41454d">4T</text><rect x="206" y="24" width="40" height="42" rx="7" fill="#6c7079"/><rect x="209" y="27" width="34" height="36" rx="5" fill="#41454d"/><text x="226" y="49" font-family="Arial" font-size="13" font-weight="bold" fill="#e8eaee" text-anchor="middle">Job</text><rect x="256" y="24" width="46" height="30" rx="4" fill="#c73a2c"/><rect x="259" y="27" width="40" height="24" rx="2" fill="#d24333"/><path d="M309 20 l8 14 h-16 z" fill="none" stroke="#41454d" stroke-width="1.4"/><text x="309" y="33" font-family="Arial" font-size="8" fill="#41454d" text-anchor="middle">!</text><g font-family="Arial" font-size="8" fill="#41454d" text-anchor="middle"><circle cx="260" cy="64" r="3" fill="#ff6a1f"/><text x="260" y="78">A</text><circle cx="276" cy="64" r="3" fill="#c2c5cc"/><text x="276" y="78">sec</text><circle cx="293" cy="64" r="3" fill="#c2c5cc"/><text x="293" y="78">Hz</text><circle cx="309" cy="64" r="3" fill="#c2c5cc"/><text x="309" y="78">%</text></g><circle cx="258" cy="92" r="3" fill="#c2c5cc"/><path d="M266 95 h4 v-6 h5 v6 h4" stroke="#41454d" stroke-width="1.4" fill="none"/><circle cx="292" cy="92" r="3" fill="#c2c5cc"/><path d="M300 90 h5 v5 M300 92 h3" stroke="#41454d" stroke-width="1.4" fill="none"/><rect x="24" y="90" width="46" height="46" rx="7" fill="#6c7079"/><rect x="27" y="93" width="40" height="40" rx="5" fill="#41454d"/><text x="47" y="109" font-family="Arial" font-size="11" font-weight="bold" fill="#e8eaee" text-anchor="middle">AC</text><text x="47" y="123" font-family="Arial" font-size="11" font-weight="bold" fill="#e8eaee" text-anchor="middle">DC</text><circle cx="84" cy="100" r="3.2" fill="#ff6a1f"/><text x="94" y="103" font-family="Arial" font-size="8" fill="#41454d">DC</text><circle cx="84" cy="114" r="3.2" fill="#c2c5cc"/><text x="94" y="117" font-family="Arial" font-size="8" fill="#41454d">AC</text><circle cx="84" cy="128" r="3.2" fill="#c2c5cc"/><text x="94" y="131" font-family="Arial" font-size="8" fill="#41454d">AC~</text><rect x="126" y="90" width="46" height="46" rx="7" fill="#6c7079"/><rect x="129" y="93" width="40" height="40" rx="5" fill="#41454d"/><g fill="#cfd2d7"><circle cx="137" cy="108" r="2"/><circle cx="145" cy="108" r="2"/><circle cx="153" cy="108" r="2"/><circle cx="161" cy="108" r="2"/><circle cx="137" cy="118" r="2"/><circle cx="145" cy="118" r="2"/><circle cx="153" cy="118" r="2"/><circle cx="161" cy="118" r="2"/></g><circle cx="186" cy="100" r="3.2" fill="#c2c5cc"/><text x="196" y="103" font-family="Arial" font-size="8" fill="#41454d">OFF</text><circle cx="186" cy="114" r="3.2" fill="#ff6a1f"/><text x="196" y="117" font-family="Arial" font-size="7.5" fill="#41454d">HYPER SPOT</text><circle cx="186" cy="128" r="3.2" fill="#c2c5cc"/><text x="196" y="131" font-family="Arial" font-size="7.5" fill="#41454d">ACTIVE SPOT</text><rect x="24" y="144" width="46" height="46" rx="7" fill="#6c7079"/><rect x="27" y="147" width="40" height="40" rx="5" fill="#41454d"/><path d="M35 178 h6 v-16 h9 v16 h7" stroke="#e8eaee" stroke-width="2" fill="none"/><circle cx="84" cy="154" r="3.2" fill="#ff6a1f"/><path d="M92 156 h4 v-5 h4 v5 h4" stroke="#41454d" stroke-width="1.3" fill="none"/><circle cx="84" cy="168" r="3.2" fill="#c2c5cc"/><path d="M92 170 h3 v-4 h3 v4 h3 v-4 h3" stroke="#41454d" stroke-width="1.3" fill="none"/><circle cx="84" cy="182" r="3.2" fill="#c2c5cc"/><path d="M92 182 q2 -4 4 0 t4 0 t4 0" stroke="#41454d" stroke-width="1.3" fill="none"/><rect x="126" y="144" width="46" height="46" rx="7" fill="#6c7079"/><rect x="129" y="147" width="40" height="40" rx="5" fill="#41454d"/><text x="149" y="164" font-family="Arial" font-size="11" font-weight="bold" fill="#e8eaee" text-anchor="middle">HF</text><path d="M143 172 h12 l-3 8 h-6 z" fill="#cfd2d7"/><circle cx="186" cy="156" r="3.2" fill="#ff6a1f"/><text x="196" y="159" font-family="Arial" font-size="8" fill="#41454d">ON</text><circle cx="186" cy="178" r="3.2" fill="#c2c5cc"/><text x="196" y="181" font-family="Arial" font-size="8" fill="#41454d">OFF</text><path d="M228 130 q30 -20 60 0" stroke="#41454d" stroke-width="4" fill="none" stroke-linecap="round"/><circle cx="258" cy="168" r="30" fill="#17181c"/><circle cx="258" cy="168" r="30" fill="none" stroke="#0c0d10" stroke-width="2"/><circle cx="258" cy="168" r="21" fill="none" stroke="#33363c" stroke-width="1"/><circle cx="300" cy="150" r="3.2" fill="#ff6a1f"/><text x="308" y="149" font-family="Arial" font-size="6.5" fill="#41454d">HyperArc</text><text x="308" y="156" font-family="Arial" font-size="6.5" fill="#41454d">Active</text><circle cx="300" cy="170" r="3.2" fill="#c2c5cc"/><path d="M308 172 l8 -6 M312 166 h4 v4" stroke="#41454d" stroke-width="1.2" fill="none"/><polyline points="26,198 42,198 42,192 56,192 70,176 108,176 120,186 150,186 164,170 200,170 214,198 230,198" fill="none" stroke="#41454d" stroke-width="2" stroke-linejoin="round"/><path d="M214,198 L214,192 226,192" fill="none" stroke="#41454d" stroke-width="2" stroke-dasharray="3 2"/><g stroke="#a7abb3" stroke-width="0.7" stroke-dasharray="2 2"><line x1="56" y1="198" x2="56" y2="176"/><line x1="108" y1="198" x2="108" y2="176"/><line x1="150" y1="198" x2="150" y2="170"/><line x1="200" y1="198" x2="200" y2="170"/></g><g font-family="Arial" font-size="7" fill="#6a6e77"><text x="46" y="207">s</text><text x="84" y="207">I1</text><text x="132" y="207">I2</text><text x="205" y="207">s</text></g><g fill="#c2c5cc" stroke="#8f939b" stroke-width="0.5"><circle cx="70" cy="176" r="2.4"/><circle cx="120" cy="186" r="2.4"/><circle cx="164" cy="170" r="2.4"/></g>'+
 '</svg>';
}
const PANEL_HL={
 ecomig:{de:['MIS-Schweissen','MIG-Löten','HyperForce, HyperRoot, HyperCold','MMA-Elektrodenschweissen','WIG Lift Arc','JOB-Modus · 99 Programme'],
  fr:['Soudage MIS','Brasage MIG','HyperForce, HyperRoot, HyperCold','Soudage à l’électrode MMA','TIG Lift Arc','Mode JOB · 99 programmes'],
  it:['Saldatura MIS','Brasatura MIG','HyperForce, HyperRoot, HyperCold','Saldatura a elettrodo MMA','TIG Lift Arc','Modo JOB · 99 programmi']},
 ecopuls:{de:['MIS-Schweissen','Impuls-Schweissen','Doppelpuls-Schweissen','MIG-Löten','HyperForce, HyperRoot, HyperCold','MMA-Elektrodenschweissen','WIG Lift Arc','JOB-Modus · 99 Programme'],
  fr:['Soudage MIS','Soudage pulsé','Soudage double pulsation','Brasage MIG','HyperForce, HyperRoot, HyperCold','Soudage à l’électrode MMA','TIG Lift Arc','Mode JOB · 99 programmes'],
  it:['Saldatura MIS','Saldatura a impulsi','Saldatura doppio impulso','Brasatura MIG','HyperForce, HyperRoot, HyperCold','Saldatura a elettrodo MMA','TIG Lift Arc','Modo JOB · 99 programmi']},
 hyper:{de:['MIS-Schweissen','Impuls-Schweissen','Doppelpuls-Schweissen','MIG-Löten','HyperPuls-Schweissen','HyperForce-Schweissen','HyperCold-Schweissen','HyperRoot-Schweissen','HyperUP-Schweissen','WIG Lift Arc','MMA-Elektrodenschweissen','JOB-Modus · 99 Programme'],
  fr:['Soudage MIS','Soudage pulsé','Soudage double pulsation','Brasage MIG','Soudage HyperPuls','Soudage HyperForce','Soudage HyperCold','Soudage HyperRoot','Soudage HyperUP','TIG Lift Arc','Soudage à l’électrode MMA','Mode JOB · 99 programmes'],
  it:['Saldatura MIS','Saldatura a impulsi','Saldatura doppio impulso','Brasatura MIG','Saldatura HyperPuls','Saldatura HyperForce','Saldatura HyperCold','Saldatura HyperRoot','Saldatura HyperUP','TIG Lift Arc','Saldatura a elettrodo MMA','Modo JOB · 99 programmi']},
 wig:{de:['Einknopfbedienung','Übersichtliche Bedienerführung','Synergische Kennlinien','Hyper Arc Active Kennlinie serienmässig','Hyper Spot Kennlinie serienmässig','ActiveSpot Kennlinie serienmässig','Hochfrequenzpulsen serienmässig','Fernbedienung Ein / Aus','HF-Start oder Lift-Arc-Start','WIG DC & MMA'],
  fr:['Commande à un bouton','Guidage clair de l’opérateur','Courbes synergiques','Courbe Hyper Arc Active de série','Courbe Hyper Spot de série','Courbe ActiveSpot de série','Pulsation haute fréquence de série','Télécommande on/off','Amorçage HF ou Lift-Arc','TIG DC & MMA'],
  it:['Comando a una manopola','Guida operatore chiara','Curve sinergiche','Curva Hyper Arc Active di serie','Curva Hyper Spot di serie','Curva ActiveSpot di serie','Pulsazione alta frequenza di serie','Telecomando on/off','Innesco HF o Lift-Arc','TIG DC & MMA']},
 wig_acdc:{de:['Einknopfbedienung','Übersichtliche Bedienerführung','Synergische Kennlinien','Hyper Arc Active Kennlinie serienmässig','Hyper Spot Kennlinie serienmässig','ActiveSpot Kennlinie serienmässig','Hochfrequenzpulsen serienmässig','MAHE-MIX-PULSE (AC)','Fernbedienung Ein / Aus','HF-Start oder Lift-Arc-Start','AC-Schweissen (WIG und MMA)'],
  fr:['Commande à un bouton','Guidage clair de l’opérateur','Courbes synergiques','Courbe Hyper Arc Active de série','Courbe Hyper Spot de série','Courbe ActiveSpot de série','Pulsation haute fréquence de série','MAHE-MIX-PULSE (AC)','Télécommande on/off','Amorçage HF ou Lift-Arc','Soudage AC (TIG et MMA)'],
  it:['Comando a una manopola','Guida operatore chiara','Curve sinergiche','Curva Hyper Arc Active di serie','Curva Hyper Spot di serie','Curva ActiveSpot di serie','Pulsazione alta frequenza di serie','MAHE-MIX-PULSE (AC)','Telecomando on/off','Innesco HF o Lift-Arc','Saldatura AC (TIG e MMA)']},
 mma:{de:['Prozesswahl: MMA · MMA-CEL · Fugenhobeln · WIG Lift-Arc','Hot-Start einstellbar','Arc-Force einstellbar (0–100 %)','Anti-Stick','Digitale Anzeige (Delta Digital)','Fernbedienung anschliessbar'],
  fr:['Choix du procédé : MMA · MMA-CEL · gougeage · TIG Lift-Arc','Hot-Start réglable','Arc-Force réglable (0–100 %)','Anti-Stick','Affichage numérique (Delta Digital)','Télécommande raccordable'],
  it:['Scelta processo: MMA · MMA-CEL · scriccatura · TIG Lift-Arc','Hot-Start regolabile','Arc-Force regolabile (0–100 %)','Anti-Stick','Display digitale (Delta Digital)','Telecomando collegabile']},
 theta:{de:['Plasmaschneiden mit HSC-Technologie','Pilotlichtbogen (kontaktlos)','Schneidstrom stufenlos','Luftdruck-Regelung','Gittertrennen möglich','2-Takt / 4-Takt'],
  fr:['Découpe plasma technologie HSC','Arc pilote (sans contact)','Courant de coupe réglable','Régulation de la pression d’air','Découpe de grilles possible','2 temps / 4 temps'],
  it:['Taglio plasma tecnologia HSC','Arco pilota (senza contatto)','Corrente di taglio regolabile','Regolazione pressione aria','Taglio di grigliati possibile','2 tempi / 4 tempi']},
 cleaner:{de:['Elektrolytisches Reinigen','Polieren von Schweissnähten','Signieren (mit Zubehör)','Leistungsstufen wählbar','Betriebsart-Wahl'],
  fr:['Nettoyage électrolytique','Polissage des soudures','Marquage (avec accessoire)','Niveaux de puissance sélectionnables','Choix du mode'],
  it:['Pulizia elettrolitica','Lucidatura delle saldature','Marcatura (con accessorio)','Livelli di potenza selezionabili','Scelta del modo']},
 steel:{de:['MIS-Schweissen','HyperCold-Schweissen','HyperRoot-Schweissen','HyperForce-Schweissen','WIG Lift Arc','MMA-Elektrodenschweissen'],
  fr:['Soudage MIS','Soudage HyperCold','Soudage HyperRoot','Soudage HyperForce','TIG Lift Arc','Soudage à l’électrode MMA'],
  it:['Saldatura MIS','Saldatura HyperCold','Saldatura HyperRoot','Saldatura HyperForce','TIG Lift Arc','Saldatura a elettrodo MMA']},
 steelpuls:{de:['MIS-Schweissen','HyperPuls-Schweissen','HyperCold-Schweissen','HyperRoot-Schweissen','HyperForce-Schweissen','HyperUP-Schweissen','WIG Lift Arc','MMA-Elektrodenschweissen'],
  fr:['Soudage MIS','Soudage HyperPuls','Soudage HyperCold','Soudage HyperRoot','Soudage HyperForce','Soudage HyperUP','TIG Lift Arc','Soudage à l’électrode MMA'],
  it:['Saldatura MIS','Saldatura HyperPuls','Saldatura HyperCold','Saldatura HyperRoot','Saldatura HyperForce','Saldatura HyperUP','TIG Lift Arc','Saldatura a elettrodo MMA']}
};

var __out = { P:P, CATS:CATS, PK:PK, UI:UI, CATTR:CATTR, SUBTR:SUBTR, PDESC:PDESC,
  SPECK:SPECK, SPECV:SPECV, PROC:PROC, DLS:DLS, FEAT:FEAT, HL:HL, HL_CLEAN:HL_CLEAN,
  CTRL:CTRL, FP:FP, PANEL_HL:PANEL_HL, MAT_LABEL:MAT_LABEL, PANEL_SVG:PANEL_SVG };
JSON.stringify(__out);
