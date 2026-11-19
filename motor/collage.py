"""Motor de papel compartido por todas las plantillas de Opalaca.

Origen: carlosmvks1/carlosmvks1.github.io, _collage/componer.py
Revisión: 625ea2c25f05421892ad332adcf0be57653d7186 (Carlos Reyes).
Adaptado con autorización del propietario: paleta diurna, cortes de un borde,
protección de alfa, fotos de producto y formatos de Instagram.
"""
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

BASE = Path(__file__).resolve().parent
FONT_ITALIC = str(BASE / "fonts/FrauncesItalic.ttf")
FONT_SEMI = str(BASE / "fonts/FrauncesSemi.ttf")
FONT_SANS = str(BASE / "fonts/PublicSansSemi.ttf")
C = {
    "crema": (246, 240, 232), "papel": (250, 246, 240),
    "tinta": (43, 38, 34), "lavanda": (214, 204, 236),
    "menta": (196, 230, 222), "durazno": (244, 205, 182),
    "oro": (184, 145, 63),
}
NAVIDAD = {"fondo": (31, 58, 46), "texto": C["crema"],
           "oro": (212, 178, 106), "secundario": (94, 125, 106)}

def crop_frac(im, box):
    w, h = im.size
    return im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))


def fit(im, size):
    return ImageOps.fit(im, size, Image.LANCZOS)


def duotone(im, dark=C["tinta"], light=C["crema"], contrast=1.2):
    g = ImageOps.grayscale(im)
    g = ImageOps.autocontrast(g, cutoff=1)
    g = ImageEnhance.Contrast(g).enhance(contrast)
    return ImageOps.colorize(g, dark, light)


def grain(im, amount=16):
    n = Image.effect_noise(im.size, amount).convert("L")
    n = Image.merge("RGB", (n, n, n))
    out = ImageChops.add(im.convert("RGB"), n, 1.0, -128)
    if im.mode == "RGBA":
        out.putalpha(im.getchannel("A"))
    return out


def rough_mask(size, torn="", amp=7, seed=1):
    """Máscara rectangular; los lados en `torn` (t,b,l,r) quedan rasgados."""
    if len(torn) > 1 or any(s not in "tblr" for s in torn):
        raise ValueError("Usá como máximo un borde rasgado: t, b, l o r")
    rnd = random.Random(seed)
    w, h = size
    step = 9
    pts = []

    def jit(side):
        return rnd.uniform(0, amp) if side in torn else 0

    for x in range(0, w + 1, step):
        pts.append((x, jit("t")))
    for y in range(0, h + 1, step):
        pts.append((w - jit("r"), y))
    for x in range(w, -1, -step):
        pts.append((x, h - jit("b")))
    for y in range(h, -1, -step):
        pts.append((jit("l"), y))
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


def piece(im, torn="", seed=1, rotate=0):
    if abs(rotate) > 3:
        raise ValueError("La rotación máxima es 3 grados")
    p = im.convert("RGBA")
    p.putalpha(rough_mask(p.size, torn, seed=seed))
    if rotate:
        p = p.rotate(rotate, resample=Image.BICUBIC, expand=True)
    return p


def disc(d, color, seed=3):
    """Círculo de papel cortado a mano: borde levemente irregular."""
    rnd = random.Random(seed)
    s = 4
    big = Image.new("RGBA", (d * s, d * s), (0, 0, 0, 0))
    dr = ImageDraw.Draw(big)
    import math

    pts = []
    for i in range(90):
        a = 2 * math.pi * i / 90
        r = d * s / 2 - 2 - rnd.uniform(0, d * s * 0.012)
        pts.append((d * s / 2 + r * math.cos(a), d * s / 2 + r * math.sin(a)))
    dr.polygon(pts, fill=color + (255,))
    return grain(big.resize((d, d), Image.LANCZOS), 10)


def circle_window(im, d):
    """Recorte circular de una imagen (lupa, foco)."""
    p = fit(im, (d, d)).convert("RGBA")
    m = Image.new("L", (d * 4, d * 4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, d * 4 - 1, d * 4 - 1), fill=255)
    p.putalpha(m.resize((d, d), Image.LANCZOS))
    return p


def silhouette(im, tol=46):
    """Separa la figura de un fondo liso (el color de las esquinas superiores)."""
    px = im.load()
    w, h = im.size
    offset = min(3, (w - 1) // 2, (h - 1) // 2)
    bg = [sum(c) / 2 for c in zip(px[offset, offset], px[w - 1 - offset, offset])]
    diff = ImageChops.difference(im, Image.new("RGB", im.size, tuple(int(v) for v in bg)))
    g = ImageOps.grayscale(diff).point(lambda v: 255 if v > tol / 3 else 0)
    g = g.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(7)).filter(ImageFilter.MaxFilter(3))
    return g.filter(ImageFilter.GaussianBlur(1.2))


def cut_piece(p, torn="", seed=1, rotate=0):
    """Como piece(), pero conserva el alfa de una figura ya recortada."""
    if abs(rotate) > 3:
        raise ValueError("La rotación máxima es 3 grados")
    a = ImageChops.multiply(p.getchannel("A"), rough_mask(p.size, torn, seed=seed))
    p = p.copy()
    p.putalpha(a)
    return p.rotate(rotate, resample=Image.BICUBIC, expand=True) if rotate else p


def slab(size, color, torn="", seed=5):
    p = Image.new("RGB", size, color)
    return piece(grain(p, 12), torn, seed)


def label(text, size=46, paper=C["crema"], color=C["tinta"], rotate=0, font=FONT_ITALIC):
    f = ImageFont.truetype(font, size)
    l, t, r, b = f.getbbox(text)
    pad_x, pad_y = int(size * 0.45), int(size * 0.28)
    w, h = r - l + pad_x * 2, b - t + pad_y * 2
    p = Image.new("RGB", (w, h), paper)
    ImageDraw.Draw(p).text((pad_x - l, pad_y - t), text, font=f, fill=color)
    return piece(grain(p, 8), "", seed=len(text), rotate=rotate)


def paste(canvas, p, xy, shadow=True):
    x, y = int(xy[0]), int(xy[1])
    if shadow:
        a = p.getchannel("A")
        sh = Image.new("RGBA", p.size, (0, 0, 0, 0))
        sh.putalpha(a.point(lambda v: int(v * 0.6)))
        sh = sh.filter(ImageFilter.GaussianBlur(3))
        canvas.alpha_composite(sh, (x + 5, y + 7))
    canvas.alpha_composite(p, (x, y))


def fondo(historia=False, tema=None):
    color = NAVIDAD['fondo'] if tema == 'navidad' else C['crema']
    return grain(Image.new('RGB', (1080, 1920 if historia else 1350), color), 10).convert('RGBA')


def opalo(d, seed=3):
    """Un único motivo de ópalo formado por tres discos de papel."""
    out = Image.new('RGBA', (d, d))
    out.alpha_composite(disc(d, C['lavanda'], seed))
    out.alpha_composite(disc(int(d * .62), C['menta'], seed + 1),
                        (int(d * .30), int(d * .06)))
    out.alpha_composite(disc(int(d * .38), C['durazno'], seed + 2),
                        (int(d * .12), int(d * .52)))
    return out


def aretes_marcador(d=240):
    """Ilustración de posición; no representa una pieza a la venta."""
    s = 4
    im = Image.new('RGBA', (d * 2 * s, d * s))
    dr = ImageDraw.Draw(im)
    for cx in (d * s * .5, d * s * 1.5):
        r = d * s * .36
        box = (cx - r, d * s * .5 - r, cx + r, d * s * .5 + r)
        dr.ellipse(box, outline=(201, 160, 72, 255), width=int(d * s * .07))
        dr.arc(box, 200, 260, fill=(246, 226, 170, 255), width=int(d * s * .03))
    return im.resize((d * 2, d), Image.Resampling.LANCZOS)


def pieza(path):
    """Respeta PNG transparente; separa fondos lisos sin recolorear la joya."""
    if path is None or not Path(path).is_file():
        print(f'ADVERTENCIA: falta foto de pieza ({path or "sin ruta"}); se usa un marcador de argollas.', file=sys.stderr)
        return aretes_marcador()
    with Image.open(path) as source:
        is_png = source.format == 'PNG'
        im = ImageOps.exif_transpose(source).convert('RGBA')
        if is_png and im.getchannel('A').getextrema()[0] < 255:
            return im.copy()
        rgb = im.convert('RGB')
        im.putalpha(silhouette(rgb))
        return im


def texto_espaciado(canvas, xy=(80, 80), texto='OPALACA', size=26, color=None, spacing=9):
    font = ImageFont.truetype(FONT_SANS, size)
    draw = ImageDraw.Draw(canvas)
    x, y = xy
    for char in texto:
        draw.text((x, y), char, font=font, fill=color or C['oro'], anchor='lt')
        x += font.getlength(char) + spacing


def guardar(canvas, path, historia=False):
    expected = (1080, 1920 if historia else 1350)
    if canvas.size != expected:
        raise ValueError(f'El lienzo debe medir {expected}, no {canvas.size}')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    grain(canvas.convert('RGB'), 6).save(path, 'PNG')
    return path
