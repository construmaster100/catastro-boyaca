/*
 * Terminos y condiciones (bloqueantes) + registro de uso del visor (Ley 1581 de 2012).
 *
 * Al entrar se muestra la pantalla de Terminos y Condiciones: el visor queda bloqueado hasta marcar la casilla
 * de aceptacion; entonces aparece el boton verde "Ingresar". La aceptacion se guarda un ano:
 *   cookie cb_consent = "todas", cb_terminos = version aceptada, cb_visitante = identificador anonimo del navegador
 *   (en la copia offline, sin servidor, se guarda en el almacenamiento local del navegador)
 * y se registra en el servidor (evento "aceptacion": fecha, hora, IP, navegador).
 * Si cambia TERMINOS_VERSION, todos deben volver a aceptar.
 */
(function () {
  var TERMINOS_VERSION = '2026-10-01.2';   // al cambiarla, todos deben volver a aceptar
  var conServidor = location.protocol.indexOf('http') === 0 && !window.__SOLO_JS && !/github\.io$/i.test(location.hostname);
  var ANIO = 365 * 24 * 3600;
  function leer(n) { var m = document.cookie.match(new RegExp('(?:^|; )' + n + '=([^;]*)')); return m ? decodeURIComponent(m[1]) : ''; }
  function poner(n, v, seg) { document.cookie = n + '=' + encodeURIComponent(v) + '; path=/; max-age=' + seg + '; SameSite=Lax'; }
  function id() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 10); }
  function local(n, v) { try { if (v === undefined) return localStorage.getItem(n) || ''; if (v === null) localStorage.removeItem(n); else localStorage.setItem(n, v); } catch (e) { return ''; } }
  var sid;
  try { sid = sessionStorage.getItem('cb_sesion') || id(); sessionStorage.setItem('cb_sesion', sid); } catch (e) { sid = id(); }

  function aceptado() { return (leer('cb_terminos') || local('cb_terminos')) === TERMINOS_VERSION; }
  function consentimiento() { return aceptado() ? 'todas' : 'pendiente'; }
  function visitante() {
    if (!aceptado()) return '';
    var v = leer('cb_visitante') || local('cb_visitante') || id();
    poner('cb_visitante', v, ANIO); local('cb_visitante', v);
    return v;
  }

  window.registrar = function (tipo, datos) {
    if (!conServidor) return;
    var si = aceptado();
    var cuerpo = JSON.stringify({ tipo: tipo, datos: datos || {}, pagina: location.pathname, sid: sid, vid: visitante(),
                                  consentimiento: consentimiento(),
                                  idioma: si ? navigator.language : '', pantalla: si ? screen.width + 'x' + screen.height : '',
                                  ref: si ? document.referrer : '' });
    try {
      if (navigator.sendBeacon) navigator.sendBeacon('/api/evento', new Blob([cuerpo], { type: 'application/json' }));
      else fetch('/api/evento', { method: 'POST', body: cuerpo, keepalive: true }).catch(function () {});
    } catch (e) {}
  };

  var TEXTO =
    '<h3>1. Objeto</h3><p>El visor <b>Catastro Boyacá</b> permite consultar información catastral pública de los predios del departamento ' +
    'de Boyacá, sus municipios, zonas urbanas y estudios económicos, con fines informativos y de consulta.</p>' +
    '<h3>2. Fuentes y alcance de la información</h3><p>Los datos provienen de fuentes públicas: Instituto Geográfico Agustín Codazzi (IGAC, ' +
    'datos abiertos catastrales y límites municipales) y Cámara de Comercio de Tunja (Boyacá en Cifras y estudios económicos). Las áreas, ' +
    'perímetros, cotas y coordenadas se calculan a partir de la geometría publicada. La información es <b>informativa</b>: no reemplaza el ' +
    'certificado catastral, la consulta oficial ante el gestor catastral ni un levantamiento topográfico, y no tiene valor jurídico. ' +
    'No se publican propietarios ni avalúos.</p>' +
    '<h3>3. Uso permitido</h3><p>El usuario se compromete a usar la información de forma lícita, a citar las fuentes (IGAC y Cámara de Comercio ' +
    'de Tunja) y a no usarla para fines fraudulentos ni para afectar derechos de terceros.</p>' +
    '<h3>4. Tratamiento de datos personales (Ley 1581 de 2012)</h3><p>Al ingresar se registran, con <b>fines estadísticos</b> y de mejora del ' +
    'servicio: fecha y hora de cada consulta, dirección IP, navegador, sistema operativo, idioma, tamaño de pantalla, páginas visitadas, ' +
    'municipios y predios consultados, y la aceptación de estos términos. Estos datos no se venden, no se publican y no se comparten con ' +
    'terceros. Como titular puede conocer, actualizar, rectificar y solicitar la supresión de sus datos, y revocar esta autorización, ' +
    'ante el responsable del visor (Juan Yamil López, Perito Catastral e Inmobiliario).</p>' +
    '<h3>5. Cookies</h3><p>El visor usa cookies propias para recordar la aceptación de estos términos (un año) y para identificar de forma anónima ' +
    'el navegador en las estadísticas de uso. No se usan cookies de publicidad ni de terceros.</p>' +
    '<h3>6. Aceptación</h3><p>Al marcar la casilla y pulsar «Ingresar», el usuario declara haber leído y aceptado estos términos y autoriza el ' +
    'tratamiento de sus datos en las condiciones descritas. Versión ' + TERMINOS_VERSION + '.</p>';

  // ---- estilos comunes de las dos ventanas
  // Misma hoja de estilo del visor: usa sus variables (--panel, --texto, --suave, --borde, --bg, --nav, --ok...),
  // su tipografia y sus bordes; asi respeta tambien el modo oscuro. Los valores despues de la coma son de respaldo.
  var CSS =
    '.cb-fondo{position:fixed;inset:0;background:rgba(15,20,25,.78);backdrop-filter:blur(3px);display:flex;align-items:center;' +
    'justify-content:center;padding:16px;font:13px/1.45 system-ui,"Segoe UI",Roboto,sans-serif;color:var(--texto,#1f2328)}' +
    '.cb-caja{background:var(--panel,#fff);color:var(--texto,#1f2328);border:1px solid var(--borde,#dcdad3);border-radius:8px;' +
    'box-shadow:0 12px 40px rgba(0,0,0,.4);overflow:hidden;display:flex;flex-direction:column;max-height:calc(100vh - 32px)}' +
    '.cb-cab{display:flex;align-items:stretch;background:var(--panel,#fff);border-bottom:1px solid var(--borde,#dcdad3)}' +
    '.cb-cab img{width:170px;height:68px;object-fit:contain;padding:4px 8px;border-right:1px solid var(--borde,#dcdad3);background:var(--panel,#fff)}' +
    '.cb-cab h2{margin:0;flex:1;display:flex;flex-direction:column;justify-content:center;padding:0 16px;background:var(--nav,#1f2a36);' +
    'color:var(--nav-texto,#f3f1ec);font-size:15px;font-weight:700;text-transform:none;letter-spacing:0}' +
    '.cb-cab h2 small{display:block;font-size:12px;font-weight:400;opacity:.75}' +
    '.cb-texto{overflow-y:auto;padding:6px 18px 10px;flex:1}' +
    '.cb-texto h3{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--suave,#5d6470);margin:14px 0 4px;font-weight:700}' +
    '.cb-texto p{margin:0 0 6px}.cb-texto b{color:var(--texto,#1f2328)}' +
    '.cb-pie{border-top:1px solid var(--borde,#dcdad3);padding:12px 18px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;background:var(--bg,#f5f4f0)}' +
    '.cb-acepto{display:flex;gap:10px;align-items:center;cursor:pointer;font-size:14px;font-weight:600}' +
    '.cb-acepto input{width:20px;height:20px;margin:0;accent-color:var(--ok,#2f7d4f);cursor:pointer;flex-shrink:0}' +
    '.cb-acepto a{color:var(--acento,#b4531f);text-decoration:underline;font-weight:700}' +
    '.cb-despliegue{margin:10px 0 2px;padding:4px 14px 8px;max-height:46vh;overflow-y:auto;border:1px solid var(--borde,#dcdad3);' +
    'border-radius:6px;background:var(--bg,#f5f4f0)}' +
    '.cb-despliegue h3{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--suave,#5d6470);margin:12px 0 3px;font-weight:700}' +
    '.cb-despliegue p{margin:0 0 6px}' +
    '.cb-nota{font-size:11px;color:var(--suave,#5d6470);margin:8px 0 0 30px}' +
    '.cb-verde{font:600 13px system-ui,"Segoe UI",sans-serif;color:#fff;background:var(--ok,#2f7d4f);border:0;border-radius:6px;padding:9px 28px;cursor:pointer}' +
    '.cb-verde:hover{filter:brightness(1.1)}.cb-verde[hidden]{display:none}' +
    '.cb-sec{font:600 12px system-ui,sans-serif;background:var(--bg,#f5f4f0);border:1px solid var(--borde,#dcdad3);border-radius:6px;padding:7px 12px;cursor:pointer;color:var(--texto,#1f2328)}';
  var LOGO = (location.pathname.indexOf('/admin') === 0 ? '/' : '') + 'img/logo_web.png';

  function ventana(id, z, html) {
    var v = document.getElementById(id);
    if (v) v.remove();
    v = document.createElement('div');
    v.id = id; v.className = 'cb-fondo'; v.style.zIndex = z;
    v.setAttribute('role', 'dialog'); v.setAttribute('aria-modal', 'true');
    v.innerHTML = '<style>' + CSS + '</style>' + html;
    document.body.appendChild(v);
    document.documentElement.style.overflow = 'hidden';
    return v;
  }
  function quitar(v) { v.remove(); if (!document.querySelector('.cb-fondo')) document.documentElement.style.overflow = ''; }

  // ---- ventana con el texto completo de los terminos (se abre con el enlace)
  function ventanaTerminos(desdeEntrada) {
    var v = ventana('cbTerminos', 10001,
      '<div class="cb-caja" style="width:min(760px,100%)"><div class="cb-cab"><img src="' + LOGO + '" alt="">' +
      '<h2>Términos y condiciones<small>Visor Catastro Boyacá · versión ' + TERMINOS_VERSION + '</small></h2></div>' +
      '<div class="cb-texto">' + TEXTO + '</div><div class="cb-pie">' +
      (!desdeEntrada && aceptado() ? '<span style="flex:1">Aceptados en este navegador.</span><button type="button" class="cb-sec" id="cbRevocar">Revocar autorización</button>'
                                   : '<span style="flex:1"></span>') +
      '<button type="button" class="cb-verde" id="cbCerrarT">Cerrar</button></div></div>');
    v.querySelector('#cbCerrarT').onclick = function () { quitar(v); };
    var r = v.querySelector('#cbRevocar');
    if (r) r.onclick = function () {
      window.registrar('aceptacion', { accion: 'revocada', version: TERMINOS_VERSION });
      ['cb_terminos', 'cb_consent', 'cb_visitante'].forEach(function (n) { poner(n, '', 0); local(n, null); });
      location.reload();
    };
  }

  // ---- ventana de entrada (bloquea el visor hasta aceptar)
  function ventanaEntrada() {
    var v = ventana('cbEntrada', 10000,
      '<div class="cb-caja" style="width:min(640px,100%)"><div class="cb-cab"><img src="' + LOGO + '" alt="">' +
      '<h2>Bienvenido<small>Visor de predios Catastro Boyacá</small></h2></div>' +
      '<div class="cb-texto" style="padding:18px 22px 6px"><label class="cb-acepto"><input type="checkbox" id="cbAcepto">' +
      '<span>Acepto los <a href="#" id="cbVerT" aria-expanded="false" aria-controls="cbDespliegue">términos y condiciones ▾</a></span></label>' +
      '<div id="cbDespliegue" class="cb-despliegue" hidden>' + TEXTO + '</div>' +
      '<p class="cb-nota">Al aceptar se autoriza el uso de cookies y el tratamiento de datos personales descritos en los términos y condiciones ' +
      '(Ley 1581 de 2012).</p></div>' +
      '<div class="cb-pie" style="justify-content:flex-end">' +
      '<button type="button" class="cb-verde" id="cbIngresar" hidden>Ingresar</button></div></div>');
    var casilla = v.querySelector('#cbAcepto'), boton = v.querySelector('#cbIngresar');
    // enlace desplegable: muestra / oculta el texto de los terminos dentro de la misma ventana
    v.querySelector('#cbVerT').onclick = function (e) {
      e.preventDefault();
      var d = v.querySelector('#cbDespliegue'), abierto = d.hidden;
      d.hidden = !abierto;
      this.setAttribute('aria-expanded', String(abierto));
      this.textContent = 'términos y condiciones ' + (abierto ? '▴' : '▾');
    };
    casilla.onchange = function () { boton.hidden = !casilla.checked; if (casilla.checked) boton.focus(); };
    boton.onclick = function () {
      if (!casilla.checked) return;
      poner('cb_terminos', TERMINOS_VERSION, ANIO); local('cb_terminos', TERMINOS_VERSION);
      poner('cb_consent', 'todas', ANIO);
      window.registrar('aceptacion', { accion: 'aceptada', version: TERMINOS_VERSION });
      window.registrar('visita');
      quitar(v);
    };
  }
  window.preferenciasCookies = window.verTerminos = function () { ventanaTerminos(false); };

  function iniciar() {
    if (aceptado()) { window.registrar('visita'); return; }
    window.registrar('visita');                       // visita anonima (todavia sin aceptar)
    ventanaEntrada();
  }
  if (document.body) iniciar(); else document.addEventListener('DOMContentLoaded', iniciar);
})();
