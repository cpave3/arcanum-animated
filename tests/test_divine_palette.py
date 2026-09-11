import hashlib
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image

from animation_fx.catalog import EFFECTS
from animation_fx.palettes import PALETTES, Palette, colorize
from animation_fx.viewer_catalog import build_viewer_catalog


class DivinePaletteTests(unittest.TestCase):
    def test_colorize_ramp_has_three_tones_and_exact_alpha_and_value(self):
        values = np.arange(256, dtype=np.uint8)
        pixels = np.zeros((3, 256, 4), dtype=np.uint8)
        pixels[0, :, :3] = values[:, None]  # Neutral master pixels also get tinted.
        pixels[1, :, :3] = np.stack((values, values // 4, values // 2), axis=-1)
        pixels[2, :, :3] = np.stack((values // 3, values, values // 5), axis=-1)
        pixels[:, :, 3] = values[::-1]
        image = Image.fromarray(pixels)
        for source in ('purple', 'gold'):
            with self.subTest(source=source):
                result = np.asarray(colorize(image, PALETTES[source], PALETTES['divine']))
                np.testing.assert_array_equal(result[:, :, 3], pixels[:, :, 3])
                np.testing.assert_array_equal(result[:, :, :3].max(axis=2), pixels[:, :, :3].max(axis=2))
                np.testing.assert_array_equal(result[0], result[1])
                np.testing.assert_array_equal(result[0], result[2])
                np.testing.assert_array_equal(result[0, 0, :3], [0, 0, 0])
                r, g, b = result[0, 40, :3]
                self.assertLess(r, g)
                self.assertLess(g, b)
                self.assertLess(b, 60)
                r, g, b = result[0, 150, :3]
                self.assertGreater(r, g)
                self.assertGreater(g, 2 * int(b))
                r, g, b = result[0, 245, :3]
                self.assertLess(r, g)
                self.assertLess(g, b)
                self.assertGreater(r, 210)
        np.testing.assert_array_equal(np.asarray(image), pixels)

    def test_every_effect_renders_divine_without_changing_alpha_or_value(self):
        for name, effect in EFFECTS.items():
            with self.subTest(effect=name):
                master = np.asarray(effect.master(effect.poster_frame))
                divine = effect.render(effect.poster_frame, 'divine')
                result = np.asarray(divine)
                self.assertEqual(divine.mode, 'RGBA')
                self.assertEqual(result.shape, master.shape)
                np.testing.assert_array_equal(result[:, :, 3], master[:, :, 3])
                np.testing.assert_array_equal(result[:, :, :3].max(axis=2), master[:, :, :3].max(axis=2))
                visible = master[:, :, 3] > 100
                self.assertTrue(visible.any())
                self.assertFalse(np.array_equal(result[visible, :3], master[visible, :3]))

    def test_rift_render_contains_blue_shadows_gold_rims_and_searing_highlights(self):
        pixels = np.asarray(EFFECTS['rift'].render(0, 'divine'))
        value = pixels[:, :, :3].max(axis=2)
        visible = pixels[:, :, 3] > 100
        for low, high, tone in ((15, 56, 'blue'), (128, 183, 'gold'), (238, 255, 'white-blue')):
            with self.subTest(tone=tone):
                selected = pixels[visible & (value >= low) & (value <= high), :3]
                self.assertGreater(len(selected), 0)
                r, g, b = selected.T.astype(int)
                if tone == 'gold':
                    self.assertTrue(np.all((r > g) & (g > b)))
                else:
                    self.assertTrue(np.all((b > g) & (g > r)))
                    if tone == 'white-blue':
                        self.assertTrue(np.all(r > .8 * b))

    def test_optional_gradient_is_used_by_colorize(self):
        target = Palette(42, gradient=((0, (0, 0, 1)), (1, (1, 0, 0))))
        image = Image.fromarray(np.array([[[128, 64, 0, 17]]], dtype=np.uint8))
        result = np.asarray(colorize(image, PALETTES['purple'], target))
        np.testing.assert_array_equal(result, [[[128, 0, 127, 17]]])

    def test_same_palette_returns_independent_identical_copy(self):
        image = EFFECTS['rift'].render(0, 'divine')
        result = colorize(image, PALETTES['divine'], PALETTES['divine'])
        self.assertIsNot(result, image)
        self.assertEqual(result.tobytes(), image.tobytes())

    def test_existing_colorize_outputs_are_byte_identical(self):
        # Golden digests captured before introducing gradients, in registry order.
        names = ('purple', 'gold', 'red', 'orange', 'acid', 'cold', 'fire', 'force',
                 'lightning', 'melee', 'necrotic', 'poison', 'psychic', 'radiant', 'thunder')
        expected = {
            'purple': '727adaae0973602f0fd6e0c94d85095b684bb32cf7a0d7eaf5da4fc6c2f81ae1',
            'gold': '61d98d4bb59ec6e8380c7ef0986d5f422d6c40df1c5d935fb2bd1c7dbcb02687',
        }
        image = Image.fromarray(np.random.default_rng(2718).integers(0, 256, (32, 32, 4), dtype=np.uint8))
        for source, digest in expected.items():
            with self.subTest(source=source):
                output = b''.join(colorize(image, PALETTES[source], PALETTES[name]).tobytes()
                                  for name in names)
                self.assertEqual(hashlib.sha256(output).hexdigest(), digest)

    def test_viewer_catalog_exposes_divine_with_hue_swatch(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog = build_viewer_catalog(Path(directory))
        divine = next(palette for palette in catalog['palettes'] if palette['id'] == 'divine')
        self.assertEqual(divine['label'], 'Divine')
        self.assertEqual(divine['swatch'], '#ffb200')


if __name__ == '__main__':
    unittest.main()
