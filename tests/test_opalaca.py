"""Contratos de datos, imagen y CLI; no requieren red ni fotos privadas."""
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw
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
        self.assertEqual(slides[1][1]['lugar'], self.posts[-1]['lugar'])
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
        self.assertIn('CC BY-SA 4.0', opalaca.caption(self.posts[1]))


class CliTests(unittest.TestCase):
    def run_cli(self, *args, cwd=None):
        return subprocess.run([sys.executable, str(ROOT / 'opalaca.py'), *map(str, args)],
                              capture_output=True, text=True, cwd=cwd)

    def test_filter_story_christmas_from_other_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.run_cli(ROOT / 'posts/ejemplos.yaml', '--solo', 'argollas-oro',
                                  '--historia', '--tema', 'navidad', '--salida', temp, cwd=temp)
            self.assertEqual(result.returncode, 0, result.stderr)
            paths = list(Path(temp).glob('*.png'))
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

    def test_invalid_batches_write_nothing(self):
        base = yaml.safe_load((ROOT / 'posts/ejemplos.yaml').read_text())
        bad_batches = [[], {}, [None], [base[0], base[0]],
                       [{**base[0], 'precio': 'gratis'}],
                       [base[-1], {**base[0], 'nombre': 'favoritos-01'}]]
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
