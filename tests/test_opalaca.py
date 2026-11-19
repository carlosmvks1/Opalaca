"""Contratos de datos, imagen y CLI; no requieren red ni fotos privadas."""
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageChops, ImageDraw
import yaml

import opalaca
from motor import collage

ROOT = opalaca.ROOT


class ImageTests(unittest.TestCase):
    def test_png_transparency_and_original_colors(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'test.png'
            im = Image.new('RGBA', (40, 40), (19, 82, 181, 0))
            im.putpixel((20, 20), (220, 48, 79, 137))
            im.save(path)
            self.assertEqual(collage.pieza(path).tobytes(), im.tobytes())

    def test_palette_png_transparency(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'palette.png'
            im = Image.new('P', (20, 20), 0)
            im.putpalette([255, 255, 255, 220, 24, 65] + [0] * 762)
            im.putpixel((10, 10), 1)
            im.save(path, transparency=0)
            result = collage.pieza(path)
            self.assertEqual(result.getpixel((0, 0))[3], 0)
            self.assertEqual(result.getpixel((10, 10)), (220, 24, 65, 255))

    def test_solid_background_removed_without_recoloring(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'opaque.png'
            im = Image.new('RGB', (100, 100), 'white')
            ImageDraw.Draw(im).rectangle((25, 25, 75, 75), fill=(205, 43, 65))
            im.save(path)
            result = collage.pieza(path)
            self.assertEqual(result.getpixel((50, 50)), (205, 43, 65, 255))
            self.assertEqual(result.getpixel((3, 3))[3], 0)

    def test_missing_photo_marker_warns(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            result = collage.pieza(None)
        self.assertIn('ADVERTENCIA', err.getvalue())
        self.assertEqual(result.mode, 'RGBA')
        self.assertEqual(result.getpixel((0, 0))[3], 0)

    def test_opal_geometry_uses_three_discs(self):
        with patch.object(collage, 'disc', side_effect=lambda d, color, seed: Image.new('RGBA', (d, d), color + (255,))) as disc:
            result = collage.opalo(100, seed=8)
        self.assertEqual([c.args for c in disc.call_args_list], [
            (100, collage.C['lavanda'], 8), (62, collage.C['menta'], 9),
            (38, collage.C['durazno'], 10)])
        self.assertEqual(result.getpixel((30, 6))[:3], collage.C['menta'])
        self.assertEqual(result.getpixel((12, 52))[:3], collage.C['durazno'])

    def test_cut_limits_and_alpha(self):
        im = Image.new('RGBA', (40, 40), (1, 2, 3, 127))
        self.assertLessEqual(collage.cut_piece(im).getchannel('A').getextrema()[1], 127)
        with self.assertRaises(ValueError):
            collage.piece(im, torn='lr')
        with self.assertRaises(ValueError):
            collage.piece(im, rotate=4)

    def test_margin_shadow_and_text_overflow(self):
        c = opalaca.Composition()
        with self.assertRaises(ValueError):
            c.put(Image.new('RGBA', (100, 100)), (900, 100))
        with self.assertRaises(ValueError):
            c.text_box('palabra' * 100, (100, 100, 100, 100))
        with self.assertRaises(ValueError):
            c.finish()
        c.opal(100, (100, 100))
        with self.assertRaises(ValueError):
            c.opal(100, (200, 200))


class DataTests(unittest.TestCase):
    def setUp(self):
        self.posts = yaml.safe_load((ROOT / 'posts/ejemplos.yaml').read_text())

    def test_example_templates_and_carousel(self):
        self.assertEqual({p['plantilla'] for p in self.posts}, opalaca.TEMPLATES)
        for post in self.posts:
            opalaca.validate(post)
        slides = opalaca.slides(self.posts[-1])
        self.assertEqual([name for name, _ in slides], ['favoritos-01', 'favoritos-02', 'favoritos-03'])
        self.assertEqual(slides[2][1]['lugar'], self.posts[-1]['lugar'])
        self.assertEqual(slides[1][1]['lugar'], 'fuentes/lugares/picacho.jpg')
        self.assertEqual(slides[1][1]['material'], 'plata 925')

    def test_invalid_product_data(self):
        for update in [{'precio': None}, {'material': ''}, {'estado': 'por encargo · 0 días'},
                       {'estado': 'pronto'}, {'nombre': '../otro'}, {'pieza': {}},
                       {'plantilla': 'inventada'}, {'lugar': 'no-existe.jpg'}]:
            with self.subTest(update=update), self.assertRaises(ValueError):
                opalaca.validate({**self.posts[0], **update})
        with self.assertRaises(ValueError):
            opalaca.validate({**self.posts[1], 'estado': 'disponible'})

    def test_story_and_guide_limits(self):
        with self.assertRaises(ValueError):
            opalaca.validate({**self.posts[3], 'texto': 'palabra ' * 41})
        for pieces in [['one'], ['one'] * 4, [{} , {}]]:
            with self.assertRaises(ValueError):
                opalaca.validate({**self.posts[2], 'piezas': pieces})

    def test_caption_honesty_credits_and_cta(self):
        for post in self.posts:
            for _, slide in opalaca.slides(post):
                caption = opalaca.caption(slide)
                self.assertTrue(caption.rstrip().endswith(opalaca.CTA))
                self.assertIn('creativecommons.org', caption)
        self.assertIn('no son una foto del producto', opalaca.caption(self.posts[0]))
        self.assertIn('no es la Sierra de Opalaca', opalaca.caption(self.posts[3]))
        self.assertIn('CC BY-SA 4.0', opalaca.caption(self.posts[0]))

    def products(self, count=4):
        return [{**self.posts[0], 'nombre': f'pieza-{i}',
                 'lugar': self.posts[i % 2]['lugar']} for i in range(count)]

    def test_layout_rotation_and_forcing(self):
        posts = self.products()
        self.assertEqual([p['layout'] for _, p in opalaca.plan(posts)], ['A', 'B', 'C', 'A'])
        self.assertNotIn('layout', posts[0])  # No mutar los datos del llamador.
        posts[1]['layout'] = 'A'
        result = [p['layout'] for _, p in opalaca.plan(posts)]
        self.assertEqual(result[1], 'A')
        self.assertTrue(all(a != b for a, b in zip(result, result[1:])))
        posts[0]['layout'] = 'A'
        with self.assertRaisesRegex(ValueError, 'consecutivos'):
            opalaca.plan(posts)
        with self.assertRaisesRegex(ValueError, 'layout'):
            opalaca.validate({**posts[0], 'layout': 'D'})

    def test_carousel_continues_rotation_and_alternates_places(self):
        jobs = opalaca.plan(self.posts)
        self.assertEqual([p['layout'] for _, p in jobs if 'layout' in p], ['A', 'B', 'C', 'A'])
        self.assertTrue(all(a['lugar'] != b['lugar'] for (_, a), (_, b) in zip(jobs, jobs[1:])))

    def test_repeated_place_warns_and_blocks_even_with_path_alias(self):
        posts = self.products(2)
        posts[1]['lugar'] = str(ROOT / posts[0]['lugar'])
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaisesRegex(ValueError, 'Alterná'):
            opalaca.plan(posts)
        self.assertIn('ADVERTENCIA: lugar repetido', err.getvalue())
        self.assertIn('pieza-0 y pieza-1', err.getvalue())

    def test_history_requires_place_and_contact_filename_is_reserved(self):
        for place in (None, '', 'foto-no-existe.jpg'):
            with self.assertRaises(ValueError):
                opalaca.validate({**self.posts[3], 'lugar': place})
        with self.assertRaisesRegex(ValueError, 'hoja.png'):
            opalaca.plan([{**self.posts[0], 'nombre': 'hoja'}])


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.posts = yaml.safe_load((ROOT / 'posts/ejemplos.yaml').read_text())

    def test_actual_jewel_and_type_in_every_layout_format_and_theme(self):
        # PNG sintético con mucho relleno transparente: medir la figura, no el archivo.
        jewel = Image.new('RGBA', (600, 600))
        ImageDraw.Draw(jewel).rectangle((200, 220, 399, 379), fill=(251, 11, 53, 255))
        original_text = ImageDraw.ImageDraw.text
        for layout in opalaca.LAYOUTS:
            for source in self.posts[:2]:
                for story in (False, True):
                    for theme in (None, 'navidad'):
                        drawn = []
                        def record(draw, xy, text, *args, **kwargs):
                            if kwargs.get('font'):
                                drawn.append((text, kwargs['font'].size))
                            return original_text(draw, xy, text, *args, **kwargs)
                        post = {**source, 'layout': layout}
                        with self.subTest(layout=layout, kind=post['plantilla'], story=story, theme=theme):
                            with patch.object(opalaca, 'pieza', return_value=jewel), patch.object(ImageDraw.ImageDraw, 'text', record):
                                canvas = opalaca.product(post, story, theme)
                            r, g, b = canvas.convert('RGB').split()
                            mask = ImageChops.multiply(r.point(lambda v: 255 if v > 230 else 0),
                                                       g.point(lambda v: 255 if v < 30 else 0))
                            left, top, right, bottom = mask.getbbox()
                            self.assertGreaterEqual(right - left, 486)
                            self.assertAlmostEqual((left + right) / 2, 540, delta=1)
                            self.assertGreaterEqual(top, 80)
                            self.assertLessEqual(bottom, canvas.height - 80)
                            for key, minimum in [('material', 36), ('precio', 46), ('estado', 46)]:
                                sizes = [size for text, size in drawn if text == post[key]]
                                self.assertTrue(sizes, key)
                                self.assertGreaterEqual(min(sizes), minimum)

    def test_narrow_and_empty_jewel_are_not_silently_shrunk(self):
        for im in [Image.new('RGBA', (30, 300), 'red'), Image.new('RGBA', (30, 300))]:
            with patch.object(opalaca, 'pieza', return_value=im), self.assertRaises(ValueError):
                opalaca.product(self.posts[0])

    def test_long_material_state_and_story_do_not_break_type_minima(self):
        for update in [{'material': 'material ' * 50}, {'estado': 'por encargo · ' + '9' * 80 + ' días'}]:
            with self.subTest(update=update), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(ValueError):
                opalaca.product({**self.posts[0], **update})
        with self.assertRaises(ValueError):
            opalaca.history({**self.posts[3], 'texto': ('extraordinariamente ' * 40).strip()})
        drawn = []
        original_text = ImageDraw.ImageDraw.text
        def record(draw, xy, text, *args, **kwargs):
            if kwargs.get('font'):
                drawn.append((text, kwargs['font'].size))
            return original_text(draw, xy, text, *args, **kwargs)
        with patch.object(ImageDraw.ImageDraw, 'text', record):
            opalaca.history(self.posts[3])
        self.assertTrue(any(text.startswith('Nuestro') for text, _ in drawn))
        self.assertTrue(all(size >= 40 for text, size in drawn if len(text) > 1))

    def test_contact_sheet_order_rows_and_no_crop(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = []
            colors = ['red', 'green', 'blue', 'yellow', 'cyan', 'magenta', 'black']
            for i, color in enumerate(colors):
                path = Path(temp) / f'{i}.png'
                Image.new('RGB', (1080, 1350), color).save(path)
                paths.append(path)
            out = Path(temp) / 'hoja.png'
            opalaca.contact_sheet(paths, out)
            with Image.open(out) as sheet:
                self.assertEqual(sheet.size, (1080, 1350))
                for i, color in enumerate(colors):
                    self.assertEqual(sheet.getpixel((i % 3 * 360 + 180, i // 3 * 450 + 225)),
                                     Image.new('RGB', (1, 1), color).getpixel((0, 0)))
                self.assertEqual(sheet.getpixel((900, 1125)), collage.C['crema'])


class CliTests(unittest.TestCase):
    def run_cli(self, *args, cwd=None):
        return subprocess.run([sys.executable, str(ROOT / 'opalaca.py'), *map(str, args)],
                              capture_output=True, text=True, cwd=cwd)

    def test_filter_story_christmas_from_other_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.run_cli(ROOT / 'posts/ejemplos.yaml', '--solo', 'argollas-oro',
                                  '--historia', '--tema', 'navidad', '--salida', temp, cwd=temp)
            self.assertEqual(result.returncode, 0, result.stderr)
            paths = [p for p in Path(temp).glob('*.png') if p.name != 'hoja.png']
            self.assertEqual(len(paths), 1)
            with Image.open(paths[0]) as im:
                self.assertEqual(im.size, (1080, 1920))
                self.assertEqual(im.mode, 'RGB')
                self.assertFalse(im.getexif())
                # Sobre fondo verde, el canal verde supera al rojo.
                r, g, b = im.getpixel((20, 20))
                self.assertGreater(g, r)
            self.assertIn('ADVERTENCIA', result.stderr)
            self.assertTrue(paths[0].with_suffix('.txt').is_file())
            with Image.open(Path(temp) / 'hoja.png') as sheet:
                self.assertEqual(sheet.size, (1080, 640))

    def test_solo_preserves_yaml_layout(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.run_cli(ROOT / 'posts/ejemplos.yaml', '--solo', 'collar-encargo', '--salida', temp)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('layout B', result.stdout)
            self.assertFalse((Path(temp) / 'argollas-oro.png').exists())

    def test_invalid_batches_write_nothing(self):
        base = yaml.safe_load((ROOT / 'posts/ejemplos.yaml').read_text())
        bad_batches = [[], {}, [None], [base[0], base[0]],
                       [{**base[0], 'precio': 'gratis'}],
                       [base[-1], {**base[0], 'nombre': 'favoritos-01'}],
                       [base[0], {**base[0], 'nombre': 'otra'}]]
        with tempfile.TemporaryDirectory() as temp:
            data = Path(temp) / 'posts.yaml'
            out = Path(temp) / 'out'
            for posts in bad_batches:
                with self.subTest(posts=posts):
                    data.write_text(yaml.safe_dump(posts))
                    result = self.run_cli(data, '--salida', out)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn('Error:', result.stderr)
                    self.assertNotIn('Traceback', result.stderr)
                    self.assertFalse(out.exists())

    def test_unknown_selection(self):
        result = self.run_cli(ROOT / 'posts/ejemplos.yaml', '--solo', 'no-existe')
        self.assertEqual(result.returncode, 2)
        self.assertIn('No existe el post', result.stderr)


if __name__ == '__main__':
    unittest.main()
