"""
Servidor local del visor: sirve la carpeta visor/ comprimiendo los datos (gzip),
lo que reduce varias veces lo que el navegador descarga.

Uso:  python servidor_visor.py [puerto]      (por defecto 8765)
      Luego abrir http://localhost:8765/
      Con --red se puede abrir desde otros equipos de la misma red (http://IP-de-este-equipo:8765/).
"""
import gzip
import sys
import webbrowser
from functools import lru_cache, partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

VISOR = Path(__file__).parent / "visor"
DOCS = Path(__file__).parent / "docs"          # documentos descargados (se sirven en /docs/...)


@lru_cache(maxsize=64)
def comprimido(ruta, modificado):
    return gzip.compress(Path(ruta).read_bytes(), compresslevel=6)


class Manejador(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # /docs/... se sirve desde la carpeta docs/ del proyecto (fuera de visor/)
        ruta = path.split("?", 1)[0].split("#", 1)[0]
        if ruta.startswith("/docs/"):
            from urllib.parse import unquote
            destino = (DOCS / unquote(ruta[len("/docs/"):])).resolve()
            if str(destino).startswith(str(DOCS.resolve())):
                return str(destino)
        return super().translate_path(path)

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
    print(f"Visor en {url}  (cierre esta ventana o Ctrl+C para apagarlo)")
    webbrowser.open(url)
    servidor.serve_forever()
