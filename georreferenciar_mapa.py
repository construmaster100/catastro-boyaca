"""
Georreferencia la imagen ilustrada del departamento (visor/img/Mapa departamental..png)
contra el contorno oficial (visor/datos/departamentos.json).

Ajuste AFIN completo (escala X/Y, desplazamiento, rotacion e inclinacion: 6 parametros) que
maximiza la coincidencia pixel a pixel (IoU) entre la silueta de la imagen y el limite real.
Luego la imagen se "remuestrea" (warp) a una grilla alineada con el mapa (Web Mercator), para
que el visor la pueda superponer sin deformaciones.

Salidas:
    visor/img/mapa_departamental_raster.png   imagen alineada, lista para el mapa
    visor/img/mapa_departamental_mini.png     version pequena (mapa de ubicacion)
    visor/datos/mapa_departamental.json       limites de la imagen y coincidencia lograda
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

VISOR = Path(__file__).parent / "visor"
ORIGEN = VISOR / "img" / "Mapa departamental..png"
ANCHO_TRABAJO = 700
ANCHO_SALIDA = 1600


def merc_y(lat):
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def lat_de(ym):
    return math.degrees(2 * math.atan(math.exp(ym)) - math.pi / 2)


def main():
    img = Image.open(ORIGEN).convert("RGBA")
    x0, y0, x1, y1 = img.getchannel("A").point(lambda a: 255 if a > 128 else 0).getbbox()
    recorte = img.crop((x0, y0, x1, y1))
    w, h = recorte.size
    k = ANCHO_TRABAJO / w
    W, H = ANCHO_TRABAJO, round(h * k)
    mascara = np.array(recorte.getchannel("A").resize((W, H), Image.BILINEAR)) > 128

    geo = json.loads((VISOR / "datos" / "departamentos.json").read_text(encoding="utf-8"))["features"][0]["geometry"]
    anillos = [geo["coordinates"][0]] if geo["type"] == "Polygon" else [p[0] for p in geo["coordinates"]]
    pts = [np.array([(lon, merc_y(lat)) for lon, lat in a]) for a in anillos]
    todos = np.vstack(pts)
    gx0, gy0 = todos.min(axis=0)
    gx1, gy1 = todos.max(axis=0)

    # parametros: pixel (x, y) de la imagen de trabajo -> (lon, ym)
    #   lon = a*x + b*y + c ;  ym = d*x + e*y + f     (inicio: ajuste por recuadro)
    p0 = np.array([(gx1 - gx0) / W, 0.0, gx0, 0.0, -(gy1 - gy0) / H, gy1])

    def a_pixel(p):
        a, b, c, d, e, f = p
        M = np.array([[a, b], [d, e]])
        Minv = np.linalg.inv(M)
        return [((q - [c, f]) @ Minv.T) for q in pts]

    def iou(p):
        m = Image.new("1", (W, H), 0)
        dr = ImageDraw.Draw(m)
        for anillo in a_pixel(p):
            dr.polygon([tuple(v) for v in anillo], fill=1)
        pm = np.array(m, dtype=bool)
        union = (pm | mascara).sum()
        return (pm & mascara).sum() / union if union else 0

    # pasos relativos por parametro (escala, inclinacion, desplazamiento)
    esc = np.array([p0[0] * 0.02, p0[0] * 0.02, (gx1 - gx0) * 0.01, -p0[4] * 0.02, -p0[4] * 0.02, (gy1 - gy0) * 0.01])
    mejor_p, mejor = p0.copy(), iou(p0)
    print(f"coincidencia inicial (recuadro): {mejor:.4f}")
    for ronda in range(7):
        mejora = True
        while mejora:
            mejora = False
            for i in range(6):
                for signo in (1, -1):
                    cand = mejor_p.copy()
                    cand[i] += signo * esc[i]
                    v = iou(cand)
                    if v > mejor + 1e-5:
                        mejor, mejor_p, mejora = v, cand, True
        esc /= 2
        print(f"  ronda {ronda + 1}: coincidencia {mejor:.4f}")
    a, b, c, d, e, f = mejor_p
    rot = math.degrees(math.atan2(d, a))
    print(f"coincidencia final: {mejor:.4f}  (rotacion {rot:.2f} grados, inclinacion {b / a:.4f})")

    # ---- warp: imagen completa (resolucion original) -> grilla alineada al mapa
    # esquinas del recorte en (lon, ym)
    s = 1 / k                                           # pixel de trabajo -> pixel original del recorte
    esquinas = np.array([[0, 0], [W, 0], [0, H], [W, H]], dtype=float)
    geo_esq = np.array([[a * x + b * y + c, d * x + e * y + f] for x, y in esquinas])
    lon0, ym0 = geo_esq.min(axis=0)
    lon1, ym1 = geo_esq.max(axis=0)
    Wo = ANCHO_SALIDA
    Ho = round(Wo * math.degrees(ym1 - ym0) / (lon1 - lon0))     # ym en radianes -> grados, igual que lon
    # salida (u, v) -> (lon, ym) -> pixel de trabajo (x, y) -> pixel original (x*s, y*s)
    du, dv = (lon1 - lon0) / Wo, (ym1 - ym0) / Ho
    Minv = np.linalg.inv(np.array([[a, b], [d, e]]))
    # (lon, ym) = (lon0 + u*du, ym1 - v*dv) ; (x, y) = Minv @ ((lon, ym) - (c, f))
    A = Minv @ np.array([[du, 0], [0, -dv]])
    t = Minv @ (np.array([lon0, ym1]) - np.array([c, f]))
    coef = (A[0, 0] * s, A[0, 1] * s, t[0] * s, A[1, 0] * s, A[1, 1] * s, t[1] * s)
    salida = recorte.transform((Wo, Ho), Image.AFFINE, coef, resample=Image.BICUBIC, fillcolor=(0, 0, 0, 0))
    # recorte con el limite OFICIAL: fuera de Boyaca queda transparente, asi el borde coincide exactamente
    mascara_of = Image.new("L", (Wo, Ho), 0)
    dm = ImageDraw.Draw(mascara_of)
    for anillo in pts:
        dm.polygon([((lon - lon0) / du, (ym1 - ym) / dv) for lon, ym in anillo], fill=255)
    alfa = np.minimum(np.array(salida.getchannel("A")), np.array(mascara_of))
    # donde el dibujo no llega pero el limite oficial si, se rellena con el color medio del dibujo
    rgb = np.array(salida.convert("RGB")).astype(float)
    hueco = (np.array(mascara_of) > 0) & (np.array(salida.getchannel("A")) < 128)
    medio = rgb[np.array(salida.getchannel("A")) > 200].mean(axis=0)
    rgb[hueco] = medio
    alfa = np.where(hueco, 255, alfa)
    salida = Image.fromarray(np.dstack([rgb.astype(np.uint8), alfa.astype(np.uint8)]), "RGBA")
    print(f"pixeles rellenados dentro del limite oficial: {hueco.sum():,} ({100 * hueco.sum() / (np.array(mascara_of) > 0).sum():.1f} %)")
    salida.save(VISOR / "img" / "mapa_departamental_raster.png", optimize=True)
    salida.resize((500, round(500 * Ho / Wo)), Image.LANCZOS).save(VISOR / "img" / "mapa_departamental_mini.png", optimize=True)
    sur, norte = lat_de(ym0), lat_de(ym1)
    (VISOR / "datos" / "mapa_departamental.json").write_text(json.dumps({
        "imagen": "img/mapa_departamental_raster.png",
        "limites": [[round(sur, 6), round(lon0, 6)], [round(norte, 6), round(lon1, 6)]],
        "tamano": [Wo, Ho], "coincidencia": round(mejor, 4), "rotacion_grados": round(rot, 3)}, indent=2), encoding="utf-8")
    print(f"limites: sur {sur:.6f}, oeste {lon0:.6f}, norte {norte:.6f}, este {lon1:.6f} | imagen {Wo}x{Ho}")


if __name__ == "__main__":
    main()
