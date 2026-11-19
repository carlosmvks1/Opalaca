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
LAYOUTS = ('A', 'B', 'C')


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
    if 'layout' in post and (kind not in {'producto', 'encargo'} or post['layout'] not in LAYOUTS):
        raise ValueError('«layout» debe ser A, B o C, solo en producto/encargo o piezas del carrusel')
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

    def tag(self, text, xy, width=860, size=34, paper=None, font=FONT_SANS, rotate=0, minimum=24):
        color = NAVIDAD['texto'] if self.theme and paper == self.secondary else C['tinta']
        for current in range(size, minimum - 1, -1):
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

    def jewel(self, path, box, minimum_width=0):
        path = ROOT / path if path else None
        self.markers |= path is None or not path.is_file()
        im = pieza(path)
        bounds = im.getbbox()
        if not bounds:
            raise ValueError(f'La foto de pieza no contiene píxeles visibles: {path}')
        im = im.crop(bounds)
        x, y, w, h = box
        im = ImageOps.contain(im, (w, h), Image.Resampling.LANCZOS)
        if im.width < minimum_width:
            raise ValueError(f'La joya debe ocupar al menos {minimum_width} px (45 % del ancho). '
                             'Usá una toma menos estrecha: no se deforma ni recorta la pieza.')
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
    layout = post.get('layout', 'A')
    if layout == 'A':
        c.photo(post['lugar'], (140, 195), (560, 300 + e // 3))
        c.opal(270, (660, 475 + e))
    elif layout == 'B':
        c.photo(post['lugar'], (380, 260), (560, 300 + e // 3), rotate=1)
        c.opal(270, (150, 475 + e))
    elif layout == 'C':
        c.photo(post['lugar'], (135, 205), (300, 490 + e // 2))
        c.opal(270, (675, 230 + e // 3))
    else:
        raise ValueError('Layout desconocido: usá A, B o C')
    c.jewel(post.get('pieza'), (180, 195, 720, 550 + e), minimum_width=486)
    lower = e - (50 if post['plantilla'] == 'encargo' else 0)
    c.tag(post['frase'], (106, 805 + lower), size=60, font=FONT_ITALIC, rotate=1.5)
    c.text_box(post.get('tipo', post['nombre'].replace('-', ' ').capitalize()),
               (106, 920 + lower, 860, 56), size=40, minimum=36)
    # El papel neutro no añade un tercer acento: producto = oro; encargo = oro + menta.
    c.tag(post['material'], (110, 980 + lower), size=40, minimum=36)
    c.put(piece(Image.new('RGB', (860, 154), c.gold)), (110, 1060 + lower))
    c.text_box(post['precio'], (126, 1069 + lower, 820, 80), size=60, minimum=46, color=C['tinta'])
    c.text_box(post['estado'], (126, 1145 + lower, 820, 62), size=46, minimum=46, color=C['tinta'])
    if post['plantilla'] == 'encargo':
        c.tag('50 % de anticipo', (110, 1180 + e), size=30, paper=c.secondary)
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
    c.text_box(post['titulo'], (102, 175, 860, 155), size=72, font=FONT_ITALIC, minimum=40)
    c.photo(post['lugar'], (115, 350), (680, 350 + e))
    c.opal(320, (640, 570 + e))
    c.text_box(post['texto'], (106, 925 + e, 860, 300), size=42, font=FONT_SEMI, minimum=40)
    return c.finish()


def slides(post):
    if post['plantilla'] != 'carrusel':
        return [(post['nombre'], post)]
    cover = {**post, 'plantilla': 'guia', 'piezas': []}
    return [(f'{post["nombre"]}-01', cover)] + [
        (f'{post["nombre"]}-{i:02d}', product_slide(post, item))
        for i, item in enumerate(post['piezas'], 2)
    ]


def plan(posts):
    """Resuelve layouts antes del filtro; comprueba toda la secuencia de láminas."""
    jobs = [(name, dict(slide)) for post in posts for name, slide in slides(post)]
    names = [name for name, _ in jobs]
    if len(names) != len(set(names)) or 'hoja' in names:
        raise ValueError('Hay nombres de archivo en conflicto con un carrusel o con hoja.png')
    products = [post for _, post in jobs if post['plantilla'] in {'producto', 'encargo'}]
    previous = None
    for i, post in enumerate(products):
        forced = post.get('layout')
        if forced:
            if forced == previous:
                raise ValueError(f'{post["nombre"]}: dos productos consecutivos fuerzan layout {forced}')
            chosen = forced
        else:
            next_forced = products[i + 1].get('layout') if i + 1 < len(products) else None
            chosen = next(LAYOUTS[(i + shift) % 3] for shift in range(3)
                          if LAYOUTS[(i + shift) % 3] not in (previous, next_forced))
        post['layout'] = previous = chosen
    repeated = False
    for (left_name, left), (right_name, right) in zip(jobs, jobs[1:]):
        if (ROOT / left['lugar']).resolve() == (ROOT / right['lugar']).resolve():
            print(f'ADVERTENCIA: lugar repetido entre {left_name} y {right_name}: {right["lugar"]}', file=sys.stderr)
            repeated = True
    if repeated:
        raise ValueError('Alterná los lugares en el YAML antes de generar; no se sustituyen fotos automáticamente')
    return jobs


def contact_sheet(paths, destination):
    """Cuadrícula 3 × N, en orden YAML, hecha de los PNG finales (sin recorte)."""
    if not paths:
        raise ValueError('La hoja necesita al menos una imagen')
    with Image.open(paths[0]) as first:
        cell = (360, round(360 * first.height / first.width))
    sheet = Image.new('RGB', (cell[0] * 3, cell[1] * ((len(paths) + 2) // 3)), C['crema'])
    for i, path in enumerate(paths):
        with Image.open(path) as im:
            thumb = ImageOps.contain(im.convert('RGB'), cell, Image.Resampling.LANCZOS)
            x, y = (i % 3) * cell[0], (i // 3) * cell[1]
            sheet.paste(thumb, (x + (cell[0] - thumb.width) // 2, y + (cell[1] - thumb.height) // 2))
    sheet.save(destination, 'PNG')


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
        jobs = plan(posts)
        if args.solo:
            selected = next((p for p in posts if p['nombre'] == args.solo), None)
            if selected is None:
                raise ValueError(f'No existe el post «{args.solo}»')
            selected_names = {name for name, _ in slides(selected)}
            jobs = [(name, post) for name, post in jobs if name in selected_names]
        variant = '-'.join(x for x in ('historias' if args.historia else '', args.tema or '') if x)
        out = args.salida or ROOT / 'salida' / (variant or 'muestras')
        renderers = {'producto': product, 'encargo': product, 'guia': guide, 'historia': history}
        # Renderizar todo antes de escribir: un dato inválido no deja un lote parcial.
        rendered = [(name, post, renderers[post['plantilla']](post, args.historia, args.tema)) for name, post in jobs]
        paths = []
        for name, post, canvas in rendered:
            path = guardar(canvas, out / f'{name}.png', args.historia)
            paths.append(path)
            path.with_suffix('.txt').write_text(caption(post), encoding='utf-8')
            print(f'{path} · {canvas.width} × {canvas.height}' + (f' · layout {post["layout"]}' if 'layout' in post else ''))
        contact_sheet(paths, out / 'hoja.png')
        print(f'{out / "hoja.png"} · cuadrícula de 3 columnas')
    except (ValueError, OSError, yaml.YAMLError, Image.DecompressionBombError) as exc:
        parser.exit(2, f'Error: {exc}\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
