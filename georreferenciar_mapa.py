"""
Georreferencia la imagen ilustrada del departamento (visor/img/Mapa departamental..png)
contra el contorno oficial (visor/datos/departamentos.json): busca la escala y posicion
donde la silueta de la imagen coincide mejor con el limite real y guarda las esquinas
de la imagen en coordenadas (visor/datos/mapa_departamental.json), mas una version
recortada para superponer en el mapa (visor/img/mapa_departamental_raster.png).
"""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

VISOR = Path(__file__).parent / "visor"
ORIGEN = VISOR / "img" / "Mapa departamental..png"
ANCHO_TRABAJO = 600


def merc_y(lat):
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def main():
    img = Image.open(ORIGEN).convert("RGBA")
    # silueta de la imagen: pixeles opacos
    alfa = img.getchannel("A").point(lambda a: 255 if a > 128 else 0)
    x0, y0, x1, y1 = alfa.getbbox()
    recorte = img.crop((x0, y0, x1, y1))
    w, h = recorte.size
    esc = ANCHO_TRABAJO / w
    mascara_img = recorte.getchannel("A").point(lambda a: 1 if a > 128 else 0) \
        .resize((ANCHO_TRABAJO, round(h * esc)), Image.NEAREST)
    W, H = mascara_img.size
    pix_img = mascara_img.load()

    # contorno oficial en coordenadas planas (lon, y-mercator)
    geo = json.loads((VISOR / "datos" / "departamentos.json").read_text(encoding="utf-8"))["features"][0]["geometry"]
    anillos = [geo["coordinates"][0]] if geo["type"] == "Polygon" else [p[0] for p in geo["coordinates"]]
    pts = [[(lon, merc_y(lat)) for lon, lat in a] for a in anillos]
    todos = [p for a in pts for p in a]
    gx0, gx1 = min(p[0] for p in todos), max(p[0] for p in todos)
    gy0, gy1 = min(p[1] for p in todos), max(p[1] for p in todos)

    def iou(sx, sy, dx, dy):
        """Coincidencia entre la silueta y el contorno ubicado con escala (sx, sy) y desplazamiento (dx, dy) en pixeles."""
        m = Image.new("1", (W, H), 0)
        d = ImageDraw.Draw(m)
        for a in pts:
            d.polygon([((x - gx0) / (gx1 - gx0) * W * sx + dx, (gy1 - y) / (gy1 - gy0) * H * sy + dy) for x, y in a], fill=1)
        pm = m.load()
        inter = union = 0
        for j in range(0, H, 2):
            for i in range(0, W, 2):
                a, b = pix_img[i, j], pm[i, j]
                inter += a and b
                union += a or b
        return inter / union if union else 0

    mejor = (iou(1, 1, 0, 0), 1, 1, 0, 0)
    print(f"coincidencia inicial (por recuadro): {mejor[0]:.3f}")
    paso_e, paso_d = 0.04, 12
    for _ in range(5):                        # busqueda local, cada vez mas fina
        mejora = True
        while mejora:
            mejora = False
            _, sx, sy, dx, dy = mejor
            for cand in [(sx + paso_e, sy, dx, dy), (sx - paso_e, sy, dx, dy), (sx, sy + paso_e, dx, dy), (sx, sy - paso_e, dx, dy),
                         (sx, sy, dx + paso_d, dy), (sx, sy, dx - paso_d, dy), (sx, sy, dx, dy + paso_d), (sx, sy, dx, dy - paso_d)]:
                v = iou(*cand)
                if v > mejor[0]:
                    mejor, mejora = (v,) + cand, True
        paso_e, paso_d = paso_e / 2, paso_d / 2
    v, sx, sy, dx, dy = mejor
    print(f"coincidencia final: {v:.3f}  (escala {sx:.3f} x {sy:.3f}, desplazamiento {dx:.1f}, {dy:.1f} px)")

    # esquinas del recorte en coordenadas: pixel -> (lon, y-mercator) invirtiendo la transformacion
    def a_geo(px, py):
        lon = gx0 + (px - dx) / (W * sx) * (gx1 - gx0)
        ym = gy1 - (py - dy) / (H * sy) * (gy1 - gy0)
        lat = math.degrees(2 * math.atan(math.exp(ym)) - math.pi / 2)
        return lat, lon
    sur, oeste = a_geo(0, H)
    norte, este = a_geo(W, 0)
    (VISOR / "datos" / "mapa_departamental.json").write_text(json.dumps({
        "imagen": "img/mapa_departamental_raster.png",
        "limites": [[round(sur, 6), round(oeste, 6)], [round(norte, 6), round(este, 6)]],
        "coincidencia": round(v, 3)}, indent=2), encoding="utf-8")
    # version para superponer (1200 px de ancho)
    salida = recorte.resize((1200, round(h * 1200 / w)), Image.LANCZOS)
    salida.save(VISOR / "img" / "mapa_departamental_raster.png", optimize=True)
    print(f"limites: sur {sur:.5f}, oeste {oeste:.5f}, norte {norte:.5f}, este {este:.5f}")


if __name__ == "__main__":
    main()
