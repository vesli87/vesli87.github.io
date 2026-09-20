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

  /* Adressen aus dem localStorage sind nicht vertrauenswuerdig: dort schreibt
     zwar normalerweise nur diese Seite, aber ein href="javascript:…" waere
     anklickbarer Schadcode, und esc() allein verhindert das nicht - es
     maskiert Anfuehrungszeichen, nicht das Schema. Erlaubt ist deshalb nur,
     was diese Seite selbst erzeugt: ein eigener Pfad oder https. */
  function safeUrl(u) {
    u = String(u == null ? '' : u).trim();
    if (/[\\\u0000-\u001f\u007f]/.test(u)) return '#';
    if (/^\/[^\/]/.test(u)) return u;
    if (/^https:\/\//i.test(u)) return u;
    return '#';
  }

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

  /* Software keyboards can shrink only the visual viewport (not 100dvh).
     These measurements affect fixed overlays only, never the page layout.
     Preserve native pinch zoom instead of resizing a dialog on each pinch. */
  (function () {
    var viewport = window.visualViewport;
    if (!viewport || !viewport.addEventListener || (window.top && window.top !== window)) return;
    var pending = false, lastHeight = '', lastTop = '';
    function measure() {
      pending = false;
      if (!Number.isFinite(viewport.scale) || Math.abs(viewport.scale - 1) > 0.01 ||
          !Number.isFinite(viewport.height) || viewport.height <= 0 ||
          !Number.isFinite(viewport.offsetTop)) return;
      var height = Math.floor(viewport.height) + 'px';
      var top = Math.max(0, Math.round(viewport.offsetTop)) + 'px';
      var style = document.documentElement.style;
      if (height !== lastHeight) { style.setProperty('--vt-viewport-height', height); lastHeight = height; }
      if (top !== lastTop) { style.setProperty('--vt-viewport-top', top); lastTop = top; }
    }
    function schedule() {
      if (pending) return;
      pending = true;
      if (window.requestAnimationFrame) window.requestAnimationFrame(measure);
      else setTimeout(measure, 16);
    }
    viewport.addEventListener('resize', schedule);
    viewport.addEventListener('scroll', schedule);
    window.addEventListener('pageshow', schedule);
    measure();
  }());

  /* Der Bildrueckfall (fehlende lokale Kopie -> Original von mahe-online.de)
     steht bewusst nicht hier, sondern als kurzes Skript im <head>, siehe
     render.py::IMG_FALLBACK_JS. Von hier aus waere er zu spaet: dieses Skript
     laeuft mit defer, und ein error-Ereignis feuert nur ein einziges Mal. */

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
  function quantity(q) { return Math.max(1, Math.min(99, parseInt(q, 10) || 1)); }
  function cleanCart(value) {
    var result = [];
    if (!Array.isArray(value)) return result;
    value.slice(0, 200).forEach(function (item) {
      if (!item || typeof item !== 'object' || typeof item.id !== 'string' ||
          !/^[a-z0-9-]{1,100}$/.test(item.id) || typeof item.name !== 'string') return;
      var hit = result.filter(function (x) { return x.id === item.id; })[0];
      if (hit) { hit.qty = quantity(hit.qty + quantity(item.qty)); return; }
      var url = safeUrl(item.url);
      if (url.charAt(0) !== '/') url = '#';
      result.push({ id: item.id, name: item.name.slice(0, 200), url: url,
        img: safeUrl(item.img), qty: quantity(item.qty) });
    });
    return result;
  }
  var cart = cleanCart(store.get(CART_KEY, []));
  // Track removals during an in-flight inquiry. A product removed and added
  // again is a new selection, even when its product ID is unchanged.
  var cartRevision = {};

  window.addEventListener('storage', function (ev) {
    if (ev.key === CART_KEY || ev.key === null) {
      // Use the event snapshot, not the latest storage value: several rapid
      // changes can already be queued, including removal followed by re-add.
      var next = [];
      try { next = cleanCart(JSON.parse(ev.newValue)); } catch (err) { /* invalid entries are discarded */ }
      cart.forEach(function (item) {
        if (!next.some(function (x) { return x.id === item.id; })) {
          cartRevision[item.id] = (cartRevision[item.id] || 0) + 1;
        }
      });
      cart = next; renderCart();
    }
  });

  function saveCart() { store.set(CART_KEY, cart); renderCart(); }

  function addCart(item) {
    var status = $('#cartStatus'); if (status) status.textContent = '';
    var hit = null;
    for (var i = 0; i < cart.length; i++) if (cart[i].id === item.id) hit = cart[i];
    if (hit) { hit.qty = quantity(hit.qty + 1); toast(t('already')); }
    else { cart.push({ id: item.id, name: item.name, url: item.url, img: item.img, qty: 1 }); toast(t('added')); }
    saveCart();
  }
  function rmCart(id) {
    cartRevision[id] = (cartRevision[id] || 0) + 1;
    cart = cart.filter(function (x) { return x.id !== id; });
    saveCart();
  }
  function setQty(id, q) {
    cart.forEach(function (x) { if (x.id === id) x.qty = quantity(q); });
    saveCart();
  }

  function renderCart() {
    var count = cart.reduce(function (a, b) { return a + (b.qty || 1); }, 0);
    $$('#cnt').forEach(function (el) { el.textContent = count; });
    var box = $('#cartItems'), form = $('#cartForm');
    if (!box) return;
    var focused = document.activeElement;
    var focusedId = focused && focused.getAttribute &&
      (focused.getAttribute('data-id') || focused.getAttribute('data-rm'));
    var focusedAction = focusedId && focused.getAttribute('data-qty');
    if (!cart.length) {
      box.innerHTML = '<div class="empty">' + esc(t('cart_empty')) + '</div>';
      if (form) form.hidden = true;
      if (activePanel === 'cart' && (focusedId || (form && form.contains(focused)))) {
        var close = $('[data-close="cart"]'); if (close) close.focus();
      }
      return;
    }
    if (form) form.hidden = false;
    box.innerHTML = cart.map(function (x) {
      return '<div class="citem">' +
        '<a class="th" href="' + esc(safeUrl(x.url)) + '">' +
        (x.img ? '<img src="' + esc(safeUrl(x.img)) + '" alt="" width="60" height="60" loading="lazy">' : '') +
        '</a>' +
        '<div class="n"><a href="' + esc(safeUrl(x.url)) + '"><b>' + esc(x.name) + '</b></a>' +
        '<span>' + esc(t('poa')) + '</span>' +
        '<span class="qty"><button type="button" data-qty="-" data-id="' + esc(x.id) + '" aria-label="' + esc(t('qty_less') + ': ' + x.name) + '"' + (x.qty === 1 ? ' disabled' : '') + '>−</button>' +
        '<output>' + (Math.max(1, Math.min(99, parseInt(x.qty, 10) || 1))) + '</output>' +
        '<button type="button" data-qty="+" data-id="' + esc(x.id) + '" aria-label="' + esc(t('qty_more') + ': ' + x.name) + '"' + (x.qty === 99 ? ' disabled' : '') + '>+</button></span></div>' +
        '<button class="rm" type="button" data-rm="' + esc(x.id) + '" aria-label="' + esc(t('cart_remove') + ': ' + x.name) + '">✕</button></div>';
    }).join('');
    if (focusedId && activePanel === 'cart') {
      var next = $$('button', box).filter(function (button) {
        return !button.disabled && (focusedAction
          ? button.getAttribute('data-id') === focusedId && button.getAttribute('data-qty') === focusedAction
          : button.getAttribute('data-rm') === focusedId);
      })[0] || $('button:not(:disabled)', box) || $('[data-close="cart"]');
      if (next) next.focus();
    }
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
  var lastFocus = null, activePanel = null;

  function restoreFocus(el) {
    if (!el || !el.focus || el.isConnected === false) return;
    // Closing a fixed dialog must not jump the document or reopen a text
    // keyboard because Safari kept an earlier input focused on pointer click.
    el.focus({ preventScroll: true });
  }

  function trapFocus(ev, el) {
    if (ev.key !== 'Tab') return;
    var items = $$('a[href],button,input,textarea,select,[tabindex="0"]', el)
      .filter(function (x) { return !x.disabled && x.getClientRects().length; });
    if (!items.length) { ev.preventDefault(); el.focus(); return; }
    var first = items[0], last = items[items.length - 1];
    if (ev.shiftKey && (document.activeElement === first || !el.contains(document.activeElement))) {
      ev.preventDefault(); last.focus();
    } else if (!ev.shiftKey && (document.activeElement === last || !el.contains(document.activeElement))) {
      ev.preventDefault(); first.focus();
    }
  }

  function panelBackground(inert) {
    $$('.skip,.util,header,main,footer,.analytics-consent,.analytics-settings').forEach(function (el) { el.inert = inert; });
  }

  function openPanel(which, trigger) {
    var el = $('#' + which); if (!el) return;
    if (activePanel === which) { closePanel(which); return; }
    if (activePanel) closePanel(activePanel);
    lastFocus = trigger || document.activeElement;
    activePanel = which;
    el.inert = false;
    el.classList.add('open'); el.setAttribute('aria-hidden', 'false');
    panelBackground(true);
    $('#scrim').classList.add('open');
    document.body.style.overflow = 'hidden';
    var btn = $('[data-open="' + which + '"]');
    if (btn) btn.setAttribute('aria-expanded', 'true');
    if (which === 'cart') {
      renderCart();
      loadIndex().then(function (idx) {
        if (!idx) return;
        cart.forEach(function (item) {
          var p = idx.products.filter(function (x) { return x.i === item.id; })[0];
          if (p) { item.name = p.n; item.url = p.u; item.img = p.g; }
        });
        saveCart();
      });
    }
    var f = el.querySelector('a,button,input');
    if (f) f.focus();
  }
  function closePanel(which) {
    var el = $('#' + which); if (!el) return;
    if (activePanel !== which) return;
    activePanel = null;
    el.classList.remove('open'); el.setAttribute('aria-hidden', 'true');
    var btn = $('[data-open="' + which + '"]');
    if (btn) btn.setAttribute('aria-expanded', 'false');
    if (!$$('.mega.open, .cart.open').length) {
      $('#scrim').classList.remove('open');
      document.body.style.overflow = '';
    }
    panelBackground(false);
    restoreFocus(lastFocus);
    el.inert = true;
  }
  function closeAll() { closePanel('mega'); closePanel('cart'); }

  document.addEventListener('click', function (ev) {
    var o = ev.target.closest('[data-open]');
    if (o) { ev.preventDefault(); openPanel(o.getAttribute('data-open'), o); return; }
    var c = ev.target.closest('[data-close]');
    if (c) {
      ev.preventDefault();
      var w = c.getAttribute('data-close');
      if (w === 'all') closeAll(); else closePanel(w);
    }
  });
  document.addEventListener('keydown', function (ev) {
    if (activePanel) trapFocus(ev, $('#' + activePanel));
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
        x.tabIndex = on ? 0 : -1;
      });
      $$('.tabpane').forEach(function (p) {
        p.classList.toggle('active', p.id === 'tab-' + name);
      });
    });
    tabbar.addEventListener('keydown', function (ev) {
      if (['ArrowRight', 'ArrowLeft', 'Home', 'End'].indexOf(ev.key) < 0) return;
      var btns = $$('.tabbtn', tabbar);
      var i = btns.indexOf(document.activeElement);
      if (i < 0) return;
      ev.preventDefault();
      var n = (i + (ev.key === 'ArrowRight' ? 1 : -1) + btns.length) % btns.length;
      if (ev.key === 'Home') n = 0;
      if (ev.key === 'End') n = btns.length - 1;
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
      img.setAttribute('role', 'button');
      img.tabIndex = 0;
      img.setAttribute('aria-label', t('lupe_open') + ': ' + img.alt);
      img.addEventListener('keydown', function (ev) {
        if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); oeffnen(img); }
      });
    });

    var box, buehne, bild, txt, vor, zurueck, zuletzt = null, gruppe = [], idx = 0;

    function bauen() {
      box = document.createElement('div');
      box.className = 'lupe';
      box.setAttribute('role', 'dialog');
      box.setAttribute('aria-modal', 'true');
      box.setAttribute('aria-label', t('lupe_open'));
      box.hidden = true;
      box.innerHTML =
        '<div class="lupe-kopf">' +
          '<button class="lupe-btn" type="button" data-lupe="zoom" aria-label="' +
            esc(t('lupe_in', 'Näher heran')) + '" aria-pressed="false">+</button>' +
          '<button class="lupe-btn" type="button" data-lupe="zu" aria-label="' +
            esc(t('lupe_close', 'Schliessen')) + '">\u2715</button>' +
        '</div>' +
        '<div class="lupe-buehne"><img alt=""></div>' +
        '<div class="lupe-fuss">' +
          '<button class="lupe-nav" type="button" data-lupe="-1" aria-label="' + esc(t('gal_prev')) + '">\u2039</button>' +
          '<span class="lupe-txt"></span>' +
          '<button class="lupe-nav" type="button" data-lupe="1" aria-label="' + esc(t('gal_next')) + '">\u203a</button>' +
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
          else if (v === 'zoom') { setZoom(!box.classList.contains('gross')); }
          else { zeigen(idx + parseInt(v, 10)); }
          return;
        }
        if (ev.target === bild) { setZoom(!box.classList.contains('gross')); return; }
        if (ev.target === buehne || ev.target === box) schliessen();
      });
    }

    function setZoom(enlarged) {
      box.classList.toggle('gross', enlarged);
      var button = $('[data-lupe="zoom"]', box);
      button.textContent = enlarged ? '\u2212' : '+';
      button.setAttribute('aria-label', enlarged ? t('lupe_out', 'Weniger nah') : t('lupe_in', 'Näher heran'));
      button.setAttribute('aria-pressed', enlarged ? 'true' : 'false');
      if (!enlarged) { buehne.scrollLeft = 0; buehne.scrollTop = 0; }
    }

    function zeigen(n) {
      idx = (n + gruppe.length) % gruppe.length;
      var q = gruppe[idx];
      setZoom(false);
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
      zuletzt = img;
      box.hidden = false;
      panelBackground(true);
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
      panelBackground(false);
      restoreFocus(zuletzt);
    }

    document.addEventListener('click', function (ev) {
      var img = ev.target.closest('.zoomable');
      if (!img) return;
      ev.preventDefault();
      oeffnen(img);
    });

    document.addEventListener('keydown', function (ev) {
      if (!box || box.hidden) return;
      trapFocus(ev, box);
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

    var motion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');
    var ruhig = motion && motion.matches;
    var i = 0, timer = null, INTERVALL = 5000, angehalten = false;

    function zeige(n) {
      i = (n + slides.length) % slides.length;
      slides.forEach(function (s, k) { s.classList.toggle('active', k === i); });
      dots.forEach(function (d, k) {
        d.classList.toggle('active', k === i);
        d.setAttribute('aria-pressed', k === i ? 'true' : 'false');
      });
      var img = slides[i].querySelector('img');
      if (img && img.getAttribute('loading') === 'lazy') img.removeAttribute('loading');
    }
    function start(explicit) {
      if (ruhig || timer || document.hidden || angehalten || (!explicit && hero.contains(document.activeElement))) return;
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
    hero.addEventListener('focusout', function () { setTimeout(start, 0); });
    if (motion && motion.addEventListener) motion.addEventListener('change', function (ev) {
      ruhig = ev.matches; if (ruhig) stopp(); else start();
    });

    /* WCAG 2.2.2: was sich von selbst bewegt und laenger als fuenf Sekunden
       laeuft, muss sich anhalten lassen. Die Punkte schalten nur um. Der
       Knopf merkt sich den Wunsch: einmal angehalten, startet auch der
       Fokuswechsel das Karussell nicht wieder. */
    var pauseKnopf = hero.querySelector('[data-hpause]');
    if (pauseKnopf) {
      var beschriftung = {
        pause: pauseKnopf.getAttribute('aria-label'),
        weiter: T.slide_play || pauseKnopf.getAttribute('aria-label')
      };
      pauseKnopf.addEventListener('click', function () {
        angehalten = !angehalten;
        if (angehalten) { stopp(); } else { start(true); }
        pauseKnopf.setAttribute('aria-pressed', angehalten ? 'true' : 'false');
        pauseKnopf.setAttribute('aria-label', angehalten ? beschriftung.weiter : beschriftung.pause);
        pauseKnopf.firstElementChild.textContent = angehalten ? '\u25B6' : '\u2759\u2759';
      });
      pauseKnopf.setAttribute('aria-pressed', 'false');
    }
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
        b.tabIndex = on ? 0 : -1;
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
      if (['ArrowRight', 'ArrowLeft', 'Home', 'End'].indexOf(ev.key) < 0) return;
      if (!ev.target.closest('.galthumb')) return;
      ev.preventDefault();
      var n = (aktiv() + (ev.key === 'ArrowRight' ? 1 : -1) + slides.length) % slides.length;
      if (ev.key === 'Home') n = 0;
      if (ev.key === 'End') n = slides.length - 1;
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
  function request(url, options, timeout) {
    var controller = new AbortController();
    var timer = setTimeout(function () { controller.abort(); }, timeout);
    options = options || {};
    options.signal = controller.signal;
    return fetch(url, options).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    }).then(function (data) { clearTimeout(timer); return data; }, function (err) {
      clearTimeout(timer); throw err;
    });
  }
  function loadIndex() {
    if (IDX) return Promise.resolve(IDX);
    if (idxLoading) return idxLoading;
    idxLoading = request(VT.searchIndex, { credentials: 'same-origin' }, 10000)
      .then(function (j) {
        if (!j || !Array.isArray(j.products)) throw new Error('Invalid search index');
        IDX = j; return j;
      })
      .catch(function () { idxLoading = null; return null; });
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
    var qs = toks(q).filter(function (x) { return x.length > 1; })
      .sort(function (a, b) { return b.length - a.length; });
    if (!qs.length) return esc(text);
    // Match plain text once, then escape each fragment. Matching already
    // escaped HTML corrupted entities and even the <mark> tags themselves.
    return String(text || '').split(new RegExp('(' + qs.join('|') + ')', 'ig'))
      .map(function (part, i) { return i % 2 ? '<mark>' + esc(part) + '</mark>' : esc(part); }).join('');
  }

  /* ------------------------------------------------- Autocomplete-Dropdown */
  var input = $('#q'), sugg = $('#sugg'), form = $('#searchForm');
  var sIdx = -1, sItems = [], suggestVersion = 0;

  function closeSuggest() {
    suggestVersion++;
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
      var version = ++suggestVersion;
      loadIndex().then(function (idx) {
        if (version !== suggestVersion || input.value.trim() !== q || document.activeElement !== input) return;
        if (!idx) {
          sugg.innerHTML = '<p class="sempty" role="status">' + esc(t('search_unavailable')) + '</p>';
          sugg.hidden = false; input.setAttribute('aria-expanded', 'true'); return;
        }
        renderSuggest(search(q));
      });
    }, 110);
    input.addEventListener('input', function () { closeSuggest(); run(); });
    input.addEventListener('blur', function () { suggestVersion++; });
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
        if (!idx) { srBox.innerHTML = '<p class="noacc" role="status">' + esc(t('search_unavailable')) + '</p>'; return; }
        srBox.innerHTML = '<div class="chips">' + (idx.popular || []).map(function (x) {
          return '<a class="chip" href="' + esc(VT.searchUrl) + '?q=' + encodeURIComponent(x) + '">' + esc(x) + '</a>';
        }).join('') + '</div>';
        $('#srTitle').textContent = t('search_popular');
      });
    } else {
      document.title = q + ' · ' + document.title;
      loadIndex().then(function (idx) {
        if (!idx) { srBox.innerHTML = '<p class="noacc" role="status">' + esc(t('search_unavailable')) + '</p>'; return; }
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

  /* Ohne Web3Forms-Schluessel geht die Anfrage ueber das Mailprogramm. Frueher
     wurde nur mailto: aufgerufen und "Mailprogramm geoeffnet" gemeldet - auch
     dann, wenn gar keines eingerichtet ist. Auf einem Rechner ohne Mailkonto
     passierte also nichts, und die Anfrage war weg.

     Jetzt bleibt der fertige Text sichtbar stehen, mit Adresse und Kopierknopf.
     Damit geht keine Anfrage mehr verloren, auch wenn mailto: ins Leere greift. */
  function mailtoFallback(f, subject, body, openMail) {
    var link = 'mailto:' + VT.mailto +
      '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
    if (openMail) {
      try { window.location.href = link; } catch (e) { /* der Kasten bleibt */ }
    }

    var box = f ? f.querySelector('.mfall') : null;
    if (!box && f) {
      box = document.createElement('div');
      box.className = 'mfall';
      f.appendChild(box);
    }
    if (!box) { toast(t('opened_mail')); return; }
    box.innerHTML =
      '<p class="mfall-h">' + esc(t('mail_h', 'Anfrage bereit zum Senden')) + '</p>' +
      '<p class="mfall-p">' + esc(t('mail_p', 'Ihr Mailprogramm sollte sich geoeffnet haben. ' +
        'Falls nicht: Text kopieren und an folgende Adresse senden.')) + '</p>' +
      '<p class="mfall-a"><a href="mailto:' + esc(VT.mailto) + '">' + esc(VT.mailto) + '</a></p>' +
      '<textarea class="mfall-t" rows="8" readonly aria-label="' + esc(t('mail_h')) + '"></textarea>' +
      '<div class="mfall-btns">' +
        '<button type="button" class="mfall-copy">' + esc(t('mail_copy', 'Text kopieren')) + '</button>' +
        '<a class="mfall-open" href="' + esc(link) + '">' + esc(t('mail_open', 'Mailprogramm oeffnen')) + '</a>' +
      '</div>';
    box.querySelector('.mfall-t').value = body;
    box.querySelector('.mfall-copy').addEventListener('click', function () {
      var ta = box.querySelector('.mfall-t');
      ta.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      if (navigator.clipboard && !ok) {
        navigator.clipboard.writeText(body).then(function () { toast(t('mail_copied', 'Kopiert')); })
          .catch(function () { toast(t('mail_copy_manual')); });
      } else {
        toast(t(ok ? 'mail_copied' : 'mail_copy_manual', ok ? 'Kopiert' : 'Bitte von Hand markieren'));
      }
    });
    box.scrollIntoView({ block: 'nearest' });
  }

  function submitForm(f, subject, extraBody, submittedCart) {
    if (f.dataset.sending === 'true') return;
    if ((f.querySelector('[name=botcheck]') || {}).checked) return;
    if (!validate(f)) return;
    var btn = f.querySelector('button[type=submit]');
    var status = $('.fstatus', f);
    var data = {
      name: (f.querySelector('[name=name]') || {}).value || '',
      email: (f.querySelector('[name=email]') || {}).value || '',
      phone: (f.querySelector('[name=phone]') || {}).value || '',
      message: (f.querySelector('[name=message]') || {}).value || ''
    };
    /* Der Mailtext folgt der Sprache der Seite. Vorher war er fest deutsch:
       wer im Tessin 'Invia richiesta' klickte, bekam einen Entwurf mit
       'Name / Firma', 'Nachricht' und 'Gewuenschte Geraete'. Der Kasten
       darum herum war laengst uebersetzt - nur der Text darin nicht. */
    var body = t('mail_f_name') + ': ' + data.name +
      '\n' + t('mail_f_mail') + ': ' + data.email +
      (data.phone ? '\n' + t('mail_f_tel') + ': ' + data.phone : '') +
      (extraBody ? '\n\n' + extraBody : '') +
      (data.message ? '\n\n' + t('mail_f_msg') + ':\n' + data.message : '') +
      '\n\n' + t('mail_f_sent') + ' ' + location.origin + location.pathname +
      ' (' + (VT.lang || 'de') + ')';

    if (!VT.web3formsKey) { mailtoFallback(f, subject, body, true); return; }

    f.dataset.sending = 'true';
    btn.disabled = true;
    if (status) { status.className = 'fstatus'; status.textContent = t('form_sending'); }

    request('https://api.web3forms.com/submit', {
      method: 'POST',
      referrerPolicy: 'no-referrer',
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
    }, 15000).then(function (j) {
      f.dataset.sending = 'false';
      btn.disabled = false;
      if (j && j.success === true) {
        if (status) { status.className = 'fstatus ok'; status.textContent = t('form_success'); }
        // The submitted snapshot succeeded. Preserve any new draft the
        // customer has started while waiting for the response.
        var unchanged = Object.keys(data).every(function (name) {
          return ((f.querySelector('[name=' + name + ']') || {}).value || '') === data[name];
        });
        if (unchanged) f.reset();
        var fallback = f.querySelector('.mfall');
        if (fallback) fallback.remove();
        if (f.id === 'cartForm' && submittedCart) {
          // The persistent confirmation lives outside the form, which may
          // be hidden and reopened for a new selection later on this page.
          if (status) { status.textContent = ''; status.className = 'fstatus'; }
          // Remove only quantities included in this request. Products added
          // while the request was in flight must stay in the list.
          cart = cart.reduce(function (out, item) {
            var sent = submittedCart.filter(function (x) { return x.id === item.id; })[0];
            var sameSelection = sent && (sent.revision || 0) === (cartRevision[item.id] || 0);
            var remaining = item.qty - (sameSelection ? sent.qty : 0);
            if (remaining > 0) out.push(Object.assign({}, item, { qty: remaining }));
            return out;
          }, []);
          saveCart();
          var confirmation = $('#cartStatus');
          if (confirmation) confirmation.textContent = t('form_success');
          // Disabling the send button can move focus to body before the
          // response arrives. Keep the completed dialog keyboard-accessible.
          if (!cart.length && activePanel === 'cart') {
            var close = $('[data-close="cart"]'); if (close) close.focus();
          }
        }
        toast(t('form_success'));
      } else {
        if (status) { status.className = 'fstatus err'; status.textContent = t('form_error'); }
        mailtoFallback(f, subject, body, false);
      }
    }).catch(function () {
      f.dataset.sending = 'false';
      btn.disabled = false;
      if (status) { status.className = 'fstatus err'; status.textContent = t('form_error'); }
      mailtoFallback(f, subject, body, false);
    });
  }

  var cartForm = $('#cartForm');
  if (cartForm) {
    cartForm.addEventListener('submit', function (ev) {
      ev.preventDefault();
      if (!cart.length) { toast(t('cart_empty')); return; }
      var submitted = cart.map(function (x) {
        return Object.assign({}, x, { revision: cartRevision[x.id] || 0 });
      });
      var lines = submitted.map(function (x) {
        return '- ' + x.name + ' × ' + (x.qty || 1) +
          (x.url.charAt(0) === '/' ? '  (' + (VT.siteUrl || location.origin) + x.url + ')' : '');
      }).join('\n');
      /* Einzahl und Mehrzahl: "1 articles" wollen wir niemandem schicken. */
      submitForm(cartForm,
        t('mail_s_cart') + ' (' + cart.length + ' ' +
          t(cart.length === 1 ? 'mail_s_item1' : 'mail_s_item') + ')',
        t('mail_f_dev') + ':\n' + lines, submitted);
    });
  }
  var kForm = $('#kontaktForm');
  if (kForm) {
    var productId = new URLSearchParams(location.search).get('product');
    if (productId && /^[a-z0-9-]{1,100}$/.test(productId)) {
      // Carry the selected product into the contact form without storing
      // personal form fields in a URL or in localStorage.
      $$('.langs a').forEach(function (a) {
        var target = new URL(a.href); target.searchParams.set('product', productId); a.href = target.href;
      });
      loadIndex().then(function (idx) {
        var p = idx && idx.products.filter(function (x) { return x.i === productId; })[0];
        var message = kForm.querySelector('[name=message]');
        if (p && message && !message.value) {
          message.value = t('consult_product').replace('{name}', p.n) + '\n' +
            (VT.siteUrl || location.origin) + p.u + '\n\n';
        }
      });
    }
    kForm.addEventListener('submit', function (ev) {
      ev.preventDefault();
      submitForm(kForm, t('mail_s_kont'));
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
