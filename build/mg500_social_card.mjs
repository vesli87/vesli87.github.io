// Manual asset build: node build/mg500_social_card.mjs.
// Preserve the complete supplied product photograph; no cropping or retouching.
import {readFileSync,writeFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {homedir} from 'node:os';
import path from 'node:path';
const require=createRequire(import.meta.url);
let sharp;
try { sharp=require('sharp'); }
catch { sharp=require(path.join(homedir(),'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp')); }
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const manifest=JSON.parse(readFileSync(path.join(root,'assets/img/manifest.json'),'utf8'));
const source=manifest['2026/08/MG500_A.png'];
const photo=readFileSync(path.join(root,'assets/img/p',`${source.key}-${source.w}.webp`));
const preview=await sharp(photo).resize({width:330,height:570,fit:'inside',withoutEnlargement:true}).png().toBuffer();
const size=await sharp(preview).metadata();
if (size.height>570 || size.width>330 || Math.abs(size.height/size.width-source.h/source.w)>0.01) throw new Error('Photo aspect ratio changed');
const copy=JSON.parse(readFileSync(path.join(root,'data/SOCIAL_CARDS.json'),'utf8')).mg500;
const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
for (const [lang,text] of Object.entries(copy)) {
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
<rect width="1200" height="630" fill="#F4F6F7"/>
<path d="M730 0H1200V630H655L730 555Z" fill="#FF5B0A"/>
<path d="M0 595H610L705 500" fill="none" stroke="#B5BEC6" stroke-width="2"/>
<rect x="770" y="20" width="360" height="590" rx="4" fill="white"/>
<g font-family="Helvetica,Arial,sans-serif" fill="#14181D">
<text x="70" y="90" font-size="32" font-weight="700">VES-TECH <tspan fill="#AE3500">Swiss</tspan></text>
<text x="70" y="184" font-size="28" font-weight="700" fill="#AE3500">MAHE</text>
<text x="66" y="302" font-size="105" font-weight="700">MG500</text>
<text x="70" y="365" font-size="36">${esc(text.type)}</text>
<text x="70" y="435" font-size="34" font-weight="700">500 A / 60 % · 4 m</text>
<text x="70" y="487" font-size="25">${esc(text.photo_note)}</text>
<text x="70" y="560" font-size="28" font-weight="700">ves-tech.ch</text>
</g></svg>`;
  const left=770+Math.round((360-size.width)/2),top=20+Math.round((590-size.height)/2);
  const rendered=await sharp(Buffer.from(svg)).composite([{input:preview,left,top}]).png({compressionLevel:9}).toBuffer();
  const expected=await sharp(preview).ensureAlpha().raw().toBuffer();
  const actual=await sharp(rendered).extract({left,top,width:size.width,height:size.height}).ensureAlpha().raw().toBuffer();
  if (!actual.equals(expected)) throw new Error('Product photo changed during card composition');
  writeFileSync(path.join(root,`assets/img/social/mg500-${lang}.png`),rendered);
  console.log(`${lang}: 1200 × 630; complete MG500 photograph retained`);
}
