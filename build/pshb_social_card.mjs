// Manual artwork build only; CI uses the reviewed, committed PNG files.
// node build/pshb_social_card.mjs (uses an existing sharp installation).
// The existing photograph is preserved. Its decoded pixels are losslessly
// wrapped as PNG because this SVG renderer does not support embedded WEBP.
// No crop, filter, recolouring, retouching or generated product geometry.
import {readFileSync, writeFileSync, mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {homedir} from 'node:os';
import path from 'node:path';

const require = createRequire(import.meta.url);
let sharp;
try { sharp = require('sharp'); }
catch { sharp = require(path.join(homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp')); }
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const source = 'assets/img/p/pshb125-ab85b8-1000.webp';
const photo = readFileSync(path.join(root, source));
const hash = createHash('sha256').update(photo).digest('hex');
if (hash !== '14e1e3b3076738e240ed3890dc4e30ad52a4ea9aa92e01f2aeac645c891b1014') {
  throw new Error('PSHB source photograph changed: review identity and full-image placement before rebuilding.');
}
const embeddedPhoto = await sharp(photo).png().toBuffer();
const sourcePixels = await sharp(photo).ensureAlpha().raw().toBuffer();
const embeddedPixels = await sharp(embeddedPhoto).ensureAlpha().raw().toBuffer();
if (!sourcePixels.equals(embeddedPixels)) throw new Error('Photo pixels changed during PNG format conversion.');
const copy = JSON.parse(readFileSync(path.join(root, 'data/SOCIAL_CARDS.json'), 'utf8')).pshb125;
const svgDir = path.join(root, 'build/social-cards');
const pngDir = path.join(root, 'assets/img/social');
mkdirSync(svgDir, {recursive: true});
mkdirSync(pngDir, {recursive: true});
const esc = value => value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

for (const lang of ['de', 'fr', 'it']) {
  const {type, photo_note: note} = copy[lang];
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-labelledby="title desc">
<title id="title">VES-TECH Swiss · MAHE PSHB 125 · ${esc(type)}</title>
<desc id="desc">${esc(note)}. MAHE PSHB 125. ves-tech.ch.</desc>
<rect width="1200" height="630" fill="#F7F1E7"/>
<rect width="16" height="630" fill="#E0511A"/>
<rect x="702" y="26" width="330" height="578" rx="20" fill="#FFFFFF"/>
<g font-family="Helvetica, Arial, sans-serif" fill="#171C20">
  <text x="165" y="111" font-size="38" font-weight="700">VES-TECH <tspan fill="#D94A16">Swiss</tspan></text>
  <path d="M165 168H631" stroke="#CDC6BA" stroke-width="2"/>
  <text x="165" y="258" font-size="35" font-weight="700" fill="#D94A16" letter-spacing="2">MAHE</text>
  <text x="159" y="348" font-size="86" font-weight="700" letter-spacing="-2">PSHB 125</text>
  <text x="165" y="406" font-size="38" font-weight="400">${esc(type)}</text>
  <text x="165" y="536" font-size="30" font-weight="700">ves-tech.ch</text>
</g>
<!-- Original decoded pixels, full image contained within the landscape card. -->
<image x="745" y="45" width="244" height="510" preserveAspectRatio="xMidYMid meet" data-source-sha256="${hash}" xlink:href="data:image/png;base64,${embeddedPhoto.toString('base64')}"/>
<text x="867" y="582" text-anchor="middle" font-family="Helvetica, Arial, sans-serif" font-size="18" fill="#57534C">${esc(note)}</text>
</svg>\n`;
  const filename = `pshb125-${lang}`;
  writeFileSync(path.join(svgDir, filename + '.svg'), svg);
  const rendered = await sharp(Buffer.from(svg)).png().toBuffer();
  // A valid SVG data URI alone is not enough: a renderer can silently omit
  // unsupported formats. Verify actual dark photo pixels, away from text.
  const region = await sharp(rendered).extract({left: 770, top: 70, width: 200, height: 470}).removeAlpha().raw().toBuffer();
  let dark = 0;
  for (let i = 0; i < region.length; i += 3) if (Math.max(...region.subarray(i, i + 3)) < 100) dark++;
  if (dark < 10000) throw new Error('Rendered share card is missing the torch photograph.');
  writeFileSync(path.join(pngDir, filename + '.png'), rendered);
  console.log(`${filename}: 1200×630; source SHA256 ${hash}`);
}
