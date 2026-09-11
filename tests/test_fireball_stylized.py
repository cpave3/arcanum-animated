import hashlib
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from animation_fx.catalog import EFFECTS
from animation_fx.effects import fireball, fireball_stylized
from animation_fx.palettes import PALETTES
from animation_fx.primitives import stylized_flames


class StylizedFireballTests(unittest.TestCase):
    def test_shared_bolt_and_ground_are_unchanged(self):
        snapshots = {
            8: 'aa3c8a1535a45b2ad6b545c833e03f432530e3719ba853bba365b656826a317f',
            119: 'c5ac44a3ae6654ae1bf23c8db136162c562d8f7bbccf62eee40f36e02def9372',
            150: 'ac90b2edfeaa2b2a345638255c5f8121f0c7c4fa4578620f7454c12fd82251c8',
        }
        for frame, digest in snapshots.items():
            self.assertEqual(hashlib.sha256(EFFECTS['fireball'].master(frame).tobytes()).hexdigest(), digest)

    def test_stylized_artwork_is_unchanged_by_realistic_gas_revision(self):
        snapshots = {
            8: '6e757bf017dbff7bd903534514e3f6664cf567e0fd6136b7feb61fd4c2c60ce7',
            26: '8400a9309e857a9042583b85813fabd45dc4cc51ced3d58c794dbfd3d814d781',
            34: '19b53385fdc54062381f107cef0f274478a04ca0e48b5e16654173122ea81590',
        }
        for frame, digest in snapshots.items():
            self.assertEqual(hashlib.sha256(EFFECTS['fireball-stylized'].master(frame).tobytes()).hexdigest(), digest)

    def test_variant_reuses_timeline_ground_and_independent_flame_components(self):
        effect = EFFECTS['fireball-stylized']
        self.assertEqual((effect.frames, effect.cue_frame), (209, 14))
        for frame, component in ((8, 'projectile'), (26, 'explosion')):
            with patch.object(fireball_stylized, component, wraps=getattr(fireball_stylized, component)) as spy:
                complete = np.asarray(effect.render(frame, 'fire'))
            spy.assert_called_once()
            with patch.object(fireball_stylized, component, return_value=Image.new('RGBA', (640, 640))):
                removed = np.asarray(effect.render(frame, 'fire'))
            self.assertFalse(np.array_equal(complete, removed))
            self.assertFalse(np.array_equal(complete, np.asarray(EFFECTS['fireball'].render(frame, 'fire'))))
        for frame in (119, 140, 180, 208):
            np.testing.assert_array_equal(np.asarray(effect.render(frame, 'fire')),
                                          np.asarray(EFFECTS['fireball'].render(frame, 'fire')))
        with patch.object(fireball, 'ground', return_value=Image.new('RGBA', (640, 640))):
            self.assertFalse(np.asarray(effect.render(119, 'fire'))[..., 3].any())

    def test_style_moves_expands_and_uses_the_same_painter_for_bolt_and_blast(self):
        effect = EFFECTS['fireball-stylized']
        samples = []
        for frame in (5, 12, 26, 40):
            with patch.object(stylized_flames, 'flame_mass', wraps=stylized_flames.flame_mass) as spy:
                image = np.asarray(effect.render(frame, 'fire'))
            self.assertTrue(spy.called)
            samples.append(image)
        for a, b in zip(samples, samples[1:]):
            self.assertFalse(np.array_equal(a, b))
        def center(image):
            ys, xs = np.where(image[..., 3] > 128)
            return (xs.min()+xs.max())/2, np.ptp(xs), np.ptp(ys)
        self.assertGreater(center(samples[1])[0], center(samples[0])[0]+70)
        _, width, height = center(samples[2])
        yy, xx = np.indices(samples[2].shape[:2])
        alpha = samples[2][..., 3].astype(float)
        self.assertLess(abs((xx*alpha).sum()/alpha.sum()-320), 25)
        self.assertLess(abs((yy*alpha).sum()/alpha.sum()-320), 25)
        self.assertGreater(min(width, height), 300)
        self.assertLess(abs(width-height), 75)

    def test_all_palettes_and_transparent_endpoints(self):
        effect = EFFECTS['fireball-stylized']
        master = np.asarray(effect.master(effect.poster_frame))
        for color in PALETTES:
            image = np.asarray(effect.render(effect.poster_frame, color))
            np.testing.assert_array_equal(image[..., 3], master[..., 3])
            self.assertFalse(image[0, :, 3].any())
            self.assertFalse(image[:, 0, 3].any())
        for frame in (0, 208, 220):
            self.assertFalse(np.asarray(effect.render(frame, 'fire'))[..., 3].any())


if __name__ == '__main__':
    unittest.main()
