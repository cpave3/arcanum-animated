import json
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from animation_fx.catalog import EFFECTS
from animation_fx.export import export_effect
from animation_fx.palettes import PALETTES
from animation_fx.primitives import particles
from animation_fx.primitives.canvas import Canvas
from animation_fx.recipe import FrameRecipe


STATUSES = {'electric': 'lightning', 'poison': 'poison', 'frost': 'cold', 'necrotic': 'necrotic', 'charmed': 'psychic', 'acid': 'acid'}


class TokenStatusTests(unittest.TestCase):
    def test_public_render_is_animated_periodic_padded_and_translucent(self):
        signatures = []
        for slug, color in STATUSES.items():
            with self.subTest(effect=slug):
                effect = EFFECTS[f'token-{slug}']
                self.assertEqual(effect.default_color, color)
                self.assertTrue(effect.loop)
                samples = [np.asarray(effect.render(frame, color)) for frame in (0, 1, 30, 88, 89, 90)]
                np.testing.assert_array_equal(samples[0], samples[-1])
                self.assertFalse(np.array_equal(samples[0], samples[2]))
                difference = lambda a, b: np.abs(a.astype(float)-b).mean()
                seam = difference(samples[4], samples[0])
                neighbors = max(difference(samples[0], samples[1]), difference(samples[3], samples[4]))
                self.assertLess(seam, neighbors*3)
                for sample in samples:
                    alpha = sample[..., 3]
                    self.assertGreater(alpha.sum(), 100_000)
                    self.assertLess((alpha > 30).mean(), .30)
                    self.assertFalse(alpha[[0, -1], :].any())
                    self.assertFalse(alpha[:, [0, -1]].any())
                    self.assertTrue(((alpha > 0) & (alpha < 255)).any())
                signatures.append(samples[0][..., 3])
        for index, alpha in enumerate(signatures):
            for other in signatures[index+1:]:
                self.assertFalse(np.array_equal(alpha, other))

    def test_all_palettes_keep_the_same_shapes(self):
        for slug in STATUSES:
            effect = EFFECTS[f'token-{slug}']
            master = np.asarray(effect.render(23, 'purple'))
            for color in PALETTES:
                with self.subTest(effect=slug, color=color):
                    image = np.asarray(effect.render(23, color))
                    np.testing.assert_array_equal(image[..., 3], master[..., 3])
                    if color != 'purple':
                        self.assertFalse(np.array_equal(image[..., :3], master[..., :3]))

    def test_acid_has_clinging_corrosion_and_surface_bubbles_not_rising_poison_orbs(self):
        effect = EFFECTS['token-acid']
        def sample(frame):
            with patch.object(Canvas, 'ring', autospec=True, side_effect=Canvas.ring) as spy:
                image = np.asarray(effect.render(frame, 'acid'))
            return image, {call.kwargs['center']: call.args[1] for call in spy.call_args_list}
        image, first = sample(0)
        _, later = sample(1)
        shared = set(first) & set(later)
        self.assertGreater(len(shared), 5)
        self.assertTrue(all(later[center] > first[center] for center in shared))
        self.assertGreater(image[..., 3].sum(), 2_000_000)
        with patch('animation_fx.effects.token_status.acid_surface', return_value=Image.new('RGBA', (640, 640))):
            without = np.asarray(effect.render(0, 'acid'))
        self.assertGreater(image[..., 3].astype(float).sum()-without[..., 3].sum(), 1_500_000)

    def test_necrotic_has_ghostly_volume_and_inward_motes_with_outward_trails(self):
        effect = EFFECTS['token-necrotic']
        def sample(frame):
            with patch.object(particles, 'draw_spark', wraps=particles.draw_spark) as spy:
                pixels = np.asarray(effect.render(frame, 'necrotic'))
            self.assertGreater(pixels[..., 3].sum(), 3_000_000)
            self.assertLess(pixels[310:330, 310:330, 3].max(), 5)
            self.assertGreater(len(spy.call_args_list), 20)
            self.assertLess(len(spy.call_args_list), 100)
            return spy.call_args_list
        first, later = sample(0), sample(1)
        radius = lambda point: np.linalg.norm(np.asarray(point)-320)
        inward = 0
        for a, b in zip(first, later):
            self.assertLess(radius(a.args[1]), radius(a.args[2]))
            if radius(b.args[1]) < radius(a.args[1]):
                inward += 1
        self.assertGreater(inward, len(first)*.9)

    def test_frost_coats_edges_with_textured_translucent_ice_not_the_token_face(self):
        effect = EFFECTS['token-frost']
        y, x = np.mgrid[:640, :640]
        radius = np.hypot(x-320, y-320)/1.25
        rim = (radius > 145) & (radius < 175)
        image = np.asarray(effect.render(23, 'cold'))
        alpha = image[..., 3]
        self.assertGreater(alpha[rim].mean(), 55)
        self.assertLess(alpha[rim].mean(), 170)
        self.assertGreater(alpha[rim].std(), 12)
        self.assertLess(alpha[radius < 75].mean(), 4)
        self.assertFalse(alpha[radius > 210].any())
        with patch('animation_fx.effects.token_status.frost_surface', return_value=Image.new('RGBA', (640, 640))):
            without = np.asarray(effect.render(23, 'cold'))[..., 3]
        self.assertGreater((alpha.astype(float)-without)[rim].mean(), 40)

    def test_frost_shard_roots_dissolve_into_coating_while_tips_remain_visible(self):
        effect = EFFECTS['token-frost']
        y, x = np.mgrid[:640, :640]
        radius = np.hypot(x-320, y-320)/1.25
        tips = (radius > 90) & (radius < 125)
        roots = (radius > 145) & (radius < 158)
        for frame in (0, 23, 60):
            complete = np.asarray(effect.render(frame, 'cold'))[..., 3].astype(float)
            with patch('animation_fx.effects.token_status.frost_shards', return_value=Image.new('RGBA', (640, 640))):
                without = np.asarray(effect.render(frame, 'cold'))[..., 3]
            contribution = complete-without
            self.assertGreater(contribution[tips].mean(), 5)
            self.assertLess(contribution[roots].mean(), contribution[tips].mean()/3)
            self.assertFalse(contribution[radius > 158].any())

    def test_charmed_strand_is_continuous_coiled_and_rotates_with_depth_shading(self):
        effect = EFFECTS['token-charmed']
        def strands(frame):
            with patch.object(Canvas, 'line', autospec=True, side_effect=Canvas.line) as spy:
                self.assertGreater(np.asarray(effect.render(frame, 'psychic'))[..., 3].sum(), 100_000)
            return [call for call in spy.call_args_list if call.kwargs.get('width') == 6]
        first, opposite = strands(0), strands(45)
        points = np.asarray([call.args[1][0] for call in first])
        self.assertGreater(np.ptp(points[:, 0]), 270)
        self.assertGreater(np.ptp(points[:, 1]), 240)
        self.assertGreaterEqual(np.count_nonzero(np.diff(np.sign(np.diff(points[:, 0])))), 3)
        for a, b in zip(first, first[1:]):
            np.testing.assert_allclose(a.args[1][1], b.args[1][0])
        for a, b in zip(first, opposite):
            self.assertAlmostEqual(a.args[1][0][0]+b.args[1][0][0], 512)
        self.assertGreater(max(abs(a.args[2]-b.args[2]) for a, b in zip(first, opposite)), .2)

    def test_electric_aura_uses_short_zaps_that_disappear_not_cross_body_arcs(self):
        effect = EFFECTS['token-electric']
        def zaps(frame):
            with patch.object(Canvas, 'line', autospec=True, side_effect=Canvas.line) as spy:
                image = np.asarray(effect.render(frame, 'lightning'))
            self.assertLess(image[260:380, 260:380, 3].mean(), 1)
            strokes = [call.args[1] for call in spy.call_args_list if call.kwargs.get('width') == 3]
            self.assertGreater(len(strokes), 2)
            for points in strokes:
                self.assertLess(np.linalg.norm(np.asarray(points[-1])-points[0]), 50)
            return {tuple(round(value, 3) for point in (points[0], points[-1]) for value in point)
                    for points in strokes}
        self.assertFalse(zaps(0) & zaps(10))

    def test_poison_bubbles_move_up_and_expand_before_popping(self):
        effect = EFFECTS['token-poison']
        def bubbles(frame):
            with patch.object(Canvas, 'ring', autospec=True, side_effect=Canvas.ring) as spy:
                self.assertGreater(np.asarray(effect.render(frame, 'poison'))[..., 3].sum(), 0)
            return [call for call in spy.call_args_list if 'arc' not in call.kwargs]
        first, second = bubbles(0), bubbles(1)
        paired = []
        for a in first:
            ax, ay = a.kwargs['center']
            candidates = [b for b in second if abs(b.kwargs['center'][0]-ax) < 2
                          and 0 < ay-b.kwargs['center'][1] < 6]
            if candidates:
                b = min(candidates, key=lambda c: abs(c.kwargs['center'][0]-ax))
                paired.append((a.args[1], b.args[1]))
        self.assertGreaterEqual(len(paired), 8)
        self.assertGreater(sum(b >= a for a, b in paired), len(paired)*.7)

    def test_exporter_keeps_native_resolution_for_each_status(self):
        for slug, color in STATUSES.items():
            with self.subTest(effect=slug), tempfile.TemporaryDirectory() as directory:
                effect = EFFECTS[f'token-{slug}']
                short = replace(effect, renderer=FrameRecipe(effect.master, SIZE=640, FPS=30, FRAMES=2))
                export_effect(short, [color], Path(directory))
                metadata = json.loads((Path(directory)/'effect.json').read_text())
                self.assertEqual(metadata['size'], 640)
                self.assertGreater((Path(directory)/f'{color}.webm').stat().st_size, 1000)
                with Image.open(Path(directory)/f'{color}.png') as poster:
                    self.assertEqual(poster.size, (640, 640))


if __name__ == '__main__':
    unittest.main()
