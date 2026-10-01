/*
 * Carga de datos sin servidor (version OFFLINE autoportante).
 *
 * Los navegadores no dejan que una pagina abierta con doble clic (file://) lea archivos .json con fetch().
 * En la copia offline cada datos/xxx.json se publica tambien como datos/xxx.json.js, que define
 * window.__D["datos/xxx.json"] = {...}; los <script> si se pueden cargar desde el disco.
 * Este archivo reemplaza fetch() por una version que carga ese .js cuando:
 *   - la pagina se abrio como archivo (file://), o
 *   - la copia es la offline (lib/modo_offline.js define window.__SOLO_JS = true).
 * En la version de trabajo y en la online no cambia nada: fetch() sigue igual.
 */
(function () {
  if (location.protocol !== 'file:' && !window.__SOLO_JS) return;
  var fetchOriginal = window.fetch ? window.fetch.bind(window) : null;
  window.__D = window.__D || {};
  window.fetch = function (url) {
    var clave = String(url);
    if (/^https?:/i.test(clave) && fetchOriginal) return fetchOriginal.apply(null, arguments);  // servicios externos
    return new Promise(function (resolver) {
      var s = document.createElement('script');
      s.src = clave + '.js';
      s.onload = function () {
        var v = window.__D[clave];
        delete window.__D[clave];          // libera memoria: el visor guarda su propia copia
        s.remove();
        resolver({
          ok: v !== undefined, status: v !== undefined ? 200 : 404,
          json: function () { return Promise.resolve(typeof v === 'string' ? JSON.parse(v) : v); },
          text: function () { return Promise.resolve(typeof v === 'string' ? v : JSON.stringify(v)); }
        });
      };
      s.onerror = function () {
        s.remove();
        resolver({ ok: false, status: 404,
                   json: function () { return Promise.reject(new Error('No se encontró ' + clave)); },
                   text: function () { return Promise.resolve(''); } });
      };
      document.head.appendChild(s);
    });
  };
})();
