// Schneidet den fast-weissen Rand eines Produktfotos weg.
// Viele MAHE-Fotos zeigen die Maschine klein in einer grossen weissen Flaeche;
// auf der Seite wirkt sie dadurch winzig, obwohl die Datei gross ist.
import Foundation
import AppKit

let args = CommandLine.arguments
guard args.count >= 3, let img = NSImage(contentsOfFile: args[1]),
      let tiff = img.tiffRepresentation, let rep = NSBitmapImageRep(data: tiff) else {
    FileHandle.standardError.write("unlesbar\n".data(using: .utf8)!); exit(1)
}
let w = rep.pixelsWide, h = rep.pixelsHigh
// NSImage rechnet in Punkten, nicht in Pixeln. Bei einem Bild mit anderer
// Aufloesung als 72 dpi liegt der Ausschnitt sonst voellig daneben - beim
// Fernregler RC 5 blieb genau deshalb nur eine Ecke des Kabels uebrig.
img.size = NSSize(width: w, height: h)
let schwelle: CGFloat = 0.93        // alles darueber gilt als Hintergrund
func istInhalt(_ x: Int, _ y: Int) -> Bool {
    guard let c = rep.colorAt(x: x, y: y) else { return false }
    if c.alphaComponent < 0.15 { return false }
    guard let s = c.usingColorSpace(.deviceRGB) else { return false }
    return !(s.redComponent > schwelle && s.greenComponent > schwelle && s.blueComponent > schwelle)
}
var x0 = w, y0 = h, x1 = -1, y1 = -1
let schritt = max(1, min(w, h) / 700)          // grosse Bilder abtasten statt jeden Pixel
for y in stride(from: 0, to: h, by: schritt) {
    for x in stride(from: 0, to: w, by: schritt) where istInhalt(x, y) {
        if x < x0 { x0 = x }; if x > x1 { x1 = x }
        if y < y0 { y0 = y }; if y > y1 { y1 = y }
    }
}
if x1 < 0 { print("leer"); exit(2) }
let luft = max(6, Int(Double(max(x1 - x0, y1 - y0)) * 0.025))   // etwas Luft stehen lassen
x0 = max(0, x0 - luft); y0 = max(0, y0 - luft)
x1 = min(w - 1, x1 + luft); y1 = min(h - 1, y1 + luft)
let nw = x1 - x0 + 1, nh = y1 - y0 + 1
if nw >= Int(Double(w) * 0.97) && nh >= Int(Double(h) * 0.97) { print("kein Rand"); exit(3) }
// Sicherheitsnetz: wer mehr als drei Viertel der Flaeche wegschneidet, hat
// vermutlich den Hintergrund falsch erkannt. Dann lieber gar nicht schneiden.
if Double(nw * nh) < Double(w * h) * 0.12 { print("verdaechtig klein"); exit(4) }
let ziel = NSImage(size: NSSize(width: nw, height: nh))
ziel.lockFocus()
NSColor.white.setFill(); NSRect(origin: .zero, size: ziel.size).fill()
img.draw(in: NSRect(x: 0, y: 0, width: nw, height: nh),
         from: NSRect(x: x0, y: h - y1 - 1, width: nw, height: nh),
         operation: .sourceOver, fraction: 1)
ziel.unlockFocus()
let out = NSBitmapImageRep(data: ziel.tiffRepresentation!)!
try! out.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: args[2]))
print("\(w)x\(h) -> \(nw)x\(nh)")
