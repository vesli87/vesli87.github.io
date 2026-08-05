/* =========================================================================
   VES-TECH Swiss — Frontend
   Die Seiten sind vollständig vorgerendert; dieses Skript ist reine
   Anreicherung: Suche, Anfrageliste, Schubladen, Tabs, Formularversand.
   Ohne JavaScript bleibt die Website vollständig lesbar und navigierbar.
   ========================================================================= */
(function () {
  'use strict';

  var VT = window.VT || {};
  var T = VT.i18n || {};
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var t = function (k, d) { return T[k] || d || k; };

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function debounce(fn, ms) {
    var id; return function () {
      var a = arguments, self = this;
      clearTimeout(id); id = setTimeout(function () { fn.apply(self, a); }, ms);
    };
  }

  /* ---------------------------------------------------------------- Toast */
  var toastTimer;
  function toast(msg) {
    var el = $('#toast'); if (!el) return;
    el.textContent = msg; el.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { el.classList.remove('show'); }, 2600);
  }

  /* -------------------------------------------------------------- Storage */
  /* localStorage kann in privaten Fenstern werfen – immer absichern. */
  var store = {
    get: function (k, d) {
      try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : d; }
      catch (e) { return d; }
    },
    set: function (k, v) {
      try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* egal */ }
    }
  };

  /* ============================ Anfrageliste ============================ */
  var CART_KEY = 'vt.cart.v1';
  var cart = store.get(CART_KEY, []);
  if (!Array.isArray(cart)) cart = [];

  function saveCart() { store.set(CART_KEY, cart); renderCart(); }

  function addCart(item) {
    var hit = null;
    for (var i = 0; i < cart.length; i++) if (cart[i].id === item.id) hit = cart[i];
    if (hit) { hit.qty = (hit.qty || 1) + 1; toast(t('already')); }
    else { cart.push({ id: item.id, name: item.name, url: item.url, img: item.img, qty: 1 }); toast(t('added')); }
    saveCart();
  }
  function rmCart(id) {
    cart = cart.filter(function (x) { return x.id !== id; });
    saveCart();
  }
  function setQty(id, q) {
    cart.forEach(function (x) { if (x.id === id) x.qty = Math.max(1, Math.min(99, q)); });
    saveCart();
  }

  function renderCart() {
    var count = cart.reduce(function (a, b) { return a + (b.qty || 1); }, 0);
    $$('#cnt').forEach(function (el) { el.textContent = count; });
    var box = $('#cartItems'), form = $('#cartForm');
    if (!box) return;
    if (!cart.length) {
      box.innerHTML = '<div class="empty">' + esc(t('cart_empty')) + '</div>';
      if (form) form.hidden = true;
      return;
    }
    if (form) form.hidden = false;
    box.innerHTML = cart.map(function (x) {
      return '<div class="citem">' +
        '<a class="th" href="' + esc(x.url || '#') + '">' +
        (x.img ? '<img src="' + esc(x.img) + '" alt="" width="60" height="60" loading="lazy">' : '') +
        '</a>' +
        '<div class="n"><a href="' + esc(x.url || '#') + '"><b>' + esc(x.name) + '</b></a>' +
        '<span>' + esc(t('poa')) + '</span>' +
        '<span class="qty"><button type="button" data-qty="-" data-id="' + esc(x.id) + '" aria-label="−">−</button>' +
        '<output>' + (x.qty || 1) + '</output>' +
        '<button type="button" data-qty="+" data-id="' + esc(x.id) + '" aria-label="+">+</button></span></div>' +
        '<button class="rm" type="button" data-rm="' + esc(x.id) + '" aria-label="✕">✕</button></div>';
    }).join('');
  }

  document.addEventListener('click', function (ev) {
    var add = ev.target.closest('[data-add]');
    if (add) {
      ev.preventDefault();
      addCart({
        id: add.getAttribute('data-add'),
        name: add.getAttribute('data-name') || add.getAttribute('data-add'),
        url: add.getAttribute('data-url') || '',
        img: add.getAttribute('data-img') || ''
      });
      return;
    }
    var rm = ev.target.closest('[data-rm]');
    if (rm) { rmCart(rm.getAttribute('data-rm')); return; }
    var q = ev.target.closest('[data-qty]');
    if (q) {
      var id = q.getAttribute('data-id');
      var cur = 1;
      cart.forEach(function (x) { if (x.id === id) cur = x.qty || 1; });
      setQty(id, q.getAttribute('data-qty') === '+' ? cur + 1 : cur - 1);
    }
  });

  /* ============================== Schubladen ============================ */
  var lastFocus = null;

  function openPanel(which) {
    var el = $('#' + which); if (!el) return;
    lastFocus = document.activeElement;
    el.classList.add('open'); el.setAttribute('aria-hidden', 'false');
    $('#scrim').classList.add('open');
    document.body.style.overflow = 'hidden';
    var btn = $('[data-open="' + which + '"]');
    if (btn) btn.setAttribute('aria-expanded', 'true');
    if (which === 'cart') renderCart();
    var f = el.querySelector('a,button,input');
    if (f) f.focus();
  }
  function closePanel(which) {
    var el = $('#' + which); if (!el) return;
    el.classList.remove('open'); el.setAttribute('aria-hidden', 'true');
    var btn = $('[data-open="' + which + '"]');
    if (btn) btn.setAttribute('aria-expanded', 'false');
    if (!$$('.mega.open, .cart.open').length) {
      $('#scrim').classList.remove('open');
      document.body.style.overflow = '';
    }
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  function closeAll() { closePanel('mega'); closePanel('cart'); }

  document.addEventListener('click', function (ev) {
    var o = ev.target.closest('[data-open]');
    if (o) { ev.preventDefault(); openPanel(o.getAttribute('data-open')); return; }
    var c = ev.target.closest('[data-close]');
    if (c) {
      ev.preventDefault();
      var w = c.getAttribute('data-close');
      if (w === 'all') closeAll(); else closePanel(w);
    }
  });
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') { closeAll(); closeSuggest(); }
  });

  /* Akkordeon im Menü – die Links darin funktionieren auch ohne JS */
  $$('.mgroup > button').forEach(function (b) {
    b.addEventListener('click', function () {
      var g = b.parentNode, open = g.classList.toggle('open');
      b.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  });

  /* ================================= Tabs =============================== */
  var tabbar = $('.tabbar');
  if (tabbar) {
    tabbar.addEventListener('click', function (ev) {
      var b = ev.target.closest('.tabbtn'); if (!b) return;
      var name = b.getAttribute('data-tab');
      $$('.tabbtn').forEach(function (x) {
        var on = x.getAttribute('data-tab') === name;
        x.classList.toggle('active', on);
        x.setAttribute('aria-selected', on ? 'true' : 'false');
      });
      $$('.tabpane').forEach(function (p) {
        p.classList.toggle('active', p.id === 'tab-' + name);
      });
    });
    tabbar.addEventListener('keydown', function (ev) {
      if (ev.key !== 'ArrowRight' && ev.key !== 'ArrowLeft') return;
      var btns = $$('.tabbtn', tabbar);
      var i = btns.indexOf(document.activeElement);
      if (i < 0) return;
      ev.preventDefault();
      var n = (i + (ev.key === 'ArrowRight' ? 1 : -1) + btns.length) % btns.length;
      btns[n].focus(); btns[n].click();
    });
  }

  /* ================================ Lupe ================================ */
  /* Bilder mit .zoomable lassen sich bildschirmfuellend ansehen. Gebraucht wird
     das dort, wo es auf Details ankommt: Verarbeitung der Maschine, Beschriftung
     eines Frontpanels. Das Overlay entsteht erst beim ersten Klick - wer nie
     zoomt, laedt auch nichts nach. */
  (function () {
    var bilder = $$('.zoomable');
    if (!bilder.length) return;

    // Groesste Datei aus dem srcset. Die Anzeige nimmt je nach Platz eine
    // kleine Stufe; in der Lupe wollen wir immer die groesste.
    function gross(img) {
      var beste = img.currentSrc || img.src, breite = 0;
      (img.getAttribute('srcset') || '').split(',').forEach(function (teil) {
        var st = teil.trim().split(/\s+/);
        var w = parseInt((st[1] || '').replace('w', ''), 10) || 0;
        if (st[0] && w >= breite) { breite = w; beste = st[0]; }
      });
      return beste;
    }

    // Hinweiszeichen auf die Container setzen, in denen ein zoombares Bild sitzt.
    bilder.forEach(function (img) {
      var box = img.closest('.dimg') || img.closest('.fp-panel');
      if (box && !box.querySelector('.lupe-hint')) {
        var s = document.createElement('span');
        s.className = 'lupe-hint';
        s.setAttribute('aria-hidden', 'true');
        s.textContent = '\u2315';                 // Lupenzeichen
        box.appendChild(s);
      }
      img.setAttribute('title', t('lupe_open', 'Bild vergrössern'));
    });

    var box, buehne, bild, txt, vor, zurueck, zuletzt = null, gruppe = [], idx = 0;

    function bauen() {
      box = document.createElement('div');
      box.className = 'lupe';
      box.setAttribute('role', 'dialog');
      box.setAttribute('aria-modal', 'true');
      box.hidden = true;
      box.innerHTML =
        '<div class="lupe-kopf">' +
          '<button class="lupe-btn" type="button" data-lupe="zoom" aria-label="' +
            esc(t('lupe_in', 'Näher heran')) + '">+</button>' +
          '<button class="lupe-btn" type="button" data-lupe="zu" aria-label="' +
            esc(t('lupe_close', 'Schliessen')) + '">\u2715</button>' +
        '</div>' +
        '<div class="lupe-buehne"><img alt=""></div>' +
        '<div class="lupe-fuss">' +
          '<button class="lupe-nav" type="button" data-lupe="-1" aria-label="&#8249;">\u2039</button>' +
          '<span class="lupe-txt"></span>' +
          '<button class="lupe-nav" type="button" data-lupe="1" aria-label="&#8250;">\u203a</button>' +
        '</div>';
      document.body.appendChild(box);
      buehne = $('.lupe-buehne', box);
      bild = $('img', buehne);
      txt = $('.lupe-txt', box);
      zurueck = $('[data-lupe="-1"]', box);
      vor = $('[data-lupe="1"]', box);

      box.addEventListener('click', function (ev) {
        var b = ev.target.closest('[data-lupe]');
        if (b) {
          var v = b.getAttribute('data-lupe');
          if (v === 'zu') { schliessen(); }
          else if (v === 'zoom') { box.classList.toggle('gross'); }
          else { zeigen(idx + parseInt(v, 10)); }
          return;
        }
        if (ev.target === bild) { box.classList.toggle('gross'); return; }
        if (ev.target === buehne || ev.target === box) schliessen();
      });
    }

    function zeigen(n) {
      idx = (n + gruppe.length) % gruppe.length;
      var q = gruppe[idx];
      box.classList.remove('gross');
      bild.src = gross(q);
      bild.alt = q.getAttribute('alt') || '';
      txt.textContent = q.getAttribute('alt') || '';
      var mehr = gruppe.length > 1;
      zurueck.hidden = !mehr;
      vor.hidden = !mehr;
    }

    function oeffnen(img) {
      if (!box) bauen();
      // Gruppe: die Bilder derselben Galerie, sonst alle zoombaren der Seite.
      var gal = img.closest('[data-gal]');
      gruppe = gal ? $$('.zoomable', gal) : bilder;
      if (gruppe.indexOf(img) < 0) gruppe = [img];
      zuletzt = document.activeElement;
      box.hidden = false;
      document.body.classList.add('lupe-offen');
      zeigen(gruppe.indexOf(img));
      $('[data-lupe="zu"]', box).focus();
    }

    function schliessen() {
      if (!box || box.hidden) return;
      box.hidden = true;
      box.classList.remove('gross');
      bild.removeAttribute('src');
      document.body.classList.remove('lupe-offen');
      if (zuletzt && zuletzt.focus) zuletzt.focus();
    }

    document.addEventListener('click', function (ev) {
      var img = ev.target.closest('.zoomable');
      if (!img) return;
      ev.preventDefault();
      oeffnen(img);
    });

    document.addEventListener('keydown', function (ev) {
      if (!box || box.hidden) return;
      if (ev.key === 'Escape') { ev.preventDefault(); schliessen(); }
      else if (ev.key === 'ArrowRight' && gruppe.length > 1) { ev.preventDefault(); zeigen(idx + 1); }
      else if (ev.key === 'ArrowLeft' && gruppe.length > 1) { ev.preventDefault(); zeigen(idx - 1); }
    });
  }());

  /* =============================== Hero ================================= */
  /* Wechselbild alle 5 Sekunden. Drei Dinge, die ein Karussell sonst falsch
     macht: Es laeuft weiter, waehrend jemand liest (deshalb Pause bei Hover und
     Tastaturfokus), es laeuft im Hintergrundtab weiter (deshalb der
     visibilitychange-Handler), und es ignoriert Menschen, die Bewegung
     ausdruecklich abbestellt haben (deshalb prefers-reduced-motion). */
  (function () {
    var hero = $('[data-hero]');
    if (!hero) return;
    var slides = $$('.hero-slide', hero);
    var dots = $$('.hdot', hero);
    if (slides.length < 2) return;

    var ruhig = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var i = 0, timer = null, INTERVALL = 5000;

    function zeige(n) {
      i = (n + slides.length) % slides.length;
      slides.forEach(function (s, k) { s.classList.toggle('active', k === i); });
      dots.forEach(function (d, k) {
        d.classList.toggle('active', k === i);
        d.setAttribute('aria-selected', k === i ? 'true' : 'false');
      });
      var img = slides[i].querySelector('img');
      if (img && img.getAttribute('loading') === 'lazy') img.removeAttribute('loading');
    }
    function start() {
      if (ruhig || timer || document.hidden) return;
      timer = setInterval(function () { zeige(i + 1); }, INTERVALL);
    }
    function stopp() { clearInterval(timer); timer = null; }

    hero.addEventListener('click', function (ev) {
      var d = ev.target.closest('.hdot');
      if (!d) return;
      stopp(); zeige(parseInt(d.getAttribute('data-i'), 10) || 0); start();
    });
    /* Kein Pausieren beim blossen Ueberfahren: das Hero fuellt den halben
       Bildschirm, der Zeiger liegt fast immer irgendwo darauf - das Karussell
       stand dann still und wechselte nie. Pausiert wird nur, wo jemand gezielt
       bedient: Tastaturfokus. */
    hero.addEventListener('focusin', stopp);
    hero.addEventListener('focusout', start);
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) { stopp(); } else { start(); }
    });
    start();
  }());

  /* ============================== Galerie =============================== */
  /* Hauptbild mit Miniaturen darunter. Der Zustand steht in den Klassen, nicht
     in einer Variablen - so bleibt die Seite auch dann richtig, wenn sie aus
     dem Cache mit bereits gesetzter Auswahl zurueckkommt. */
  $$('[data-gal]').forEach(function (gal) {
    var slides = $$('.galslide', gal);
    var thumbs = $$('.galthumb', gal);
    if (slides.length < 2) return;

    function zeige(n) {
      n = (n + slides.length) % slides.length;
      slides.forEach(function (s, i) { s.classList.toggle('active', i === n); });
      thumbs.forEach(function (b, i) {
        var on = i === n;
        b.classList.toggle('active', on);
        b.setAttribute('aria-selected', on ? 'true' : 'false');
      });
      // Erst beim Anzeigen laden - das Hauptbild bleibt das einzige, das der
      // Browser sofort holt.
      var img = slides[n].querySelector('img');
      if (img && img.getAttribute('loading') === 'lazy') { img.removeAttribute('loading'); }
    }
    function aktiv() {
      for (var i = 0; i < slides.length; i++) {
        if (slides[i].classList.contains('active')) return i;
      }
      return 0;
    }

    gal.addEventListener('click', function (ev) {
      var t = ev.target.closest('.galthumb');
      if (t) { zeige(parseInt(t.getAttribute('data-i'), 10) || 0); return; }
      var nav = ev.target.closest('.galnav');
      if (nav) { zeige(aktiv() + (parseInt(nav.getAttribute('data-step'), 10) || 1)); }
    });

    gal.addEventListener('keydown', function (ev) {
      if (ev.key !== 'ArrowRight' && ev.key !== 'ArrowLeft') return;
      if (!ev.target.closest('.galthumb')) return;
      ev.preventDefault();
      var n = (aktiv() + (ev.key === 'ArrowRight' ? 1 : -1) + slides.length) % slides.length;
      zeige(n); thumbs[n].focus();
    });
  });

  /* ================================ Suche =============================== */
  /* Normalisierung muss exakt build/build.py::norm entsprechen. */
  function norm(s) {
    return String(s || '').toLowerCase()
      .replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss')
      .replace(/[àâ]/g, 'a').replace(/[éèê]/g, 'e').replace(/[îï]/g, 'i')
      .replace(/ô/g, 'o').replace(/[ùû]/g, 'u').replace(/ç/g, 'c')
      .replace(/[’']/g, ' ')
      .replace(/[^a-z0-9]+/g, ' ')
      .replace(/\s+/g, ' ').trim();
  }
  function toks(s) { return norm(s).split(' ').filter(Boolean); }

  /* Levenshtein mit Abbruch – reicht für Tippfehler in Gerätenamen. */
  function lev(a, b, max) {
    if (Math.abs(a.length - b.length) > max) return max + 1;
    var prev = [], cur = [], i, j;
    for (j = 0; j <= b.length; j++) prev[j] = j;
    for (i = 1; i <= a.length; i++) {
      cur[0] = i; var best = cur[0];
      for (j = 1; j <= b.length; j++) {
        cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1,
          prev[j - 1] + (a.charAt(i - 1) === b.charAt(j - 1) ? 0 : 1));
        if (cur[j] < best) best = cur[j];
      }
      if (best > max) return max + 1;
      prev = cur.slice();
    }
    return prev[b.length];
  }

  var IDX = null, idxLoading = null;
  function loadIndex() {
    if (IDX) return Promise.resolve(IDX);
    if (idxLoading) return idxLoading;
    idxLoading = fetch(VT.searchIndex, { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (j) { IDX = j; return j; })
      .catch(function () { return null; });
    return idxLoading;
  }

  function wordStarts(text, q) {
    if (!text) return false;
    if (text.lastIndexOf(q, 0) === 0) return true;
    return text.indexOf(' ' + q) >= 0;
  }

  function fieldScore(it, q) {
    var t1 = it.t1 || '', t2 = it.t2 || '', t3 = it.t3 || '', s = 0;
    if (t1 === q) s = 130;
    else if (wordStarts(t1, q)) s = 95;
    else if (t1.indexOf(q) >= 0) s = 62;
    if (s < 48 && wordStarts(t2, q)) s = 48;
    else if (s < 32 && t2.indexOf(q) >= 0) s = 32;
    if (s < 20 && wordStarts(t3, q)) s = 20;
    else if (s < 12 && t3.indexOf(q) >= 0) s = 12;
    if (!s && q.length >= 4) {           // Tippfehlertoleranz nur auf dem Namen
      var max = q.length > 6 ? 2 : 1, words = t1.split(' ');
      for (var i = 0; i < words.length; i++) {
        if (!words[i] || Math.abs(words[i].length - q.length) > max) continue;
        var d = lev(words[i], q, max);
        if (d <= max) { s = Math.max(s, 46 - d * 14); break; }
      }
    }
    return s;
  }

  function scoreItem(it, qts, syn) {
    var total = 0, missed = 0;
    for (var i = 0; i < qts.length; i++) {
      var variants = [qts[i]].concat(syn[qts[i]] || []);
      var best = 0;
      for (var v = 0; v < variants.length; v++) {
        var sc = fieldScore(it, variants[v]);
        if (v > 0) sc *= 0.82;           // Synonymtreffer leicht abwerten
        if (sc > best) best = sc;
      }
      if (!best) missed++;
      total += best;
    }
    if (missed === qts.length) return 0;
    if (missed) total *= 0.4;            // nicht alle Wörter getroffen
    return total;
  }

  function search(q) {
    var out = { products: [], cats: [], procs: [], dls: [], suggestion: null, q: q };
    if (!IDX) return out;
    var qts = toks(q);
    if (!qts.length) return out;
    var syn = IDX.syn || {};
    ['products', 'cats', 'procs', 'dls'].forEach(function (grp) {
      out[grp] = (IDX[grp] || []).map(function (it) {
        return { it: it, s: scoreItem(it, qts, syn) };
      }).filter(function (r) { return r.s > 0; })
        .sort(function (a, b) { return b.s - a.s || a.it.n.localeCompare(b.it.n); })
        .map(function (r) { return r.it; });
    });
    if (!out.products.length && !out.cats.length && !out.procs.length) {
      out.suggestion = didYouMean(qts);
    }
    return out;
  }

  function didYouMean(qts) {
    if (!IDX || !IDX.vocab) return null;
    var best = null, bestD = 99;
    qts.forEach(function (q) {
      if (q.length < 4) return;
      for (var i = 0; i < IDX.vocab.length; i++) {
        var w = IDX.vocab[i];
        if (Math.abs(w.length - q.length) > 2) continue;
        var d = lev(w, q, 2);
        if (d < bestD && d > 0) { bestD = d; best = w; }
      }
    });
    return bestD <= 2 ? best : null;
  }

  function mark(text, q) {
    var qs = toks(q).filter(function (x) { return x.length > 1; });
    var html = esc(text);
    qs.forEach(function (x) {
      html = html.replace(new RegExp('(' + x.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'ig'),
        '<mark>$1</mark>');
    });
    return html;
  }

  /* ------------------------------------------------- Autocomplete-Dropdown */
  var input = $('#q'), sugg = $('#sugg'), form = $('#searchForm');
  var sIdx = -1, sItems = [];

  function closeSuggest() {
    if (!sugg) return;
    sugg.hidden = true; sugg.innerHTML = ''; sIdx = -1; sItems = [];
    if (input) { input.setAttribute('aria-expanded', 'false'); input.removeAttribute('aria-activedescendant'); }
  }

  function renderSuggest(res) {
    if (!sugg) return;
    var html = '', n = 0;
    function group(label, items, limit, withImg) {
      if (!items.length) return;
      html += '<div class="sgrp">' + esc(label) + '</div>';
      items.slice(0, limit).forEach(function (it) {
        html += '<a class="sitem" id="sg' + n + '" role="option" aria-selected="false" href="' + esc(it.u) + '">' +
          (withImg && it.g ? '<img src="' + esc(it.g) + '" alt="" width="40" height="40" loading="lazy">' : '') +
          '<span class="sn">' + mark(it.n, res.q) + '</span>' +
          (it.v ? '<span class="sv">' + esc(it.v) + '</span>' : '') + '</a>';
        sItems.push(it); n++;
      });
    }
    sItems = [];
    group(t('search_group_products'), res.products, 6, true);
    group(t('search_group_cats'), res.cats, 3, false);
    group(t('search_group_procs'), res.procs, 2, false);
    if (!sItems.length) {
      html = '<div class="sempty">' + esc(t('search_no_results')) + ' “' + esc(res.q) + '”';
      if (res.suggestion) {
        html += '<br><a class="sdym" href="' + esc(VT.searchUrl) + '?q=' + encodeURIComponent(res.suggestion) + '">' +
          esc(t('search_did_you_mean')) + ' “' + esc(res.suggestion) + '”?</a>';
      }
      html += '</div>';
    } else {
      html += '<a class="sall" href="' + esc(VT.searchUrl) + '?q=' + encodeURIComponent(res.q) + '">' +
        esc(t('search_all_results')) + ' →</a>';
    }
    sugg.innerHTML = html;
    sugg.hidden = false;
    sIdx = -1;
    if (input) input.setAttribute('aria-expanded', 'true');
  }

  function highlightSuggest(delta) {
    var els = $$('.sitem', sugg);
    if (!els.length) return;
    if (sIdx >= 0 && els[sIdx]) els[sIdx].setAttribute('aria-selected', 'false');
    sIdx += delta;
    if (sIdx < 0) sIdx = els.length - 1;
    if (sIdx >= els.length) sIdx = 0;
    els[sIdx].setAttribute('aria-selected', 'true');
    els[sIdx].scrollIntoView({ block: 'nearest' });
    if (input) input.setAttribute('aria-activedescendant', els[sIdx].id);
  }

  if (input) {
    var run = debounce(function () {
      var q = input.value.trim();
      if (q.length < 2) { closeSuggest(); return; }
      loadIndex().then(function () { renderSuggest(search(q)); });
    }, 110);
    input.addEventListener('input', run);
    input.addEventListener('focus', function () { loadIndex(); });
    input.addEventListener('keydown', function (ev) {
      if (sugg.hidden) return;
      if (ev.key === 'ArrowDown') { ev.preventDefault(); highlightSuggest(1); }
      else if (ev.key === 'ArrowUp') { ev.preventDefault(); highlightSuggest(-1); }
      else if (ev.key === 'Enter' && sIdx >= 0) {
        var el = $$('.sitem', sugg)[sIdx];
        if (el) { ev.preventDefault(); window.location.href = el.getAttribute('href'); }
      }
    });
    document.addEventListener('click', function (ev) {
      if (form && !form.contains(ev.target)) closeSuggest();
    });
  }

  /* ------------------------------------------------------- Ergebnisseite */
  var srBox = $('#srResults');
  if (srBox) {
    var params = new URLSearchParams(location.search);
    var q = (params.get('q') || '').trim();
    var pq = $('#pq'); if (pq) pq.value = q;
    if (input) input.value = q;

    if (!q) {
      loadIndex().then(function (idx) {
        if (!idx) return;
        srBox.innerHTML = '<div class="chips">' + (idx.popular || []).map(function (x) {
          return '<a class="chip" href="' + esc(VT.searchUrl) + '?q=' + encodeURIComponent(x) + '">' + esc(x) + '</a>';
        }).join('') + '</div>';
        $('#srTitle').textContent = t('search_popular');
      });
    } else {
      document.title = q + ' · ' + document.title;
      loadIndex().then(function (idx) {
        if (!idx) { srBox.innerHTML = '<p class="noacc">' + esc(t('form_error')) + '</p>'; return; }
        var res = search(q);
        var total = res.products.length;
        $('#srTitle').textContent = t('search_results_for') + ' “' + q + '”';
        $('#srCount').textContent = total === 1 ? t('search_one_result')
          : t('search_n_results').replace('{n}', total);
        var html = '';
        if (res.products.length) {
          html += '<div class="pgrid">' + res.products.map(function (p) {
            return '<article class="pcard"><a class="pcard-link" href="' + esc(p.u) + '">' +
              '<div class="imgbox">' +
              '<img src="' + esc(p.g) + '" alt="' + esc(p.n) + '" width="280" height="280" loading="lazy" decoding="async"></div>' +
              '<div class="body"><h3>' + mark(p.n, q) + '</h3><p>' + mark(p.d, q) + '</p>' +
              '<div class="spec"><span>' + esc(p.c) + '</span><span>' + esc(p.s) + '</span></div></div></a>' +
              '<div class="foot"><span class="poa">' + esc(t('poa')) + '</span>' +
              '<button class="add" type="button" data-add="' + esc(p.i) + '" data-name="' + esc(p.n) +
              '" data-url="' + esc(p.u) + '" data-img="' + esc(p.g) + '">' + esc(t('inquire')) + '</button></div></article>';
          }).join('') + '</div>';
        }
        function list(label, items) {
          if (!items.length) return '';
          return '<h2 class="sec-h">' + esc(label) + '</h2><div class="linklist">' +
            items.slice(0, 12).map(function (it) {
              return '<a href="' + esc(it.u) + '"><b>' + mark(it.n, q) + '</b>' +
                (it.d ? '<span>' + esc(it.d) + '</span>' : '') + '</a>';
            }).join('') + '</div>';
        }
        html += list(t('search_group_cats'), res.cats);
        html += list(t('search_group_procs'), res.procs);
        html += list(t('search_group_dl'), res.dls);
        if (!html) {
          html = '<div class="noresult"><p class="big">' + esc(t('search_no_results')) + ' “' + esc(q) + '”</p>' +
            '<p>' + esc(t('search_no_results_help')) + '</p>';
          if (res.suggestion) {
            html += '<p><a class="btn pri" href="' + esc(VT.searchUrl) + '?q=' + encodeURIComponent(res.suggestion) + '">' +
              esc(t('search_did_you_mean')) + ' “' + esc(res.suggestion) + '”?</a></p>';
          }
          html += '<p><a href="' + esc(VT.productsUrl) + '">' + esc(t('search_all_results')) + ' →</a></p></div>';
        }
        srBox.innerHTML = html;
      });
    }
  }

  /* =============================== Formulare ============================ */
  function fieldError(el, msg) {
    el.setAttribute('aria-invalid', 'true');
    /* Die Meldung gehört direkt hinter das Feld – alle Felder haben dasselbe
       Elternelement (das Formular), deshalb wird über nextElementSibling
       gesucht und nicht über parentNode.querySelector. */
    var p = el.nextElementSibling;
    if (!p || !p.classList || !p.classList.contains('ferr')) {
      p = document.createElement('p');
      p.className = 'ferr';
      p.id = (el.id || el.name || 'f') + '-err';
      el.parentNode.insertBefore(p, el.nextSibling);
    }
    p.textContent = msg;
    el.setAttribute('aria-describedby', p.id);
  }
  function clearErrors(f) {
    $$('.ferr', f).forEach(function (x) { x.remove(); });
    $$('[aria-invalid]', f).forEach(function (x) {
      x.removeAttribute('aria-invalid');
      x.removeAttribute('aria-describedby');
    });
  }
  function validate(f) {
    clearErrors(f);
    var ok = true;
    $$('[required]', f).forEach(function (el) {
      if (!el.value.trim()) { fieldError(el, t('form_required')); ok = false; }
      else if (el.type === 'email' && !/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(el.value.trim())) {
        fieldError(el, t('form_invalid_mail')); ok = false;
      }
    });
    if (!ok) { var first = f.querySelector('[aria-invalid]'); if (first) first.focus(); }
    return ok;
  }

  function mailtoFallback(subject, body) {
    window.location.href = 'mailto:' + VT.mailto +
      '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
    toast(t('opened_mail'));
  }

  function submitForm(f, subject, extraBody) {
    if (!validate(f)) return;
    var btn = f.querySelector('button[type=submit]');
    var status = $('.fstatus', f);
    var data = {
      name: (f.querySelector('[name=name]') || {}).value || '',
      email: (f.querySelector('[name=email]') || {}).value || '',
      phone: (f.querySelector('[name=phone]') || {}).value || '',
      message: (f.querySelector('[name=message]') || {}).value || ''
    };
    var body = 'Name / Firma: ' + data.name + '\nE-Mail: ' + data.email +
      (data.phone ? '\nTelefon: ' + data.phone : '') +
      (extraBody ? '\n\n' + extraBody : '') +
      (data.message ? '\n\nNachricht:\n' + data.message : '') +
      '\n\nGesendet über ' + location.origin + location.pathname + ' (' + (VT.lang || 'de') + ')';

    if (!VT.web3formsKey) { mailtoFallback(subject, body); return; }

    btn.disabled = true;
    if (status) { status.className = 'fstatus'; status.textContent = t('form_sending'); }

    fetch('https://api.web3forms.com/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({
        access_key: VT.web3formsKey,
        subject: subject,
        from_name: data.name || 'VES-TECH Swiss',
        email: data.email,
        phone: data.phone,
        message: body,
        botcheck: (f.querySelector('[name=botcheck]') || {}).checked || false,
        replyto: data.email
      })
    }).then(function (r) { return r.json(); }).then(function (j) {
      btn.disabled = false;
      if (j && j.success) {
        if (status) { status.className = 'fstatus ok'; status.textContent = t('form_success'); }
        f.reset();
        if (f.id === 'cartForm') { cart = []; saveCart(); }
        toast(t('form_success'));
      } else {
        if (status) { status.className = 'fstatus err'; status.textContent = t('form_error'); }
      }
    }).catch(function () {
      btn.disabled = false;
      if (status) { status.className = 'fstatus err'; status.textContent = t('form_error'); }
      mailtoFallback(subject, body);
    });
  }

  var cartForm = $('#cartForm');
  if (cartForm) {
    cartForm.addEventListener('submit', function (ev) {
      ev.preventDefault();
      if (!cart.length) { toast(t('cart_empty')); return; }
      var lines = cart.map(function (x) {
        return '- ' + x.name + ' × ' + (x.qty || 1) +
          (x.url ? '  (' + location.origin + x.url + ')' : '');
      }).join('\n');
      submitForm(cartForm, 'Anfrage VES-TECH (' + cart.length + ' Artikel)',
        'Gewünschte Geräte:\n' + lines);
    });
  }
  var kForm = $('#kontaktForm');
  if (kForm) {
    kForm.addEventListener('submit', function (ev) {
      ev.preventDefault();
      submitForm(kForm, 'Kontaktanfrage VES-TECH Swiss');
    });
  }

  /* ================================ Start =============================== */
  renderCart();

  /* Suchfeld per "/" fokussieren – kleine Profi-Geste */
  document.addEventListener('keydown', function (ev) {
    if (ev.key === '/' && document.activeElement === document.body && input) {
      ev.preventDefault(); input.focus();
    }
  });
})();
