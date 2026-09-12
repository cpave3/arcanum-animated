import math
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from animation_fx.catalog import EFFECTS
from animation_fx.effects import rift_edge_anchor
from animation_fx.palettes import PALETTES
from animation_fx.primitives import lightning, orbs, particles, rift, runes
from animation_fx.profiles import PROFILES

ROOT = Path(__file__).resolve().parents[1]


class RiftEdgeAnchorTests(unittest.TestCase):
    side = 'left'

    @property
    def effect(self):
        return EFFECTS[f'rift-edge-anchor-{self.side}']

    def canonical(self, point):
        x, y = point
        return (320-x if self.side == 'right' else x, y)

    def pixels(self, frame=23, color='gold'):
        return np.asarray(self.effect.render(frame, color))

    def test_public_render_registration_and_all_palette_alpha(self):
        self.assertEqual((self.effect.size, self.effect.fps, self.effect.frames), (320, 30, 90))
        self.assertEqual((self.effect.role, self.effect.loop, self.effect.source_color,
                          self.effect.default_color), ('anchor', True, 'gold', 'radiant'))
        self.assertEqual(self.effect.anchor_side, self.side)
        self.assertNotIn('rift-edge-anchor', EFFECTS)
        self.assertEqual(PROFILES['vtt'].size_for(self.effect.size), 256)
        source = self.pixels()
        self.assertEqual(self.effect.render(23, 'gold').mode, 'RGBA')
        self.assertEqual(source.shape, (320, 320, 4))
        self.assertEqual(len(PALETTES), 17)
        variants = []
        for color in PALETTES:
            with self.subTest(color=color):
                pixels = self.pixels(color=color)
                np.testing.assert_array_equal(pixels[..., 3], source[..., 3])
                self.assertGreater(pixels[..., 3].max(), 240)
                self.assertTrue(np.any((pixels[..., 3] > 0) & (pixels[..., 3] < 255)))
                variants.append(pixels.tobytes())
        self.assertGreater(len(set(variants)), 10)

    def test_bounded_artwork_animation_and_periodic_seam(self):
        samples = {frame: self.pixels(frame) for frame in (0, 1, 23, 45, 88, 89)}
        for frame, pixels in samples.items():
            with self.subTest(frame=frame):
                alpha = pixels[..., 3]
                self.assertFalse(np.any(alpha[[0, -1], :]))
                self.assertFalse(np.any(alpha[:, [0, -1]]))
                ys, xs = np.where(alpha > 10)
                self.assertGreater(xs.min(), 60)
                self.assertLess(xs.max(), 260)
                self.assertGreater(ys.min(), 40)
                self.assertLess(ys.max(), 285)
                self.assertLess(np.mean(alpha > 10), .2)
        delta = lambda a, b: np.abs(samples[a].astype(float)-samples[b]).mean()
        seam = delta(89, 0)
        self.assertGreater(seam, .1)
        self.assertLess(seam, 1.5*max(delta(0, 1), delta(88, 89)))
        self.assertGreater(max(delta(0, 23), delta(0, 45)), 2*seam)
        for frame in (0, 23, 89):
            np.testing.assert_array_equal(self.pixels(frame+90), samples[frame])
        np.testing.assert_array_equal(self.pixels(-1), samples[89])

    def test_three_distinct_glyphs_one_brace_and_three_powered_groups(self):
        with patch.object(runes, 'draw_rune', wraps=runes.draw_rune) as glyphs, \
                patch.object(runes, 'draw_brackets', wraps=runes.draw_brackets) as brackets, \
                patch.object(orbs, 'orb_layer', wraps=orbs.orb_layer) as nodes, \
                patch.object(lightning, 'draw_tether', wraps=lightning.draw_tether) as tethers:
            complete = self.pixels()
        expected = ('spire', 'eye', 'branch') if self.side == 'left' else ('gate', 'hourglass', 'fork')
        self.assertEqual(tuple(call.args[1] for call in glyphs.call_args_list), expected)
        self.assertTrue(all(0 < call.kwargs['size'] <= 1.5 for call in glyphs.call_args_list))
        brackets.assert_called_once()
        self.assertEqual(brackets.call_args.kwargs['sides'], (-1,))
        charged = [call for call in nodes.call_args_list if call.args[2] > 5]
        self.assertEqual(len(charged), 3)
        self.assertEqual(nodes.call_count, 6)  # Three stationary orbs and three small rim contacts.
        self.assertEqual(tethers.call_count, 3)
        for index, contact in enumerate(rift_edge_anchor.contacts(23, self.side)):
            endpoint = self.canonical(contact)
            np.testing.assert_allclose(tethers.call_args_list[index].args[2], endpoint)
            powered = tethers.call_args_list[index].args[1]
            self.assertTrue(any(np.allclose(call.args[1], powered) for call in charged))
        np.testing.assert_array_equal(complete, self.pixels())

    def test_middle_joint_has_stationary_power_orb_and_small_moving_contact(self):
        for frame in range(90):
            with self.subTest(frame=frame), \
                    patch.object(orbs, 'orb_layer', wraps=orbs.orb_layer) as spy:
                image = self.pixels(frame)
                middle = [call for call in spy.call_args_list if call.args[1][1] == 160]
                self.assertEqual(len(middle), 2)
                small = next(call for call in middle if call.args[2] < 3)
                large = next(call for call in middle if call.args[2] > 5)
                np.testing.assert_array_equal(large.args[1], (180, 160))
                contact = rift_edge_anchor.contacts(frame, self.side)[1]
                np.testing.assert_allclose(small.args[1], self.canonical(contact))
                x, y = (round(value) for value in contact)
                # Sample the native pixel, not a broad average hiding a missed contact.
                self.assertGreater(image[y, x, 3], 240)
                self.assertGreater(image[y, x, 0], 240)
                self.assertGreater(image[y, x, 1], 200)
                mirrored = image[:, ::-1]
                self.assertEqual(mirrored[y, 319-x, 3], image[y, x, 3])
                self.assertLessEqual(abs((319-x)-round(320-contact[0])), 1)

    def test_native_render_is_side_specific_not_a_mirrored_copy(self):
        other = 'right' if self.side == 'left' else 'left'
        with self.assertRaises(TypeError):
            rift_edge_anchor.render(23)
        with self.assertRaises(TypeError):
            rift_edge_anchor.render(23, self.side)
        for frame in (0, 23, 45, 89):
            actual = self.pixels(frame)
            np.testing.assert_array_equal(actual, np.asarray(rift_edge_anchor.render(frame, side=self.side)))
            opposite = np.asarray(EFFECTS[f'rift-edge-anchor-{other}'].render(frame, 'gold'))
            self.assertGreater(np.abs(actual.astype(float)-opposite[:, ::-1]).sum(), 1000)

    def test_shared_painters_make_visible_contributions(self):
        for module, name in ((runes, 'draw_rune'), (runes, 'draw_brackets'),
                             (lightning, 'draw_tether'), (particles, 'draw_spark'),
                             (orbs, 'orb_layer')):
            with self.subTest(painter=name):
                with patch.object(module, name, wraps=getattr(module, name)) as spy:
                    complete = self.pixels()
                self.assertTrue(spy.called)
                replacement = Image.new('RGBA', (640, 640)) if name == 'orb_layer' else None
                with patch.object(module, name, return_value=replacement):
                    removed = self.pixels()
                self.assertGreater(np.abs(complete.astype(float)-removed).sum(), 1000)
                self.assertGreater(np.abs(complete[..., 3].astype(float)-removed[..., 3]).sum(), 100)

    def test_native_contacts_forward_map_to_actual_bank_through_full_cycle(self):
        for frame in range(90):
            contour = rift.compact_contour(math.tau*frame/90)
            contacts = rift_edge_anchor.contacts(frame, self.side)
            self.assertEqual(len(contacts), 3)
            for (x, y), target_y in zip(contacts, (270, 320, 370)):
                with self.subTest(frame=frame, y=target_y):
                    world_x = (264 if self.side == 'left' else 376)+(x-160)*.64
                    self.assertAlmostEqual(320+(y-160)*.64, target_y)
                    crossings = []
                    for a, b in zip(contour, contour[1:]+contour[:1]):
                        if min(a[1], b[1]) <= target_y < max(a[1], b[1]):
                            crossings.append(a[0]+(b[0]-a[0])*(target_y-a[1])/(b[1]-a[1]))
                    self.assertEqual(len(crossings), 2)
                    expected = min(crossings) if self.side == 'left' else max(crossings)
                    self.assertAlmostEqual(world_x, expected)

    def test_contour_changes_move_rendered_contacts(self):
        original = rift.compact_contour
        before = self.pixels()
        contacts = rift_edge_anchor.contacts(23, self.side)

        def widen(phase):
            contour = original(phase)
            return [(x+(-4 if index < len(contour)//2 else 6), y)
                    for index, (x, y) in enumerate(contour)]

        with patch.object(rift, 'compact_contour', side_effect=widen), \
                patch.object(lightning, 'draw_tether', wraps=lightning.draw_tether) as tethers:
            after = self.pixels()
            moved = rift_edge_anchor.contacts(23, self.side)
        shift = (-4 if self.side == 'left' else 6)/.64
        for index, (old_x, old_y) in enumerate(contacts):
            expected = (old_x+shift, old_y)
            np.testing.assert_allclose(moved[index], expected)
            np.testing.assert_allclose(tethers.call_args_list[index].args[2], self.canonical(expected))
            x, y = round(old_x), round(old_y)
            region = np.s_[y-10:y+11, x-15:x+16, 3]
            self.assertGreater(np.abs(before[region].astype(float)-after[region]).sum(), 100)

    def test_original_orb_runes_and_vortex_snapshots_unchanged(self):
        for name, filename in (('orb-anchor', 'golden-anchor.png'),
                               ('rune-anchor', 'golden-rune-anchor.png'),
                               ('vortex', 'purple-rift-outward.png')):
            with self.subTest(effect=name), Image.open(ROOT / filename) as snapshot:
                effect = EFFECTS[name]
                np.testing.assert_array_equal(np.asarray(effect.render(0, effect.source_color)),
                                              np.asarray(snapshot))


class RightRiftEdgeAnchorTests(RiftEdgeAnchorTests):
    side = 'right'


if __name__ == '__main__':
    unittest.main()
