"""
Servidor local del visor: sirve la carpeta visor/ comprimiendo los datos (gzip),
lo que reduce varias veces lo que el navegador descarga.

Ademas registra las visitas (estadisticas de uso) y sirve la vista de administrador:
    /api/evento          (POST) el visor informa visitas, ingresos, predios consultados...  -> registro/visitas.jsonl
    /admin/              vista de administrador (carpeta admin/, fuera de visor/: nunca se publica)
    /api/estadisticas    resumen para la vista de administrador
La vista de administrador y sus datos SOLO responden a este computador (127.0.0.1).

Uso:  python servidor_visor.py [puerto]      (por defecto 8765)
      Luego abrir http://localhost:8765/        administrador: http://localhost:8765/admin/
      Con --red se puede abrir desde otros equipos de la misma red (http://IP-de-este-equipo:8765/).
"""
import gzip
import json
import re
import sys
import threading
import webbrowser
from collections import Counter, defaultdict
from datetime import datetime
from functools import lru_cache, partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

CARPETA = Path(__file__).parent
VISOR = CARPETA / "visor"
DOCS = CARPETA / "docs"            # documentos descargados (se sirven en /docs/...)
ADMIN = CARPETA / "admin"          # vista de administrador (se sirve en /admin/, solo local)
REGISTRO = CARPETA / "registro" / "visitas.jsonl"
CANDADO = threading.Lock()
TIPOS = {"visita", "predio", "municipio", "ficha", "descarga", "documento", "busqueda"}


@lru_cache(maxsize=64)
def comprimido(ruta, modificado):
    return gzip.compress(Path(ruta).read_bytes(), compresslevel=6)


# ------------------------------------------------------------------ estadisticas
def navegador(ua):
    for patron, nombre in [(r"Edg/", "Edge"), (r"OPR/|Opera", "Opera"), (r"Firefox/", "Firefox"),
                           (r"Chrome/", "Chrome"), (r"Safari/", "Safari")]:
        if re.search(patron, ua or ""):
            return nombre
    return "Otro"


def sistema(ua):
    for patron, nombre in [(r"Windows", "Windows"), (r"Android", "Android"), (r"iPhone|iPad", "iOS"),
                           (r"Mac OS X", "macOS"), (r"Linux", "Linux")]:
        if re.search(patron, ua or ""):
            return nombre
    return "Otro"


def estadisticas():
    eventos = []
    if REGISTRO.exists():
        for linea in REGISTRO.read_text(encoding="utf-8").splitlines():
            try:
                eventos.append(json.loads(linea))
            except ValueError:
                pass
    visitas = [e for e in eventos if e["tipo"] == "visita"]
    predios = [e for e in eventos if e["tipo"] == "predio"]
    por_dia = defaultdict(lambda: {"visitas": 0, "ingresos": set(), "predios": 0})
    for e in eventos:
        d = por_dia[e["fecha"][:10]]
        if e["tipo"] == "visita":
            d["visitas"] += 1
            d["ingresos"].add(e.get("sid"))
        elif e["tipo"] == "predio":
            d["predios"] += 1
    dias = [{"dia": k, "visitas": v["visitas"], "ingresos": len(v["ingresos"]), "predios": v["predios"]}
            for k, v in sorted(por_dia.items())][-60:]
    top_predios = Counter((e["datos"].get("codigo"), e["datos"].get("municipio")) for e in predios)
    top_mun = Counter(e["datos"].get("municipio") for e in predios + [x for x in eventos if x["tipo"] == "municipio"])
    paginas = Counter(e.get("pagina") for e in visitas)
    consultantes = {}
    for e in eventos:
        c = consultantes.setdefault(e.get("vid") or e["ip"], {
            "visitante": (e.get("vid") or "")[:8], "ip": e["ip"], "navegador": navegador(e.get("ua")),
            "sistema": sistema(e.get("ua")), "idioma": e.get("idioma"), "pantalla": e.get("pantalla"),
            "primero": e["fecha"], "ultimo": e["fecha"], "visitas": 0, "ingresos": set(), "predios": 0, "ultimo_predio": ""})
        c["ultimo"] = max(c["ultimo"], e["fecha"])
        c["ip"] = e["ip"]
        if e["tipo"] == "visita":
            c["visitas"] += 1
            c["ingresos"].add(e.get("sid"))
        elif e["tipo"] == "predio":
            c["predios"] += 1
            c["ultimo_predio"] = e["datos"].get("codigo", "")
    lista = sorted(consultantes.values(), key=lambda c: c["ultimo"], reverse=True)
    for c in lista:
        c["ingresos"] = len(c["ingresos"])
    return {
        "generado": datetime.now().isoformat(timespec="seconds"),
        "total_eventos": len(eventos),
        "totales": {"visitas": len(visitas), "ingresos": len({e.get("sid") for e in visitas}),
                    "visitantes": len(consultantes), "predios": len(predios),
                    "predios_distintos": len(top_predios),
                    "fichas": sum(e["tipo"] == "ficha" for e in eventos),
                    "descargas": sum(e["tipo"] == "descarga" for e in eventos)},
        "dias": dias,
        "paginas": paginas.most_common(),
        "navegadores": Counter(c["navegador"] for c in lista).most_common(),
        "sistemas": Counter(c["sistema"] for c in lista).most_common(),
        "top_predios": [{"codigo": c, "municipio": m, "veces": n} for (c, m), n in top_predios.most_common(50)],
        "top_municipios": [{"municipio": m, "veces": n} for m, n in top_mun.most_common(30) if m],
        "consultantes": lista[:300],
        "recientes": list(reversed(eventos[-300:])),
    }


# ------------------------------------------------------------------ servidor
class Manejador(SimpleHTTPRequestHandler):
    def es_local(self):
        return self.client_address[0] in ("127.0.0.1", "::1")

    def translate_path(self, path):
        ruta = unquote(path.split("?", 1)[0].split("#", 1)[0])
        for prefijo, base in (("/docs/", DOCS), ("/admin/", ADMIN)):
            if ruta.startswith(prefijo):
                destino = (base / ruta[len(prefijo):]).resolve()
                if str(destino).startswith(str(base.resolve())):
                    return str(destino / "index.html") if destino.is_dir() else str(destino)
        return super().translate_path(path)

    def responder_json(self, codigo, obj):
        datos = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        ruta = self.path.split("?", 1)[0]
        if ruta.startswith("/admin") or ruta.startswith("/api/"):
            if not self.es_local():                          # administrador: solo desde este computador
                return self.responder_json(403, {"error": "Solo disponible en el equipo del administrador"})
            if ruta == "/admin":
                self.send_response(301)
                self.send_header("Location", "/admin/")
                self.end_headers()
                return
            if ruta == "/api/estadisticas":
                return self.responder_json(200, estadisticas())
        return super().do_GET()

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/evento":
            return self.responder_json(404, {"error": "no existe"})
        try:
            largo = min(int(self.headers.get("Content-Length", 0)), 8192)
            e = json.loads(self.rfile.read(largo).decode("utf-8"))
            if e.get("tipo") not in TIPOS:
                raise ValueError("tipo")
            reg = {"fecha": datetime.now().isoformat(timespec="seconds"), "tipo": e["tipo"],
                   "ip": self.client_address[0], "ua": self.headers.get("User-Agent", "")[:300],
                   "pagina": str(e.get("pagina", ""))[:120], "vid": str(e.get("vid", ""))[:40],
                   "sid": str(e.get("sid", ""))[:40], "idioma": str(e.get("idioma", ""))[:20],
                   "pantalla": str(e.get("pantalla", ""))[:20], "ref": str(e.get("ref", ""))[:200],
                   "datos": {k: str(v)[:120] for k, v in (e.get("datos") or {}).items()}}
            with CANDADO:
                REGISTRO.parent.mkdir(exist_ok=True)
                with open(REGISTRO, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(reg, ensure_ascii=False) + "\n")
            self.send_response(204)
            self.end_headers()
        except Exception:
            self.responder_json(400, {"error": "evento invalido"})

    def send_head(self):
        ruta = Path(self.translate_path(self.path))
        if ruta.suffix in (".json", ".html", ".js", ".css") and ruta.is_file() \
                and "gzip" in self.headers.get("Accept-Encoding", ""):
            datos = comprimido(str(ruta), ruta.stat().st_mtime)
            self.send_response(200)
            self.send_header("Content-Type", self.guess_type(str(ruta)))
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(datos)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            from io import BytesIO
            return BytesIO(datos)
        return super().send_head()

    def end_headers(self):
        # Siempre revalidar: asi el navegador no muestra versiones viejas del visor
        if not self._headers_buffer or b"Cache-Control" not in b"".join(self._headers_buffer):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    puerto = int(args[0]) if args else 8765
    host = "0.0.0.0" if "--red" in sys.argv else "127.0.0.1"
    servidor = ThreadingHTTPServer((host, puerto), partial(Manejador, directory=str(VISOR)))
    url = f"http://localhost:{puerto}/"
    print(f"Visor en {url}   Administrador: {url}admin/  (cierre esta ventana o Ctrl+C para apagarlo)")
    if "--sin-navegador" not in sys.argv:
        webbrowser.open(url)
    servidor.serve_forever()
