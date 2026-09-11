import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from animation_fx.catalog import EFFECTS
from animation_fx.effects import turn_undead
from animation_fx.palettes import PALETTES
from animation_fx.primitives import combustion, geometry, particles, runes
from animation_fx.primitives.canvas import Canvas


class TurnUndeadTests(unittest.TestCase):
    def setUp(self):
        self.effect = EFFECTS['turn-undead']
        self.y, self.x = np.mgrid[:640, :640]
        self.radius = np.hypot(self.x-320, self.y-320)

    def pixels(self, frame, color='divine'):
        return np.asarray(self.effect.render(frame, color))

    def test_public_render_endpoints_palette_alpha_and_metadata(self):
        self.assertEqual((self.effect.size, self.effect.fps, self.effect.frames), (640, 30, 90))
        self.assertFalse(self.effect.loop)
        self.assertEqual(self.effect.source_color, 'purple')
        self.assertEqual(self.effect.default_color, 'divine')
        master = self.pixels(self.effect.poster_frame, 'purple')
        for color in PALETTES:
            with self.subTest(color=color):
                for frame in (-1, 0, 89, 100):
                    self.assertFalse(self.pixels(frame, color)[..., 3].any())
                pixels = self.pixels(self.effect.poster_frame, color)
                np.testing.assert_array_equal(pixels[..., 3], master[..., 3])
                self.assertTrue(np.any((pixels[..., 3] > 0) & (pixels[..., 3] < 255)))
                self.assertFalse(pixels[[0, -1], :, 3].any())
                self.assertFalse(pixels[:, [0, -1], 3].any())
                if color != 'purple':
                    self.assertFalse(np.array_equal(pixels[..., :3], master[..., :3]))
        np.testing.assert_array_equal(self.pixels(48), self.pixels(48))

    def test_cue_is_a_central_flash_and_poster_has_a_broad_blast(self):
        gathering = self.pixels(6)[..., 3]
        cue = self.pixels(self.effect.cue_frame)
        center = self.radius < 25
        self.assertGreater(cue[center, 3].mean(), gathering[center].mean()*2)
        self.assertGreater(cue[center, :3].mean(), 210)
        poster = self.pixels(self.effect.poster_frame)[..., 3]
        self.assertGreater(poster[self.radius > 130].sum(), poster.sum()*.6)
        self.assertGreater(poster.sum(), 5_000_000)
        self.assertLess(self.pixels(85)[..., 3].sum(), poster.sum()*.01)

    def test_motion_expands_radially_without_a_projectile_or_residue(self):
        radii = []
        for frame in (30, 39, 48, 58, 70):
            alpha = self.pixels(frame)[..., 3].astype(float)
            mass = alpha.sum()
            self.assertLess(abs((alpha*self.x).sum()/mass-320), 4)
            self.assertLess(abs((alpha*self.y).sum()/mass-320), 4)
            radii.append((alpha*self.radius).sum()/mass)
        self.assertTrue(all(b > a+10 for a, b in zip(radii, radii[1:])), radii)
        self.assertGreater(radii[-1]-radii[0], 120)

    def test_runes_form_quickly_orbit_then_launch_intact_and_fade(self):
        samples = {}
        images = {}
        original = runes.draw_rune
        for frame in (1, 3, 5, 12, 22, 23, 24, 30, 44, 60):
            with patch.object(runes, 'draw_rune', wraps=original) as spy:
                images[frame] = self.pixels(frame)
                samples[frame] = [call.kwargs for call in spy.call_args_list]
            self.assertGreater(images[frame][..., 3].sum(), 0)
            self.assertEqual(len(samples[frame]), len(runes.GLYPHS))
            self.assertTrue(all(call['fragmentation'] == 0 for call in samples[frame]))
        radius = lambda call: np.linalg.norm(np.asarray(call['center'])-256)
        self.assertGreater(radius(samples[3][0]), radius(samples[5][0]))
        for frame in (5, 12, 23):
            self.assertAlmostEqual(radius(samples[frame][0]), 55)
            self.assertEqual(samples[frame][0]['opacity'], 1)
        self.assertGreater(radius(samples[1][0]), radius(samples[3][0]))
        self.assertGreater(samples[5][0]['rotation']-samples[1][0]['rotation'], .8)
        self.assertGreater(samples[23][0]['rotation']-samples[5][0]['rotation'], 2*np.pi)
        self.assertGreater(samples[23][0]['rotation']-samples[22][0]['rotation'], .5)
        self.assertGreater(samples[24][0]['rotation']-samples[23][0]['rotation'], .5)
        self.assertFalse(np.array_equal(images[5], images[23]))
        for before, after in ((24, 30), (30, 44), (44, 60)):
            for a, b in zip(samples[before], samples[after]):
                self.assertGreater(radius(b), radius(a)+20)
                self.assertAlmostEqual(a['rotation'], b['rotation'])
                self.assertLess(b['opacity'], a['opacity'])
            self.assertFalse(np.array_equal(images[before], images[after]))

    def test_echoes_are_independently_timed_visible_layers(self):
        original = turn_undead.radiant_echo
        with patch.object(turn_undead, 'radiant_echo', wraps=original) as spy:
            complete = self.pixels(48)
        self.assertEqual(spy.call_count, 3)
        starts = [call.args[1] for call in spy.call_args_list]
        self.assertEqual(len(set(starts)), 3)
        peaks = []
        for start in starts:
            def omit(frame, onset, *args):
                if onset == start:
                    return Image.new('RGBA', (640, 640))
                return original(frame, onset, *args)
            with patch.object(turn_undead, 'radiant_echo', side_effect=omit):
                removed = self.pixels(48)
                before = self.pixels(start)
            np.testing.assert_array_equal(before, self.pixels(start))
            difference = complete[..., 3].astype(float)-removed[..., 3]
            self.assertGreater(difference.sum(), 100_000)
            bins = self.radius.astype(int)
            profile = np.bincount(bins.ravel(), weights=difference.ravel())
            peaks.append(int(profile.argmax()))
        self.assertGreater(peaks[0]-peaks[1], 25)
        self.assertGreater(peaks[1]-peaks[2], 25)

    def test_shared_painters_and_field_have_observable_contributions(self):
        complete = self.pixels(48)
        cases = ((particles, 'draw_spark', None), (runes, 'draw_rune', None),
                 (Canvas, 'ring', None),
                 (combustion, 'energy_field', Image.new('RGBA', (640, 640))),
                 (combustion, 'turbulence', np.zeros((640, 640), dtype=np.float32)))
        for module, name, replacement in cases:
            with self.subTest(primitive=name):
                # Autospec preserves Canvas method binding while calling the real painter.
                original = getattr(module, name)
                with patch.object(module, name, autospec=True, side_effect=original) as spy:
                    rendered = self.pixels(48 if name != 'ring' else 8)
                    self.assertTrue(spy.called)
                with patch.object(module, name, return_value=replacement):
                    removed = self.pixels(48 if name != 'ring' else 8)
                self.assertGreater(np.abs(rendered.astype(float)-removed).sum(), 1000)
        with patch.object(geometry, 'compose', wraps=geometry.compose) as spy:
            np.testing.assert_array_equal(self.pixels(48), complete)
            spy.assert_called_once()
            self.assertEqual(len(spy.call_args.args), 4)


if __name__ == '__main__':
    unittest.main()
