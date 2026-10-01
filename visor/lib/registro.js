/*
 * Registro de uso del visor + cookies con consentimiento (Ley 1581 de 2012).
 *
 * Cookies (solo cuando el visor corre con servidor_visor.py; nunca en la copia offline ni en la version publicada):
 *   cb_consent   "todas" | "necesarias"            decision del visitante (1 ano)
 *   cb_visitante identificador anonimo del navegador (1 ano), SOLO si cb_consent = "todas"
 * Sin consentimiento (o mientras no responda) las visitas se cuentan de forma anonima: el servidor no guarda
 * IP, navegador ni identificador. La sesion (pestana) se cuenta con sessionStorage, que se borra al cerrarla.
 */
(function () {
  var activo = location.protocol.indexOf('http') === 0 && !window.__SOLO_JS && !/github\.io$/i.test(location.hostname);
  var ANIO = 365 * 24 * 3600;
  function leer(n) { var m = document.cookie.match(new RegExp('(?:^|; )' + n + '=([^;]*)')); return m ? decodeURIComponent(m[1]) : ''; }
  function poner(n, v, seg) { document.cookie = n + '=' + encodeURIComponent(v) + '; path=/; max-age=' + seg + '; SameSite=Lax'; }
  function id() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 10); }
  var sid;
  try { sid = sessionStorage.getItem('cb_sesion') || id(); sessionStorage.setItem('cb_sesion', sid); } catch (e) { sid = id(); }

  function consentimiento() { return leer('cb_consent') || 'pendiente'; }
  function visitante() {
    if (consentimiento() !== 'todas') return '';
    var v = leer('cb_visitante');
    if (!v) { v = id(); }
    poner('cb_visitante', v, ANIO);                        // renueva el ano en cada visita
    return v;
  }

  window.registrar = function (tipo, datos) {
    if (!activo) return;
    var todas = consentimiento() === 'todas';
    var cuerpo = JSON.stringify({ tipo: tipo, datos: datos || {}, pagina: location.pathname, sid: sid, vid: visitante(),
                                  consentimiento: consentimiento(),
                                  idioma: todas ? navigator.language : '', pantalla: todas ? screen.width + 'x' + screen.height : '',
                                  ref: todas ? document.referrer : '' });
    try {
      if (navigator.sendBeacon) navigator.sendBeacon('/api/evento', new Blob([cuerpo], { type: 'application/json' }));
      else fetch('/api/evento', { method: 'POST', body: cuerpo, keepalive: true }).catch(function () {});
    } catch (e) {}
  };

  // ---- barra de cookies (no bloquea el visor)
  function barra() {
    var viejo = document.getElementById('barraCookies');
    if (viejo) viejo.remove();
    var b = document.createElement('div');
    b.id = 'barraCookies';
    b.setAttribute('role', 'dialog');
    b.setAttribute('aria-label', 'Preferencias de cookies');
    b.style.cssText = 'position:fixed;left:50%;bottom:14px;transform:translateX(-50%);z-index:6000;max-width:min(720px,calc(100% - 24px));' +
      'background:#1f2a36;color:#f3f1ec;border-radius:10px;box-shadow:0 8px 28px rgba(0,0,0,.35);padding:12px 16px;display:flex;gap:14px;' +
      'align-items:center;flex-wrap:wrap;font:13px/1.4 system-ui,"Segoe UI",sans-serif';
    b.innerHTML = '<span style="flex:1 1 320px">🍪 Usamos cookies para contar visitas y conocer qué predios se consultan. ' +
      'Con «Aceptar» se registran tu IP y tu navegador con fines estadísticos (Ley 1581 de 2012). ' +
      'Con «Solo necesarias» la visita se cuenta de forma anónima.</span>' +
      '<button type="button" data-c="necesarias" style="font:600 12px system-ui,sans-serif;padding:7px 12px;border-radius:6px;cursor:pointer;' +
      'background:transparent;color:#f3f1ec;border:1px solid rgba(255,255,255,.4)">Solo necesarias</button>' +
      '<button type="button" data-c="todas" style="font:700 12px system-ui,sans-serif;padding:7px 16px;border-radius:6px;cursor:pointer;' +
      'background:#b8860b;color:#fff;border:0">Aceptar</button>';
    b.addEventListener('click', function (e) {
      var c = e.target.getAttribute && e.target.getAttribute('data-c');
      if (!c) return;
      var antes = consentimiento();
      poner('cb_consent', c, ANIO);
      if (c !== 'todas') poner('cb_visitante', '', 0);      // al rechazar se borra el identificador
      b.remove();
      if (antes === 'pendiente' && c === 'todas') window.registrar('visita', { consentimiento: 'aceptado' });
    });
    document.body.appendChild(b);
  }
  window.preferenciasCookies = function () { if (activo) barra(); };

  if (!activo) return;
  window.registrar('visita');
  if (consentimiento() === 'pendiente') {
    if (document.body) barra(); else document.addEventListener('DOMContentLoaded', barra);
  }
})();
