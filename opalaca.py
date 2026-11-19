#!/usr/bin/env python3
"""Generador de posts Opalaca. Los datos viven en YAML, el collage en motor/."""
import argparse
import re
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont, ImageOps

from motor.collage import (
    C, NAVIDAD, FONT_ITALIC, FONT_SANS, FONT_SEMI, fondo, fit, duotone,
    piece, pieza, opalo, paste, label, guardar, texto_espaciado,
)

ROOT = Path(__file__).resolve().parent
CTA = '📩 Escribinos al WhatsApp del perfil'
TEMPLATES = {'producto', 'encargo', 'guia', 'historia', 'carrusel'}


def required(post, keys):
    for key in keys:
        if not isinstance(post.get(key), str) or not post[key].strip():
            raise ValueError(f'{post.get("nombre", "entrada")}: falta texto en «{key}»')


def validate(post):
    if not isinstance(post, dict):
        raise ValueError('Cada post debe ser un mapa YAML')
    required(post, ['nombre', 'plantilla', 'lugar'])
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', post['nombre']):
        raise ValueError('«nombre» debe ser un identificador como argollas-oro')
    kind = post['plantilla']
    if kind not in TEMPLATES:
        raise ValueError(f'Plantilla desconocida: {kind}')
    if not (ROOT / post['lugar']).is_file():
        raise ValueError(f'No existe la foto de lugar: {post["lugar"]}')
    if 'pieza' in post and post['pieza'] is not None and not isinstance(post['pieza'], str):
        raise ValueError('«pieza» debe ser una ruta o null')
    if kind in {'producto', 'encargo'}:
        required(post, ['frase', 'material', 'precio', 'estado'])
        if 'tipo' in post:
            required(post, ['tipo'])
        if not re.fullmatch(r'L\s?\d+(?:[.,]\d{2})?', post['precio']):
            raise ValueError('Precio inválido: usá L350 o L350.00')
        ordered = re.fullmatch(r'por encargo · [1-9]\d* días', post['estado'])
        if post['estado'] != 'disponible' and not ordered:
            raise ValueError('Estado: disponible o por encargo · N días')
        if kind == 'encargo' and not ordered:
            raise ValueError('La plantilla encargo requiere por encargo · N días')
    elif kind == 'historia':
        required(post, ['titulo', 'texto'])
        if len(post['texto'].split()) > 40:
            raise ValueError('La historia admite como máximo 40 palabras')
    else:
        required(post, ['titulo', 'rango'])
        pieces = post.get('piezas', [])
        if not isinstance(pieces, list):
            raise ValueError('«piezas» debe ser una lista')
        if kind == 'guia':
            if pieces and len(pieces) not in (2, 3):
                raise ValueError('La guía admite 2 o 3 piezas, o ninguna')
            if any(p is not None and not isinstance(p, str) for p in pieces):
                raise ValueError('Las piezas de la guía deben ser rutas o null')
        else:
            if not pieces:
                raise ValueError('El carrusel necesita al menos una pieza')
            for item in pieces:
                if not isinstance(item, dict):
                    raise ValueError('Cada pieza del carrusel debe ser un mapa')
                validate(product_slide(post, item))


def product_slide(parent, item):
    return {'lugar': parent['lugar'], **item, 'plantilla': 'producto'}


def wrap(text, font, width):
    lines = []
    for paragraph in text.splitlines():
        line = ''
        for word in paragraph.split():
            if font.getlength(word) > width:
                return None
            candidate = f'{line} {word}'.strip()
            if font.getlength(candidate) > width:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    return lines


class Composition:
    """Composición acotada: comprueba márgenes, tipografía y un motivo de ópalo."""
    def __init__(self, story=False, theme=None):
        self.canvas = fondo(story, theme)
        self.extra = self.canvas.height - 1350
        self.text = NAVIDAD['texto'] if theme else C['tinta']
        self.gold = NAVIDAD['oro'] if theme else C['oro']
        self.secondary = NAVIDAD['secundario'] if theme else C['menta']
        self.theme = theme
        self.opals = 0
        self.markers = False
        texto_espaciado(self.canvas, color=self.gold)

    def put(self, im, xy, shadow=True):
        x, y = xy
        # Reserva también la extensión de la sombra de 5 × 7 px.
        if x < 80 or y < 80 or x + im.width + (5 if shadow else 0) > 1000 or y + im.height + (7 if shadow else 0) > self.canvas.height - 80:
            raise ValueError(f'Composición fuera del margen de 80 px: {xy}, {im.size}')
        paste(self.canvas, im, xy, shadow)

    def text_box(self, text, box, size=40, font=FONT_SANS, color=None, minimum=24):
        x, y, width, height = box
        for current in range(size, minimum - 1, -1):
            face = ImageFont.truetype(font, current)
            lines = wrap(text, face, width - 8)
            step = round(current * 1.32)
            if lines and len(lines) * step <= height:
                break
        else:
            raise ValueError(f'Texto demasiado largo para su espacio: {text!r}')
        layer = Image.new('RGBA', (width, height))
        draw = ImageDraw.Draw(layer)
        for i, line in enumerate(lines):
            draw.text((4, i * step), line, font=face, fill=color or self.text, anchor='lt')
        self.put(layer, (x, y), shadow=False)

    def tag(self, text, xy, width=860, size=34, paper=None, font=FONT_SANS, rotate=0):
        color = NAVIDAD['texto'] if self.theme and paper == self.secondary else C['tinta']
        for current in range(size, 23, -1):
            im = label(text, current, paper=paper or C['papel'], color=color, font=font, rotate=rotate)
            if im.width <= width:
                self.put(im, xy)
                return
        raise ValueError(f'Etiqueta demasiado larga: {text!r}')

    def photo(self, path, xy, size, torn='b', rotate=-1):
        with Image.open(ROOT / path) as source:
            rgb = ImageOps.exif_transpose(source).convert('RGB')
            im = duotone(fit(rgb, size), dark=C['tinta'], light=C['crema'], contrast=1.25)
        self.put(piece(im, torn=torn, rotate=rotate, seed=4), xy)

    def jewel(self, path, box):
        path = ROOT / path if path else None
        self.markers |= path is None or not path.is_file()
        im = pieza(path)
        bounds = im.getbbox()
        if bounds:
            im = im.crop(bounds)
        x, y, w, h = box
        im = ImageOps.contain(im, (w, h), Image.Resampling.LANCZOS)
        self.put(im, (x + (w - im.width) // 2, y + (h - im.height) // 2))

    def opal(self, d, xy):
        self.opals += 1
        if self.opals != 1:
            raise ValueError('Cada post lleva exactamente un motivo de ópalo')
        self.put(opalo(d), xy)

    def finish(self):
        if self.opals != 1:
            raise ValueError('Falta el disco de ópalo')
        if self.markers:
            self.text_box('Muestra · foto de pieza pendiente', (106, self.canvas.height - 116, 860, 34), size=24)
        return self.canvas


def product(post, story=False, theme=None):
    c = Composition(story, theme)
    e = c.extra
    c.photo(post['lugar'], (120, 190), (820, 490 + e))
    c.opal(370, (590, 530 + e))
    c.jewel(post.get('pieza'), (145, 510 + e, 510, 310))
    c.tag(post['frase'], (106, 835 + e), size=64, font=FONT_ITALIC, rotate=1.5)
    c.text_box(post.get('tipo', post['nombre'].replace('-', ' ').capitalize()),
               (106, 955 + e, 860, 53), size=38)
    # El papel neutro no añade un tercer acento: producto = oro; encargo = oro + menta.
    c.tag(post['material'], (110, 1016 + e), size=32)
    c.tag(f'{post["precio"]} · {post["estado"]}', (110, 1082 + e), size=34, paper=c.gold)
    if post['plantilla'] == 'encargo':
        c.tag('50 % de anticipo', (110, 1150 + e), size=30, paper=c.secondary)
    return c.finish()


def guide(post, story=False, theme=None):
    c = Composition(story, theme)
    e = c.extra
    c.opal(310, (650, 180))
    c.text_box(post['titulo'], (102, 175, 540, 190), size=106, font=FONT_ITALIC, minimum=40)
    c.photo(post['lugar'], (110, 450), (840, 490 + e), torn='t', rotate=1)
    paths = post.get('piezas', [])
    for i, path in enumerate(paths):
        w = 780 // len(paths)
        c.jewel(path, (135 + i * w, 650 + e, w - 20, 230))
    c.tag(post['rango'], (110, 1000 + e), size=58,
          paper=NAVIDAD['secundario'] if theme else C['lavanda'])
    c.tag('listos para regalar', (110, 1135 + e), size=34, paper=c.secondary)
    return c.finish()


def history(post, story=False, theme=None):
    c = Composition(story, theme)
    e = c.extra
    c.text_box(post['titulo'], (102, 175, 860, 155), size=72, font=FONT_ITALIC, minimum=36)
    c.photo(post['lugar'], (115, 370), (820, 430 + e))
    c.opal(390, (570, 620 + e))
    c.text_box(post['texto'], (106, 1050 + e, 860, 175), size=34, font=FONT_SEMI)
    return c.finish()


def slides(post):
    if post['plantilla'] != 'carrusel':
        return [(post['nombre'], post)]
    cover = {**post, 'plantilla': 'guia', 'piezas': []}
    return [(f'{post["nombre"]}-01', cover)] + [
        (f'{post["nombre"]}-{i:02d}', product_slide(post, item))
        for i, item in enumerate(post['piezas'], 2)
    ]


def caption(post):
    lines = [post.get('tipo', post.get('titulo', post['nombre'].replace('-', ' ')))]
    for key in ['frase', 'material', 'precio', 'estado', 'rango', 'texto']:
        if key in post:
            lines.append(post[key])
    if post['plantilla'] == 'encargo':
        lines.append('50 % de anticipo')
    paths = [post.get('pieza')] if post['plantilla'] in {'producto', 'encargo'} else post.get('piezas', [])
    if any(p is None or not (ROOT / p).is_file() for p in paths):
        lines.append('Muestra de diseño. Argollas ilustradas: no son una foto del producto. Datos de ejemplo; confirmar antes de publicar.')
    if post['plantilla'] == 'historia':
        lines.append('La inspiración es hondureña; no implica que las piezas se fabriquen en Honduras o contengan ópalo.')
    photo = (ROOT / post['lugar']).resolve()
    if photo == (ROOT / 'fuentes/lugares/picacho.jpg').resolve():
        lines.append('Foto: El Picacho, Tegucigalpa (no es la Sierra de Opalaca), Ian Mackenzie (madmack66), CC BY 2.0. https://commons.wikimedia.org/wiki/File:El_Picacho_at_dusk.jpg — https://creativecommons.org/licenses/by/2.0/ . Modificada: recorte, duotono y collage.')
    elif photo == (ROOT / 'fuentes/lugares/calle.jpg').resolve():
        lines.append('Foto: Tegucigalpa Honduras street, chamo estudio, CC BY-SA 2.0. https://commons.wikimedia.org/wiki/File:Tegucigalpa_Honduras_street.jpg — https://creativecommons.org/licenses/by-sa/2.0/ . Modificada: recorte, duotono y collage. Esta composición se comparte bajo CC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/ .')
    lines.append(CTA)
    return '\n\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archivo', type=Path)
    parser.add_argument('--solo', metavar='NOMBRE')
    parser.add_argument('--historia', action='store_true', help='Formato 1080 × 1920 (cualquier plantilla)')
    parser.add_argument('--tema', choices=['navidad'])
    parser.add_argument('--salida', type=Path, help='Carpeta de destino; predeterminado: salida/muestras')
    args = parser.parse_args(argv)
    try:
        posts = yaml.safe_load(args.archivo.read_text(encoding='utf-8'))
        if not isinstance(posts, list) or not posts:
            raise ValueError('El YAML debe contener una lista no vacía de posts')
        names = []
        for post in posts:
            validate(post)
            names.append(post['nombre'])
        if len(names) != len(set(names)):
            raise ValueError('Hay nombres de posts repetidos')
        if args.solo:
            posts = [p for p in posts if p['nombre'] == args.solo]
            if not posts:
                raise ValueError(f'No existe el post «{args.solo}»')
        jobs = [slide for post in posts for slide in slides(post)]
        filenames = [name for name, _ in jobs]
        if len(filenames) != len(set(filenames)):
            raise ValueError('Hay nombres de archivo en conflicto con un carrusel')
        variant = '-'.join(x for x in ('historias' if args.historia else '', args.tema or '') if x)
        out = args.salida or ROOT / 'salida' / (variant or 'muestras')
        renderers = {'producto': product, 'encargo': product, 'guia': guide, 'historia': history}
        # Renderizar todo antes de escribir: un dato inválido no deja un lote parcial.
        rendered = [(name, post, renderers[post['plantilla']](post, args.historia, args.tema)) for name, post in jobs]
        for name, post, canvas in rendered:
            path = guardar(canvas, out / f'{name}.png', args.historia)
            path.with_suffix('.txt').write_text(caption(post), encoding='utf-8')
            print(f'{path} · {canvas.width} × {canvas.height}')
    except (ValueError, OSError, yaml.YAMLError, Image.DecompressionBombError) as exc:
        parser.exit(2, f'Error: {exc}\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
