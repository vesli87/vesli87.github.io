/* ==== source lines 540-557 ==== */
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


/* ==== source lines 583-589 ==== */
const USE_LOCAL=false;
const REMOTE='https://mahe-online.de/wp-content/uploads/';
const LOCAL='images/';
const IMG=''; // Platzhalter – die Produkte speichern nur den relativen Pfad
var EMBED={};/*EMBED-MARKER*/
function SRC(path){var fn=path.split('/').pop(); if(EMBED[fn])return EMBED[fn]; return USE_LOCAL?LOCAL+fn:REMOTE+path;}
function fullImg(path){return path.replace(/-[0-9]+x[0-9]+(\.[a-zA-Z]+)$/,'$1');}

/* ==== source lines 767-769 ==== */
let cart=[];
/* ================= i18n ================= */
let LANG='de';

/* ==== source lines 781-786 ==== */
function catT(c){return LANG!=='de'&&CATTR[c.id]?CATTR[c.id].t[LANG]:c.t;}
function catD(c){return LANG!=='de'&&CATTR[c.id]?CATTR[c.id].d[LANG]:c.d;}
function subT(n){return LANG!=='de'&&SUBTR[n]?SUBTR[n][LANG]:n;}
function pDesc(p){return LANG!=='de'&&PDESC[p.id]?PDESC[p.id][LANG]:p.desc;}
function trK(k){return LANG!=='de'&&SPECK[k]?SPECK[k][LANG]:k;}
function trV(v){if(LANG==='de')return v; if(SPECV[v])return SPECV[v][LANG]; if(v.indexOf('bis ')===0)return (LANG==='fr'?'jusqu\u2019à ':'fino a ')+v.slice(4); return v;}

/* ==== source lines 814-826 ==== */
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


/* ==== source lines 850-891 ==== */
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


/* ==== source lines 926-938 ==== */
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

/* ==== source lines 940-951 ==== */
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



/* ==== source lines 990-1003 ==== */
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

/* ==== source lines 1036-1239 ==== */
function renderFront(p){
 var panels=fpAssign(p);
 var hl=highlightsOf(p);
 var html='';
 if(hl){html+='<div class="fp-highlights"><h4 class="besond">'+t('highlights')+'</h4><ul class="besond-list">'+hl.map(function(x){return '<li>'+x+'</li>'}).join('')+'</ul></div>';}
 if(panels.length){
  html+='<h4 class="fp-section">'+t('front_h')+'</h4>';
  panels.forEach(function(pk){var fp=FP[pk];var ph=PANEL_HL[pk][LANG]||PANEL_HL[pk].de;
   html+='<div class="fp"><h4 class="fp-title">'+fp.n+'</h4>'+
    '<div class="fp-body"><div class="fp-panel">'+(fp.img?'<img referrerpolicy="no-referrer" class="fp-photo" src="'+SRC(fullImg(fp.img))+'" onerror="imgFail(this,&#39;'+fp.n.replace(/'/g,'')+'&#39;,&#39;'+fp.img+'&#39;)" alt="'+fp.n+'">':panelSVG(fp.big))+'</div>'+
    '<div class="fp-right"><h5 class="besond">'+t('front_bes')+'</h5><ul class="besond-list fp-list">'+ph.map(function(x){return '<li>'+x+'</li>'}).join('')+'</ul></div></div></div>';
  });
  var main=FP[panels[panels.length-1]];
  html+='<div class="fp-ctrls"><h5 class="besond">'+t('controls')+'</h5><ul class="besond-list">'+main.ctrl.map(function(c){return '<li>'+(CTRL[c][LANG]||CTRL[c].de)+'</li>'}).join('')+'</ul></div>';
 } else if(!hl){
  var feats=deriveFeat(p);html+='<div class="featlist">'+feats.map(function(k){return '<div class="fitem">'+FEAT[k].svg+'<span>'+featLabel(k)+'</span></div>'}).join('')+'</div>';
 }
 document.getElementById('tab-feat').innerHTML=html;
}
function renderProcs(p){
  var box=document.getElementById('pProcs');box.innerHTML='';
  deriveFeat(p).forEach(k=>{var f=FEAT[k];if(!f)return;var el=document.createElement('div');el.className='procbadge'+(f.tile?' tile':'');
    el.innerHTML='<div class="ic">'+f.svg+'</div><div class="lb">'+featLabel(k)+'</div>';box.appendChild(el);});
  var mats=matOf(p);
  if(mats.length){var row=document.createElement('div');row.className='matchips';
    row.innerHTML=mats.map(m=>'<span class="matchip"><b>'+m+'</b>'+matLabel(m)+'</span>').join('');box.appendChild(row);}
}
function renderMeta(p){
  document.getElementById('pMeta').innerHTML=
   '<div class="m"><span class="lab">'+t('availability')+'</span><span class="val ok">'+t('avail_val')+'</span></div>'+
   '<div class="m"><span class="lab">'+t('brand')+'</span><span class="val">MAHE</span></div>'+
   '<div class="m"><span class="lab">'+t('artno')+'</span><span class="val">'+p.id.toUpperCase()+'</span></div>';
}
function renderTabs(p){
  var rows=Object.entries(p.specs).map(([k,v])=>'<div class="r"><span class="k">'+trK(k)+'</span><span class="v">'+trV(v)+'</span></div>').join('');
  document.getElementById('tab-tech').innerHTML='<div class="spectable"><h4>'+t('techdata')+'</h4>'+rows+'</div>';
  renderFront(p);
  var acc=relatedAcc(p);
  if(!acc.length){document.getElementById('tab-acc').innerHTML='<p class="noacc">'+t('no_acc')+'</p>';}
  else{document.getElementById('tab-acc').innerHTML='<div class="accgrid">'+acc.map(id=>{var a=P.find(x=>x.id===id);
     return '<div class="acccard" onclick="goProd(\''+id+'\')"><div class="im"><img referrerpolicy="no-referrer" src="'+SRC(a.img)+'" onerror="imgFail(this,\''+a.name.replace(/'/g,'')+'\',\''+a.img+'\')" alt=""></div><div class="bd"><div class="vt">'+a.vt+'</div><h4>'+a.name+'</h4><p>'+pDesc(a)+'</p></div></div>';}).join('')+'</div>';}
  document.getElementById('tab-dl').innerHTML='<div class="dlrow">'+
    '<div class="dlitem" onclick="toast(t(\'dl_soon\'))"><div class="ico">PDF</div><div class="nm">'+t('dl_datasheet')+'<span>'+p.name+'</span></div><span class="arw">↓</span></div>'+
    '<div class="dlitem" onclick="toast(t(\'dl_soon\'))"><div class="ico">PDF</div><div class="nm">'+t('dl_manual')+'<span>'+p.name+'</span></div><span class="arw">↓</span></div>'+
    '<div class="dlitem" onclick="toast(t(\'dl_soon\'))"><div class="ico">PDF</div><div class="nm">'+t('dl_cat')+'<span>MAHE</span></div><span class="arw">↓</span></div></div>';
}
function switchTab(name){
  document.querySelectorAll('.tabbtn').forEach(b=>b.classList.toggle('active',b.dataset.tab===name));
  document.querySelectorAll('.tabpane').forEach(pn=>pn.classList.remove('active'));
  var el=document.getElementById('tab-'+name); if(el)el.classList.add('active');
}
document.getElementById('pTabbar').addEventListener('click',e=>{var b=e.target.closest('.tabbtn');if(b)switchTab(b.dataset.tab);});

/* ---------- Home cards ---------- */
const hc=document.getElementById('homeCards');
function buildHome(){hc.innerHTML='';CATS.forEach((c,i)=>{
  const n=P.filter(p=>p.cat===c.id).length;
  const el=document.createElement('div');el.className='cat';el.onclick=()=>goCat(c.id);
  el.innerHTML=`<div class="idx">0${i+1} · ${n} ${t('devices')}</div><div class="pk">${PK[c.pk]}</div><h3>${catT(c)}</h3><p>${catD(c)}</p><div class="go">${t('card_open')}</div>`;
  hc.appendChild(el);
});}

/* ---------- Mega menu ---------- */
const ms=document.getElementById('megaScroll');
function buildMega(){ms.innerHTML='';CATS.forEach(c=>{
  const g=document.createElement('div');g.className='mgroup';
  const subs=c.subs.map((s,i)=>`<a onclick="goCat('${c.id}','${s.replace(/'/g,"")}');closeMega()"><span class="num">${String(i+1).padStart(2,'0')}</span><b>${subT(s)}</b><span>→</span></a>`).join('');
  g.innerHTML=`<button aria-expanded="false"><span>${catT(c)}</span><span class="chev">▸</span></button><div class="sub">${subs}</div>`;
  g.querySelector('button').onclick=()=>{g.classList.toggle('open')};
  ms.appendChild(g);
});
[['n_service','kontakt'],['n_downloads','downloads'],['n_warranty','kontakt'],['n_process','verfahren'],['n_contact','kontakt']].forEach(([key,view])=>{
  const g=document.createElement('div');g.className='mgroup';
  g.innerHTML=`<button onclick="${view?"goView('"+view+"');":""}closeMega()"><span>${t(key)}</span><span class="chev">→</span></button>`;
  ms.appendChild(g);
});}
const fp=document.getElementById('fprod');
function buildFprod(){fp.innerHTML='';CATS.forEach(c=>{const li=document.createElement('li');li.innerHTML=`<a onclick="goCat('${c.id}')">${catT(c)}</a>`;fp.appendChild(li)});}
buildHome();buildMega();buildFprod();

/* ---------- Views ---------- */
function show(id){document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));document.getElementById('view-'+id).classList.add('active');window.scrollTo({top:0})}
function goHome(){show('home');closeAll()}
function goView(id){show(id);closeAll();if(id==='verfahren')renderVerfahren();if(id==='downloads')renderDownloads();}

let curCat=null,curSub=null;
function goCat(catId,sub){
  curCat=CATS.find(c=>c.id===catId);curSub=sub||null;closeAll();
  document.getElementById('catTitle').textContent=catT(curCat);
  document.getElementById('catDesc').textContent=catD(curCat);
  document.getElementById('crumbs').innerHTML=`<a onclick="goHome()">${t('c_home')}</a><span class="sep">›</span><a onclick="goCat('${curCat.id}')">${t('c_products')}</a><span class="sep">›</span>${catT(curCat)}`;
  const chips=document.getElementById('chips');chips.innerHTML='';
  const all=document.createElement('button');all.className='chip'+(curSub?'':' active');all.textContent=t('chip_all');all.onclick=()=>goCat(catId);chips.appendChild(all);
  curCat.subs.forEach(s=>{const b=document.createElement('button');b.className='chip'+(curSub===s?' active':'');b.textContent=subT(s);b.onclick=()=>goCat(catId,s);chips.appendChild(b)});
  renderProducts();
  show('catalog');
}
function renderProducts(){
  let list=P.filter(p=>p.cat===curCat.id);
  if(curSub)list=list.filter(p=>p.sub===curSub);
  document.getElementById('secTitle').textContent=curSub?subT(curSub):t('sec_all');
  document.getElementById('secCount').textContent=list.length+' '+t('items')+' · '+t('poa');
  const g=document.getElementById('pgrid');g.innerHTML='';
  list.forEach(p=>{
    const specs=Object.entries(p.specs).slice(0,3).map(([k,v])=>`<span>${trV(v)}</span>`).join('');
    const el=document.createElement('div');el.className='pcard';el.onclick=()=>goProd(p.id);
    el.innerHTML=`<div class="imgbox"><span class="vtag">${p.vt}</span><img loading="lazy" referrerpolicy="no-referrer" src="${SRC(p.img)}" alt="${p.name}" onerror="imgFail(this,'${p.name.replace(/'/g,"")}','${p.img}')"></div>
      <div class="body"><h3>${p.name}</h3><p>${pDesc(p)}</p><div class="spec">${specs}</div></div>
      <div class="foot"><span class="poa">${t('poa')}</span><button class="add" onclick="event.stopPropagation();addCart('${p.id}')">${t('inquire')}</button></div>`;
    g.appendChild(el);
  });
}
function goProd(id){
  const p=P.find(x=>x.id===id);curCat=CATS.find(c=>c.id===p.cat);closeAll();window.__curProd=id;
  document.getElementById('pCrumbs').innerHTML=`<a onclick="goHome()">${t('c_home')}</a><span class="sep">›</span><a onclick="goCat('${p.cat}')">${catT(curCat)}</a><span class="sep">›</span><a onclick="goCat('${p.cat}','${p.sub.replace(/'/g,"")}')">${subT(p.sub)}</a><span class="sep">›</span>${p.name}`;
  document.getElementById('pVtag').textContent=p.vt;
  const im=document.getElementById('pImg');im.dataset.step='';im.onerror=function(){imgFail(im,p.name,p.img)};im.src=SRC(fullImg(p.img));im.alt=p.name;
  document.getElementById('pKicker').textContent=catT(curCat)+' · MAHE';
  document.getElementById('pName').textContent=p.name;
  document.getElementById('pDesc').textContent=pDesc(p);
  renderProcs(p);renderMeta(p);renderTabs(p);switchTab('feat');var _fb=document.querySelector('.tabbtn[data-tab="feat"]');if(_fb)_fb.textContent=fpAssign(p).length?t('tab_feat'):t('highlights');
  document.getElementById('pAdd').onclick=()=>addCart(p.id);
  show('product');
}
function doSearch(e){e.preventDefault();const q=document.getElementById('q').value.trim().toLowerCase();if(!q)return;
  const hit=P.filter(p=>(p.name+' '+p.desc+' '+p.vt+' '+p.sub).toLowerCase().includes(q));
  if(!hit.length){toast(t('no_hits')+' "'+q+'"');return}
  curCat={id:'_search',t:'',d:'',subs:[]};curSub=null;
  document.getElementById('catTitle').textContent=t('c_search');
  document.getElementById('catDesc').textContent=hit.length+' · '+q;
  document.getElementById('crumbs').innerHTML=`<a onclick="goHome()">${t('c_home')}</a><span class="sep">›</span>${t('c_search')}`;
  document.getElementById('chips').innerHTML='';
  document.getElementById('secTitle').textContent=t('c_search');
  document.getElementById('secCount').textContent=hit.length+' '+t('items');
  const g=document.getElementById('pgrid');g.innerHTML='';
  hit.forEach(p=>{const specs=Object.entries(p.specs).slice(0,3).map(([k,v])=>`<span>${trV(v)}</span>`).join('');
    const el=document.createElement('div');el.className='pcard';el.onclick=()=>goProd(p.id);
    el.innerHTML=`<div class="imgbox"><span class="vtag">${p.vt}</span><img loading="lazy" referrerpolicy="no-referrer" src="${SRC(p.img)}" onerror="imgFail(this,'${p.name.replace(/'/g,"")}','${p.img}')" alt="${p.name}"></div><div class="body"><h3>${p.name}</h3><p>${pDesc(p)}</p><div class="spec">${specs}</div></div><div class="foot"><span class="poa">${t('poa')}</span><button class="add" onclick="event.stopPropagation();addCart('${p.id}')">${t('inquire')}</button></div>`;
    g.appendChild(el)});
  show('catalog');closeAll();
}

/* ---------- Cart / Anfrage ---------- */
function addCart(id){if(!cart.includes(id)){cart.push(id);renderCart();toast(t('added'))}else{toast(t('already'))}}
function rmCart(id){cart=cart.filter(x=>x!==id);renderCart()}
function renderCart(){
  document.getElementById('cnt').textContent=cart.length;
  const box=document.getElementById('cartItems'),form=document.getElementById('cartForm');
  if(!cart.length){box.innerHTML='<div class="empty">'+t('cart_empty')+'</div>';form.style.display='none';return}
  form.style.display='block';box.innerHTML='';
  cart.forEach(id=>{const p=P.find(x=>x.id===id);const el=document.createElement('div');el.className='citem';
    el.innerHTML=`<div class="th"><img referrerpolicy="no-referrer" src="${SRC(p.img)}" onerror="imgFail(this,'${p.name.replace(/'/g,"")}','${p.img}')" alt=""></div><div class="n"><b>${p.name}</b><span>${p.vt} · ${t('poa')}</span></div><button class="rm" onclick="rmCart('${id}')" aria-label="Entfernen">✕</button>`;
    box.appendChild(el)});
}
function sendInquiry(){
  const name=document.getElementById('cName').value||'—';
  const mail=document.getElementById('cMail').value||'—';
  const msg=document.getElementById('cMsg').value||'';
  const lines=cart.map(id=>'- '+P.find(x=>x.id===id).name).join('%0D%0A');
  const body=`Anfrage von: ${name}%0D%0AE-Mail: ${mail}%0D%0A%0D%0AGewünschte Geräte:%0D%0A${lines}%0D%0A%0D%0ANachricht:%0D%0A${encodeURIComponent(msg)}`;
  window.location.href=`mailto:info@ves-tech.ch?subject=${encodeURIComponent('Anfrage VES-TECH ('+cart.length+' Artikel)')}&body=${body}`;
  toast(t('opened_mail'));
}
function sendKontakt(){
  const name=document.getElementById('kName').value||'—';const mail=document.getElementById('kMail').value||'—';
  const tel=document.getElementById('kTel').value||'—';const msg=document.getElementById('kMsg').value||'';
  const body=`Name: ${name}%0D%0AE-Mail: ${mail}%0D%0ATelefon: ${tel}%0D%0A%0D%0A${encodeURIComponent(msg)}`;
  window.location.href=`mailto:info@ves-tech.ch?subject=${encodeURIComponent('Kontaktanfrage VES-TECH')}&body=${body}`;
  toast(t('opened_mail'));
}

/* ---------- Drawers ---------- */
const scrim=document.getElementById('scrim');
function openMega(){document.getElementById('mega').classList.add('open');scrim.classList.add('open');document.body.style.overflow='hidden'}
function closeMega(){document.getElementById('mega').classList.remove('open');if(!document.getElementById('cart').classList.contains('open')){scrim.classList.remove('open');document.body.style.overflow=''}}
function openCart(){renderCart();document.getElementById('cart').classList.add('open');scrim.classList.add('open');document.body.style.overflow='hidden'}
function closeCart(){document.getElementById('cart').classList.remove('open');if(!document.getElementById('mega').classList.contains('open')){scrim.classList.remove('open');document.body.style.overflow=''}}
function closeAll(){closeMega();closeCart()}
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeAll()});

let tt;function toast(m){const t2=document.getElementById('toast');t2.textContent=m;t2.classList.add('show');clearTimeout(tt);tt=setTimeout(()=>t2.classList.remove('show'),2200)}

/* ---------- Sprachumschaltung ---------- */
function applyLang(){
  document.documentElement.lang = LANG==='de'?'de-CH':LANG;
  document.querySelectorAll('[data-i18n]').forEach(el=>{el.textContent=t(el.getAttribute('data-i18n'));});
  document.querySelectorAll('[data-i18n-ph]').forEach(el=>{el.setAttribute('placeholder',t(el.getAttribute('data-i18n-ph')));});
  // Hero-Titel (zwei Teile)
  const hp=document.getElementById('heroPre'),ha=document.getElementById('heroAcc');
  if(hp)hp.textContent=t('hero_pre'); if(ha)ha.textContent=t('hero_acc');
  buildHome();buildMega();buildFprod();
  // aktuelle Ansicht neu zeichnen
  if(document.getElementById('view-catalog').classList.contains('active')&&curCat&&curCat.id!=='_search'){goCat(curCat.id,curSub);}
  else if(document.getElementById('view-product').classList.contains('active')&&window.__curProd){goProd(window.__curProd);}
  if(document.getElementById('view-verfahren').classList.contains('active'))renderVerfahren();
  if(document.getElementById('view-downloads').classList.contains('active'))renderDownloads();
  renderCart();
  document.querySelectorAll('.langs button').forEach(b=>b.setAttribute('aria-pressed', b.dataset.lang===LANG?'true':'false'));
}
function setLang(l){LANG=l;applyLang();}
document.querySelectorAll('.langs button').forEach(b=>{b.addEventListener('click',()=>setLang(b.dataset.lang));});

renderCart();
applyLang();
