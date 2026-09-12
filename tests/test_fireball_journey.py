import hashlib
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from animation_fx.catalog import EFFECTS
from animation_fx.effects import fireball
from animation_fx.palettes import PALETTES


class FireballJourneyTests(unittest.TestCase):
    def test_projectile_head_stays_centered_with_a_left_tail(self):
        effect = EFFECTS['fireball-projectile']
        self.assertEqual((effect.frames, effect.fps, effect.loop), (60, 30, True))
        centers = []
        for frame in (0, 7, 15, 30, 45, 59):
            with self.subTest(frame=frame):
                pixels = np.asarray(effect.render(frame, 'fire'))
                ys, xs = np.where(pixels[..., 3] > 240)
                center = ((xs.min()+xs.max())/2, (ys.min()+ys.max())/2)
                centers.append(center)
                np.testing.assert_allclose(center, (320, 320), atol=2)
                self.assertLess(abs(np.ptp(xs)/np.ptp(ys)-1), .15)
                self.assertGreater(pixels[:, :260, 3].sum(), 100000)
                self.assertEqual(pixels[:, 380:, 3].max(), 0)
        self.assertLessEqual(np.ptp(centers, axis=0).max(), 1)

    def test_projectile_animates_with_smooth_seam_wrap_and_palette_alpha(self):
        effect = EFFECTS['fireball-projectile']
        reference = [np.asarray(effect.render(f, 'purple'))[..., 3] for f in (0, 1, 59)]
        for color in PALETTES:
            with self.subTest(color=color):
                samples = [np.asarray(effect.render(f, color)) for f in (0, 1, 59)]
                for pixels, alpha in zip(samples, reference):
                    self.assertEqual(pixels.shape, (640, 640, 4))
                    np.testing.assert_array_equal(pixels[..., 3], alpha)
                    self.assertGreater(alpha.max(), 240)
                    self.assertTrue(((alpha > 0) & (alpha < 255)).any())
                    self.assertFalse(alpha[[0, -1], :].any())
                    self.assertFalse(alpha[:, [0, -1]].any())
                first, following, last = [pixels.astype(float) for pixels in samples]
                step = np.abs(following-first).mean()
                self.assertGreater(step, 0)
                self.assertLess(np.abs(last-first).mean(), 2*step)
                for frame, expected in ((60, samples[0]), (121, samples[1]), (-1, samples[2])):
                    np.testing.assert_array_equal(np.asarray(effect.render(frame, color)), expected)

    def test_detonation_never_draws_a_projectile_and_matches_original_impact(self):
        effect = EFFECTS['fireball-detonation']
        self.assertEqual((effect.frames, effect.fps, effect.loop, effect.cue_frame),
                         (107, 30, False, 1))
        with patch.object(fireball, 'projectile', side_effect=AssertionError('baked flight')), \
                patch.object(fireball, 'projectile_material', side_effect=AssertionError('orb')):
            for frame in range(effect.frames):
                with self.subTest(frame=frame):
                    pixels = np.asarray(effect.render(frame, 'fire'))
                    if frame == 0:
                        self.assertFalse(pixels[..., 3].any())
                    else:
                        np.testing.assert_array_equal(
                            pixels, np.asarray(EFFECTS['fireball-opening'].render(frame+13, 'fire')))

    def test_detonation_palette_alpha_clamping_and_exact_ground_handoffs(self):
        effect = EFFECTS['fireball-detonation']
        reference = {f: np.asarray(effect.render(f, 'purple'))[..., 3] for f in (1, 21, 106)}
        for color in PALETTES:
            with self.subTest(color=color):
                self.assertFalse(np.asarray(effect.render(0, color))[..., 3].any())
                for frame, alpha in reference.items():
                    pixels = np.asarray(effect.render(frame, color))
                    np.testing.assert_array_equal(pixels[..., 3], alpha)
                    self.assertGreater(alpha.max(), 0)
                    np.testing.assert_array_equal(
                        pixels, np.asarray(EFFECTS['fireball-opening'].render(frame+13, color)))
                final = np.asarray(effect.render(106, color))
                for name in ('fireball-embers', 'fireball-closing'):
                    np.testing.assert_array_equal(final, np.asarray(EFFECTS[name].render(0, color)))
                for frame, endpoint in ((-10, 0), (107, 106), (1000, 106)):
                    np.testing.assert_array_equal(np.asarray(effect.render(frame, color)),
                                                  np.asarray(effect.render(endpoint, color)))

    def test_shared_material_visibly_changes_moving_and_centered_orbs(self):
        for name, frame in (('fireball', 8), ('fireball-opening', 8), ('fireball-projectile', 8)):
            with self.subTest(effect=name):
                with patch.object(fireball, 'projectile_material', wraps=fireball.projectile_material) as spy:
                    complete = np.asarray(EFFECTS[name].render(frame, 'fire'))
                spy.assert_called_once()
                self.assertGreater(complete[..., 3].sum(), 0)
                with patch.object(fireball, 'projectile_material', return_value=Image.new('RGBA', (640, 640))):
                    removed = np.asarray(EFFECTS[name].render(frame, 'fire'))
                self.assertFalse(removed[..., 3].any())
                self.assertFalse(np.array_equal(complete, removed))

    def test_original_bolt_snapshot_is_unchanged(self):
        pixels = EFFECTS['fireball'].render(8, 'purple').tobytes()
        self.assertEqual(hashlib.sha256(pixels).hexdigest(),
                         'aa3c8a1535a45b2ad6b545c833e03f432530e3719ba853bba365b656826a317f')


if __name__ == '__main__':
    unittest.main()
