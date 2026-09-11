import hashlib
import unittest

import numpy as np
from PIL import Image

from animation_fx.catalog import EFFECTS
from animation_fx.palettes import PALETTES, colorize


class EldritchPaletteTests(unittest.TestCase):
    def test_colorize_ramps_preserve_exact_alpha_and_value_with_infernal_tones(self):
        values = np.arange(256, dtype=np.uint8)
        pixels = np.zeros((3, 256, 4), dtype=np.uint8)
        pixels[0, :, :3] = values[:, None]
        pixels[1, :, :3] = np.stack((values, values // 4, values // 2), axis=-1)
        pixels[2, :, :3] = np.stack((values // 3, values, values // 5), axis=-1)
        pixels[:, :, 3] = values[::-1]
        image = Image.fromarray(pixels)
        for source in ('purple', 'gold', 'divine'):
            with self.subTest(source=source):
                result = np.asarray(colorize(image, PALETTES[source], PALETTES['eldritch']))
                np.testing.assert_array_equal(result[:, :, 3], pixels[:, :, 3])
                np.testing.assert_array_equal(result[:, :, :3].max(axis=2), pixels[:, :, :3].max(axis=2))
                np.testing.assert_array_equal(result[0], result[1])
                np.testing.assert_array_equal(result[0], result[2])
                np.testing.assert_array_equal(result[0, 0], [0, 0, 0, 255])
                self.assertEqual(result[0, 255, 3], 0)
                r, g, b = result[0, 20, :3].astype(int)
                self.assertTrue(0 <= g < r < b <= 20)
                r, g, b = result[0, 115, :3].astype(int)
                self.assertTrue(g < r < b)
                r, g, b = result[0, 165, :3].astype(int)
                self.assertTrue(g < b < r)
                r, g, b = result[0, 217:, :3].T.astype(int)
                self.assertTrue(np.all((g < .05 * r) & (b < .13 * r)))
        np.testing.assert_array_equal(np.asarray(image), pixels)

    def test_every_effect_renders_eldritch_without_changing_alpha_or_value(self):
        for name, effect in EFFECTS.items():
            with self.subTest(effect=name):
                master = np.asarray(effect.master(effect.poster_frame))
                image = effect.render(effect.poster_frame, 'eldritch')
                result = np.asarray(image)
                self.assertEqual(image.mode, 'RGBA')
                self.assertEqual(result.shape, master.shape)
                np.testing.assert_array_equal(result[:, :, 3], master[:, :, 3])
                np.testing.assert_array_equal(result[:, :, :3].max(axis=2), master[:, :, :3].max(axis=2))
                visible = master[:, :, 3] > 100
                self.assertTrue(visible.any())
                self.assertFalse(np.array_equal(result[visible, :3], master[visible, :3]))

    def test_rift_render_contains_dark_violet_purple_magenta_and_red(self):
        pixels = np.asarray(EFFECTS['rift'].render(0, 'eldritch'))
        value = pixels[:, :, :3].max(axis=2)
        visible = pixels[:, :, 3] > 100
        for low, high, tone in ((15, 50, 'violet'), (90, 115, 'purple'),
                                (160, 175, 'magenta'), (217, 255, 'red')):
            with self.subTest(tone=tone):
                selected = pixels[visible & (value >= low) & (value <= high), :3]
                self.assertGreater(len(selected), 0)
                r, g, b = selected.T.astype(int)
                if tone in ('violet', 'purple'):
                    self.assertTrue(np.all((g < r) & (r < b)))
                elif tone == 'magenta':
                    self.assertTrue(np.all((g < b) & (b < r)))
                else:
                    self.assertTrue(np.all((g < .05 * r) & (b < .13 * r)))

    def test_same_palette_returns_independent_identical_copy(self):
        image = EFFECTS['rift'].render(0, 'eldritch')
        result = colorize(image, PALETTES['eldritch'], PALETTES['eldritch'])
        self.assertIsNot(result, image)
        self.assertEqual(result.tobytes(), image.tobytes())

    def test_all_prior_palette_pairs_are_byte_identical(self):
        names = ('purple', 'gold', 'red', 'orange', 'acid', 'cold', 'fire', 'force',
                 'lightning', 'melee', 'necrotic', 'poison', 'psychic', 'radiant',
                 'thunder', 'divine')
        # Captured before adding Eldritch, concatenating targets in names order.
        expected = {
            'purple': '26781b4a52945aeb653799f09c65b1dcfda5da495c3566e830f60225fed72abc',
            'gold': '39a77e41ada2143e5627247c54c9f67fbffbaa02f45b4251212e973baf26a1ed',
            'red': 'b34fddc9dccd4a6af5076d10f9591baf32503faebe93aec3a488ac545dedb1fc',
            'orange': '312517ae744e6d64380e284bf6b6dd5e46095173348f1dfa6e195ef10d9eefe4',
            'acid': '5f7b3f5b90a0ab9b7ae3c27f1897aaa624af661e4ae897311466bd4c2afe247b',
            'cold': 'a4bf95c65966454d2d726f2daa075639d0ed33d649510555f7ee89c3135f16a0',
            'fire': 'b0482a4517e46a4c24b86dab042cbb83b54c448120f97fc115c61133d5d76610',
            'force': 'b34fddc9dccd4a6af5076d10f9591baf32503faebe93aec3a488ac545dedb1fc',
            'lightning': 'd5cbbb1b2de6725d65faf849d4e052785a9ac9ffe16e6982ee86ba54c01d19a5',
            'melee': 'f4e8d9fa238a1b049738e559f37f28299fdae2c916484f02542a60cecb0d8d0f',
            'necrotic': '2cf3e36f073d32ca93d7fe4c701e55df67dd6e1bed1601ec36e8ec9377a7797d',
            'poison': '20da8b4825043062ab213160be3f488752337e509232b606a18b0a20d619b0cb',
            'psychic': 'ed87868c550ae13c81458655e0445fcf946ae4542214d6795618765fef5d1d00',
            'radiant': '39a77e41ada2143e5627247c54c9f67fbffbaa02f45b4251212e973baf26a1ed',
            'thunder': '433a6b56b2ee99ecba7375437aeef5a96d9285be6716bd4321d0ceec46f05748',
            'divine': '6446c4ac77a2e12ee5e637d9a6ea5472f51254aa7b27a94be5547119917c6172',
        }
        image = Image.fromarray(np.random.default_rng(2718).integers(0, 256, (32, 32, 4), dtype=np.uint8))
        for source, digest in expected.items():
            with self.subTest(source=source):
                output = b''.join(colorize(image, PALETTES[source], PALETTES[name]).tobytes()
                                  for name in names)
                self.assertEqual(hashlib.sha256(output).hexdigest(), digest)


if __name__ == '__main__':
    unittest.main()
