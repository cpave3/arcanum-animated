import unittest

import numpy as np

from animation_fx.catalog import EFFECTS
from animation_fx.palettes import PALETTES


class CelestialRevelationTests(unittest.TestCase):
    """Public Effect.render must visibly gather, contract, burst, and clear in every palette."""

    def setUp(self):
        self.effect = EFFECTS['celestial-revelation']
        self.y, self.x = np.mgrid[:640, :640]
        self.radius = np.hypot(self.x-320, self.y-320)

    def pixels(self, frame, color='divine'):
        return np.asarray(self.effect.render(frame, color))

    def mean_radius(self, frame):
        alpha = self.pixels(frame)[..., 3].astype(float)
        return (alpha*self.radius).sum()/alpha.sum()

    def test_pool_fades_in_then_contracts_to_a_bright_core(self):
        early = self.pixels(6)[..., 3]
        pool = self.pixels(42)[..., 3]
        self.assertGreater(pool.sum(), early.sum()*5)
        radii = [self.mean_radius(frame) for frame in (42, 52, 62, 72)]
        self.assertTrue(all(a > b+15 for a, b in zip(radii, radii[1:])), radii)
        core = self.pixels(78)
        self.assertLess(radii[-1], 30)
        self.assertGreater(core[self.radius < 6, :3].mean(), 220)
        self.assertGreater(core[self.radius < 6, 3].mean(), 200)
        self.assertLess(core[self.radius > 80, 3].sum(), core[..., 3].sum()*.01)

    def test_burst_expands_from_caster_and_dissolves(self):
        self.assertFalse(self.effect.loop)
        self.assertEqual((self.effect.fps, self.effect.frames), (30, 150))
        self.assertEqual(self.effect.cue_frame, 81)
        radii = [self.mean_radius(frame) for frame in (81, 94, 108, 125)]
        self.assertTrue(all(b > a+25 for a, b in zip(radii, radii[1:])), radii)
        for frame in (42, 57, 81, 94, 108):
            alpha = self.pixels(frame)[..., 3].astype(float)
            self.assertLess(abs((alpha*self.x).sum()/alpha.sum()-320), 8)
            self.assertLess(abs((alpha*self.y).sum()/alpha.sum()-320), 8)
            self.assertFalse(alpha[[0, -1], :].any())
            self.assertFalse(alpha[:, [0, -1]].any())
        self.assertLess(self.pixels(147)[..., 3].sum(), self.pixels(108)[..., 3].sum()*.01)
        for frame in (-1, 0, 149, 150, 300):
            self.assertFalse(self.pixels(frame)[..., 3].any())

    def test_all_palettes_preserve_geometry_and_render_deterministically(self):
        self.assertEqual(self.effect.default_color, 'divine')
        master = self.pixels(self.effect.poster_frame, 'purple')
        for color in PALETTES:
            with self.subTest(color=color):
                image = self.pixels(self.effect.poster_frame, color)
                np.testing.assert_array_equal(image[..., 3], master[..., 3])
                self.assertTrue(((image[..., 3] > 0) & (image[..., 3] < 255)).any())
                if color != 'purple':
                    self.assertFalse(np.array_equal(image[..., :3], master[..., :3]))
        np.testing.assert_array_equal(self.pixels(57), self.pixels(57))


if __name__ == '__main__':
    unittest.main()
