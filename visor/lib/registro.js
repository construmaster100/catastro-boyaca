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
  var TERMINOS_VERSION = '2026-10-01';
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

  // ---- pantalla de terminos y condiciones (bloquea el visor hasta aceptar)
  function pantalla(soloLectura) {
    var viejo = document.getElementById('terminosCB');
    if (viejo) viejo.remove();
    var o = document.createElement('div');
    o.id = 'terminosCB';
    o.setAttribute('role', 'dialog');
    o.setAttribute('aria-modal', 'true');
    o.setAttribute('aria-labelledby', 'terminosTitulo');
    o.innerHTML =
      '<style>' +
      '#terminosCB{position:fixed;inset:0;z-index:10000;background:rgba(15,30,22,.82);backdrop-filter:blur(4px);display:flex;align-items:center;' +
      'justify-content:center;padding:16px;font:13.5px/1.5 system-ui,"Segoe UI",sans-serif}' +
      '#terminosCB .tc{background:#fff;color:#1f2328;border-radius:14px;width:min(760px,100%);max-height:calc(100vh - 32px);display:flex;' +
      'flex-direction:column;box-shadow:0 18px 50px rgba(0,0,0,.45);overflow:hidden}' +
      '#terminosCB .tc-cab{display:flex;align-items:center;gap:14px;padding:14px 20px;border-bottom:3px solid #0f4d2e}' +
      '#terminosCB .tc-cab img{height:56px}#terminosCB h2{margin:0;font-size:19px;color:#0f4d2e;text-transform:none;letter-spacing:0}' +
      '#terminosCB h2 small{display:block;font-size:12px;font-weight:400;color:#5d6470;text-transform:none;letter-spacing:0}' +
      '#terminosCB .tc-texto{overflow-y:auto;padding:6px 22px 10px;flex:1}' +
      '#terminosCB .tc-texto h3{font-size:13.5px;color:#0f4d2e;margin:14px 0 4px}#terminosCB .tc-texto p{margin:0 0 6px}' +
      '#terminosCB .tc-pie{border-top:1px solid #dcdad3;padding:14px 20px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;background:#f7f6f2}' +
      '#terminosCB label{flex:1 1 360px;display:flex;gap:10px;align-items:flex-start;cursor:pointer;font-weight:600}' +
      '#terminosCB input[type=checkbox]{width:20px;height:20px;margin:1px 0 0;accent-color:#2f7d4f;flex-shrink:0;cursor:pointer}' +
      '#terminosCB .ingresar{font:700 15px system-ui,sans-serif;color:#fff;background:#2f7d4f;border:0;border-radius:8px;padding:11px 30px;' +
      'cursor:pointer;box-shadow:0 2px 8px rgba(47,125,79,.45)}#terminosCB .ingresar:hover{background:#246b40}' +
      '#terminosCB .ingresar[hidden]{display:none}' +
      '#terminosCB .sec{font:600 12px system-ui,sans-serif;background:none;border:1px solid #c3c2b7;border-radius:6px;padding:7px 12px;cursor:pointer;color:#1f2328}' +
      '</style>' +
      '<div class="tc"><div class="tc-cab"><img src="' + (location.pathname.indexOf('/admin') === 0 ? '/' : '') + 'img/logo_web.png" alt="">' +
      '<h2 id="terminosTitulo">Términos y condiciones<small>Lea y acepte para ingresar al visor Catastro Boyacá</small></h2></div>' +
      '<div class="tc-texto">' + TEXTO + '</div>' +
      '<div class="tc-pie">' + (soloLectura
        ? '<span style="flex:1">Términos aceptados en este navegador (versión ' + TERMINOS_VERSION + ').</span>' +
          '<button type="button" class="sec" id="tcRevocar">Revocar autorización</button><button type="button" class="ingresar" id="tcCerrar">Cerrar</button>'
        : '<label><input type="checkbox" id="tcAcepto"> He leído y acepto los términos y condiciones y autorizo el tratamiento de mis datos personales ' +
          '(Ley 1581 de 2012).</label><button type="button" class="ingresar" id="tcIngresar" hidden>Ingresar</button>') +
      '</div></div>';
    document.body.appendChild(o);
    document.documentElement.style.overflow = 'hidden';
    function cerrar() { o.remove(); document.documentElement.style.overflow = ''; }
    if (soloLectura) {
      o.querySelector('#tcCerrar').onclick = cerrar;
      o.querySelector('#tcRevocar').onclick = function () {
        window.registrar('aceptacion', { accion: 'revocada', version: TERMINOS_VERSION });
        ['cb_terminos', 'cb_consent', 'cb_visitante'].forEach(function (n) { poner(n, '', 0); local(n, null); });
        location.reload();
      };
      return;
    }
    var casilla = o.querySelector('#tcAcepto'), boton = o.querySelector('#tcIngresar');
    casilla.onchange = function () { boton.hidden = !casilla.checked; if (casilla.checked) boton.focus(); };
    boton.onclick = function () {
      if (!casilla.checked) return;
      poner('cb_terminos', TERMINOS_VERSION, ANIO); local('cb_terminos', TERMINOS_VERSION);
      poner('cb_consent', 'todas', ANIO);
      window.registrar('aceptacion', { accion: 'aceptada', version: TERMINOS_VERSION });
      window.registrar('visita');
      cerrar();
    };
  }
  window.preferenciasCookies = window.verTerminos = function () { pantalla(aceptado()); };

  function iniciar() {
    if (aceptado()) { window.registrar('visita'); return; }
    window.registrar('visita');                       // visita anonima (todavia sin aceptar)
    pantalla(false);
  }
  if (document.body) iniciar(); else document.addEventListener('DOMContentLoaded', iniciar);
})();
