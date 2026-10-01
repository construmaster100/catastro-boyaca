/*
 * Registro de uso del visor (estadisticas para la vista de administrador).
 * Envia al servidor local (servidor_visor.py, /api/evento): visitas, ingresos (sesiones) y predios consultados.
 * Datos: fecha, tipo de evento, pagina, identificador anonimo del navegador, idioma y pantalla; el servidor
 * agrega IP y navegador. No se registra en la version offline sin servidor ni en la version publicada.
 */
(function () {
  var activo = location.protocol.indexOf('http') === 0 && !window.__SOLO_JS && !/github\.io$/i.test(location.hostname);
  function id() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 10); }
  function guardado(almacen, clave) {
    try { var v = almacen.getItem(clave); if (!v) { v = id(); almacen.setItem(clave, v); } return v; } catch (e) { return id(); }
  }
  var vid = guardado(window.localStorage, 'cb_visitante');      // mismo navegador = mismo visitante
  var sid = guardado(window.sessionStorage, 'cb_sesion');       // cada ingreso (pestana nueva) = una sesion
  window.registrar = function (tipo, datos) {
    if (!activo) return;
    var cuerpo = JSON.stringify({ tipo: tipo, datos: datos || {}, pagina: location.pathname, vid: vid, sid: sid,
                                  idioma: navigator.language, pantalla: screen.width + 'x' + screen.height,
                                  ref: document.referrer });
    try {
      if (navigator.sendBeacon) navigator.sendBeacon('/api/evento', new Blob([cuerpo], { type: 'application/json' }));
      else fetch('/api/evento', { method: 'POST', body: cuerpo, keepalive: true }).catch(function () {});
    } catch (e) {}
  };
  window.registrar('visita');
})();
