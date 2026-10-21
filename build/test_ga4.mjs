// Exercise the actual optional GA4 adapter, never Google's production collector.
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {test} from 'node:test';
const init = createRequire(import.meta.url)('../assets/js/analytics.js');
function fixture({choice='granted',oldChoice=null,search='',referrer='',signal=false,ahrefs=false,id='G-ABC123DEF4',campaigns={}}={}) {
 const appended=[],listeners={},sent=[],saved=new Map(),deleted=[];
 const panel={hidden:true,dataset:{host:'www.ves-tech.ch',ga4Id:id,ahrefsKey:ahrefs?'public-key':'',token:''},
   addEventListener:(k,f)=>listeners['panel-'+k]=f, querySelector:()=>({focus(){}})};
 const settings={setAttribute(){},focus(){},addEventListener:(k,f)=>listeners['settings-'+k]=f};
 if(choice)saved.set('vt.analytics.consent.v3',JSON.stringify({value:choice,at:Date.now()-1000}));
 if(oldChoice)saved.set('vt.analytics.consent.v2',JSON.stringify({value:oldChoice,at:Date.now()-1000}));
 const config={products:{'beta-dx':'schweissgeraete'},paths:['/kontakt/','/produkte/schweissgeraete/beta-dx/'],contactPath:'/kontakt/',campaigns,topics:['tig'],servicePaths:{}};
 const context={URL,Date,navigator:{globalPrivacyControl:signal},location:{hostname:'www.ves-tech.ch',origin:'https://www.ves-tech.ch',pathname:'/kontakt/',search,hash:'',reload(){this.reloaded=true;}},
 localStorage:{getItem:k=>saved.get(k)||null,setItem:(k,v)=>saved.set(k,v)},sessionStorage:{getItem:()=>null,setItem(){},removeItem(){}},
 document:{referrer,visibilityState:'visible',getElementById:id=>id==='analyticsConsent'?panel:id==='analyticsSettings'?settings:null,
 querySelector:()=>({href:'https://www.ves-tech.ch/kontakt/'}),addEventListener:(k,f)=>listeners['doc-'+k]=f,
 createElement:()=>({dataset:{},setAttribute(){}}),body:{appendChild:s=>appended.push(s)},
 get cookie(){return 'vt_ga=own; vt_ga_ABC123DEF4=own; customer_cookie=leave';},set cookie(x){deleted.push(x);}},
 window:{VT:{lang:'de',analytics:config},addEventListener:(k,f)=>listeners[k]=f,AhrefsAnalytics:{sendEvent:(n,o)=>sent.push([n,o])}}};
 init(context);
 return {context,panel,appended,listeners,deleted,sent,commands:()=>Array.from(context.window.dataLayer||[],x=>Array.from(x)),
 load(){for(const s of appended)s.onload?.();},
 choose(value){listeners['panel-click']({target:{closest:()=>({dataset:{consent:value}})}});}};
}

test('GA4 performs no network or command buffering without fresh consent',()=>{
 for(const options of [{choice:null},{choice:'denied'},{choice:null,oldChoice:'granted'},{choice:'granted',signal:true},{choice:'granted',search:'?email=private@example.invalid'},{choice:'granted',referrer:'https://external.invalid/private'}]) {
  const f=fixture(options);assert.equal(f.appended.length,0);assert.equal(f.commands().length,0);
  assert.equal(f.context.window.VTAnalytics.track('inquiry_success'),false);
 }
 const old=fixture({choice:null,oldChoice:'denied'});assert.equal(old.panel.hidden,true);assert.equal(old.appended.length,0);
});
test('GA4-only loads once, uses denied ads consent and emits one sanitised page view',()=>{
 const f=fixture({search:'?topic=tig'});
 assert.equal(f.appended.length,1);assert.equal(f.appended[0].src,'https://www.googletagmanager.com/gtag/js?id=G-ABC123DEF4');
 assert.equal(f.appended[0].referrerPolicy,'no-referrer');
 const cfg=f.commands().find(x=>x[0]==='config')[2];
 assert.equal(cfg.send_page_view,false);assert.equal(cfg.allow_google_signals,false);assert.equal(cfg.allow_ad_personalization_signals,false);
 assert.equal(cfg.cookie_domain,'none');assert.equal(cfg.cookie_expires,15552000);assert.equal(cfg.cookie_update,false);
 assert.equal(cfg.page_location,'https://www.ves-tech.ch/kontakt/');assert.equal(cfg.page_referrer,'');
 assert.equal(f.commands()[0][2].ad_user_data,'denied');assert.equal(f.commands()[0][2].ad_personalization,'denied');
 f.load();assert.equal(f.commands().filter(x=>x[0]==='event'&&x[1]==='page_view').length,1);
 f.choose('granted');assert.equal(f.appended.length,1);
});
test('customer inputs cannot enter custom parameters and queue is post-consent and bounded',()=>{
 const f=fixture();
 for(let i=0;i<45;i++)f.context.window.VTAnalytics.track('inquiry_submit',{email:'private@example.invalid',message:'SECRET',user_id:'PRIVATE',form_type:'contact'});
 f.load();const events=f.commands().filter(x=>x[0]==='event');
 assert.equal(events.filter(x=>x[1]==='inquiry_submit').length,30);
 assert.doesNotMatch(JSON.stringify(events),/private|SECRET|PRIVATE|email|message|user_id/);
 assert.equal(f.context.window.VTAnalytics.track('unknown_email_event'),false);
});
test('failure of either tracker cannot block the other tracker',()=>{
 const a=fixture({ahrefs:true});a.appended.find(x=>x.src.includes('ahrefs')).onerror();a.appended.find(x=>x.src.includes('googletagmanager')).onload();
 assert.equal(a.context.window.VTAnalytics.track('contact_phone'),true);
 assert.equal(a.commands().filter(x=>x[1]==='contact_phone').length,1);
 const b=fixture({ahrefs:true});b.appended.find(x=>x.src.includes('googletagmanager')).onerror();b.appended.find(x=>x.src.includes('ahrefs')).onload();
 assert.equal(b.context.window.VTAnalytics.track('contact_phone'),true);assert.equal(b.sent.filter(x=>x[0]==='contact_phone').length,1);
});
test('withdrawal immediately opts out, clears owned cookies only and discards pending actions',()=>{
 const f=fixture();f.load();f.choose('denied');
 assert.equal(f.context.window['ga-disable-G-ABC123DEF4'],true);assert.equal(f.context.location.reloaded,true);assert.equal(f.commands().length,0);
 assert.equal(f.deleted.length,2);assert.ok(f.deleted.every(x=>x.startsWith('vt_ga')&&x.includes('Max-Age=0')));
 assert.equal(f.context.window.VTAnalytics.track('inquiry_success'),false);
});
test('unknown click IDs and arbitrary query parameters stay excluded',()=>{
 for(const search of ['?gclid=private','?msclkid=private','?topic=tig&email=private','?topic=constructor','?topic=tig&topic=tig'])assert.equal(fixture({search}).appended.length,0);
});
test('fresh consent is stored under v3 and cannot reuse a previous v2 grant',()=>{
 const f=fixture({choice:null,oldChoice:'granted'});assert.equal(f.appended.length,0);f.choose('granted');assert.equal(f.appended.length,1);f.load();assert.equal(f.commands().filter(x=>x[1]==='page_view').length,1);
});
test('only a click on a Brevo hosted signup link is counted, never a subscriber or address',()=>{
 const f=fixture();f.load();
 const link={getAttribute:()=> 'https://forms.sibforms.com/serve/PUBLIC_FORM==',hasAttribute:x=>x==='data-newsletter'};
 f.listeners['doc-click']({type:'click',target:{closest:()=>link},stopImmediatePropagation(){}});
 const event=f.commands().find(x=>x[0]==='event'&&x[1]==='newsletter_open');assert.ok(event);assert.doesNotMatch(JSON.stringify(event),/sibforms|PUBLIC_FORM|email/);
});

test('reviewed newsletter attribution reaches GA4 as email without subscriber identifiers',()=>{
 const row={source:'ves-tech-newsletter',medium:'email',campaign:'tig-montage-2026',content:'technical-2026-tig-de'};
 const search='?'+new URLSearchParams(Object.fromEntries(Object.entries(row).map(([k,v])=>['utm_'+k,v])));
 const f=fixture({search,campaigns:{newsletter:row}});f.load();
 const cfg=f.commands().find(x=>x[0]==='config')[2];
 assert.equal(cfg.campaign_source,row.source);assert.equal(cfg.campaign_medium,'email');
 assert.equal(cfg.campaign_name,row.campaign);assert.equal(cfg.campaign_content,row.content);
 assert.equal(fixture({search:search+'&email=private@example.invalid',campaigns:{newsletter:row}}).appended.length,0);
});
