import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from animation_fx.catalog import EFFECTS
from animation_fx.effects import paired_rays
from animation_fx.export import export_effect
from animation_fx.palettes import PALETTES
from animation_fx.primitives import beams
from animation_fx.profiles import ExportProfile, PROFILES
from animation_fx.viewer_catalog import build_viewer_catalog


CASTERS = ('ray-cast-1', 'ray-cast-2', 'ray-cast-3')


class PairedRayTests(unittest.TestCase):
    def pixels(self, name, frame, color='purple'):
        return np.asarray(EFFECTS[name].render(frame, color))

    def test_public_render_has_transparent_endpoints_and_all_palette_posters(self):
        self.assertEqual(len(PALETTES), 17)
        for name, frames in zip((*CASTERS, 'ray-beam', 'ray-hit'), (36, 46, 56, 9, 40)):
            effect = EFFECTS[name]
            self.assertEqual((effect.size, effect.fps, effect.frames, effect.loop),
                             (640, 30, frames, False))
            self.assertEqual(PROFILES['vtt'].size_for(effect.size), 384)
            master = self.pixels(name, effect.poster_frame)
            self.assertTrue(master[..., 3].any())
            for color in PALETTES:
                with self.subTest(effect=name, color=color):
                    for frame in (-1, 0, frames-1, frames+5):
                        self.assertFalse(self.pixels(name, frame, color)[..., 3].any())
                    poster = self.pixels(name, effect.poster_frame, color)
                    np.testing.assert_array_equal(poster[..., 3], master[..., 3])
                    if color == 'eldritch':
                        visible = master[..., 3] > 100
                        self.assertFalse(np.array_equal(poster[visible, :3], master[visible, :3]))

    def test_caster_and_hit_render_without_edge_beams(self):
        for name in (*CASTERS, 'ray-hit'):
            for frame in range(EFFECTS[name].frames):
                with self.subTest(effect=name, frame=frame):
                    alpha = self.pixels(name, frame)[..., 3]
                    self.assertLessEqual(alpha[:, :80].max(), 2)
                    self.assertLessEqual(alpha[:, -80:].max(), 2)
            self.assertGreater(self.pixels(name, EFFECTS[name].cue_frame)[280:360, 280:360, 3].sum(), 1000)

    def test_beam_travels_only_left_to_right_and_spans_width_at_arrival(self):
        fronts = []
        for frame in (1, 2, 3, 4):
            alpha = self.pixels('ray-beam', frame)[..., 3]
            y, x = np.where(alpha > 100)
            fronts.append(x.max())
            self.assertLess(abs(y.mean()-320), 3)
            self.assertGreater(x.max()-x.min(), (y.max()-y.min())*2)
            self.assertFalse(alpha[:240].any())
            self.assertFalse(alpha[400:].any())
        self.assertTrue(all(b-a > 100 for a, b in zip(fronts, fronts[1:])), fronts)
        alpha = self.pixels('ray-beam', 4)[..., 3]
        self.assertTrue((alpha[320, 40:600] > 100).all())
        self.assertFalse(alpha[:, [0, -1]].any())
        self.assertLess(alpha[320, 8], alpha[320, 24])
        self.assertLess(alpha[320, -9], alpha[320, -25])

    def test_charge_reuses_inward_vortex_and_condenses_without_glyphs(self):
        from animation_fx.primitives import swirl, runes
        with patch.object(swirl, 'render_swirl', wraps=swirl.render_swirl) as painter, \
                patch.object(runes, 'draw_rune', wraps=runes.draw_rune) as glyphs:
            early = self.pixels('ray-cast-1', 3)
            later = self.pixels('ray-cast-1', 10)
        self.assertEqual([call.args[0] for call in painter.call_args_list], [-18, -60])
        glyphs.assert_not_called()
        with patch.object(swirl, 'render_swirl', return_value=Image.new('RGBA', (640, 640))):
            no_swirl = self.pixels('ray-cast-1', 3)
        self.assertFalse(np.array_equal(early, no_swirl))
        y, x = np.indices(early.shape[:2]); radius = np.hypot(x-320, y-320)
        self.assertGreater(early[radius > 70, 3].sum(), later[radius > 70, 3].sum()*2)
        self.assertGreater(later[radius < 12, 3].mean(), early[radius < 12, 3].mean())

    def test_caster_recipes_share_one_count_parameterized_renderer(self):
        for count, name in enumerate(CASTERS, 1):
            recipe = EFFECTS[name].renderer.render
            self.assertIs(recipe.func, paired_rays.caster)
            self.assertEqual(recipe.keywords, {'count': count})
            self.assertTrue(self.pixels(name, 16)[..., 3].any())

    def test_only_standalone_beam_uses_shared_beam_painter(self):
        for name in (*CASTERS, 'ray-hit', 'ray-beam'):
            with self.subTest(effect=name):
                with patch.object(beams, 'draw_beam', wraps=beams.draw_beam) as spy:
                    complete = self.pixels(name, EFFECTS[name].poster_frame)
                if name == 'ray-beam':
                    self.assertEqual(spy.call_args.args[2:4], ((0, 256), (512, 256)))
                    with patch.object(beams, 'draw_beam'):
                        removed = self.pixels(name, EFFECTS[name].poster_frame)
                    self.assertFalse(removed[..., 3].any())
                    self.assertGreater(complete[..., 3].sum(), 1000)
                else:
                    spy.assert_not_called()

    def test_casters_reuse_charge_painter_with_visible_contribution(self):
        for name in CASTERS:
            with patch.object(paired_rays, 'charge', wraps=paired_rays.charge) as spy:
                complete = self.pixels(name, 8)
            spy.assert_called_once()
            with patch.object(paired_rays, 'charge'):
                removed = self.pixels(name, 8)
            self.assertGreater(complete[..., 3].sum(), removed[..., 3].sum()+1000)

    def test_target_reuses_impact_painter_after_blank_frame_zero(self):
        for frame in (0, 1, 10):
            with patch.object(paired_rays, 'impact', wraps=paired_rays.impact) as spy:
                complete = self.pixels('ray-hit', frame)
            spy.assert_called_once_with(frame-1)
            with patch.object(paired_rays, 'impact', return_value=Image.new('RGBA', (640, 640))):
                removed = self.pixels('ray-hit', frame)
            if frame == 0:
                self.assertFalse(complete[..., 3].any())
            else:
                self.assertGreater(complete[280:360, 280:360, 3].sum(),
                                   removed[280:360, 280:360, 3].sum()+1000)

    def test_real_exports_preserve_local_cues_pairing_and_decodable_alpha(self):
        profile = ExportProfile('test', scale=1, max_size=96, crf=22, cpu_used=8)
        expected = {
            'ray-cast-1': {'effects': ['ray-beam', 'ray-hit'], 'event': 'Release',
                           'times': [12/30], 'direction': 'center'},
            'ray-hit': {'effects': ['ray-beam', *CASTERS], 'event': 'Impact',
                        'times': [1/30], 'direction': 'center'},
            'ray-beam': {'effects': [*CASTERS, 'ray-hit'], 'event': 'Arrival',
                         'times': [4/30], 'direction': 'right'},
        }
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            for name, pairing in expected.items():
                with self.subTest(effect=name):
                    effect = EFFECTS[name]
                    directory = output / name
                    export_effect(effect, ['eldritch'], directory, profile)
                    metadata = json.loads((directory / 'effect.json').read_text())
                    self.assertEqual(metadata['pairing'], pairing)
                    self.assertEqual(metadata['cue_time'], pairing['times'][0])
                    self.assertEqual(metadata['duration'], effect.frames/30)
                    self.assertEqual(metadata['frames'], effect.frames)
                    decoded = subprocess.run([
                        'ffmpeg', '-v', 'error', '-c:v', 'libvpx-vp9', '-i',
                        str(directory / 'eldritch.webm'), '-f', 'rawvideo',
                        '-pix_fmt', 'rgba', '-'], check=True, capture_output=True).stdout
                    frames = np.frombuffer(decoded, dtype=np.uint8).reshape(-1, 96, 96, 4)
                    self.assertEqual(len(frames), effect.frames)
                    self.assertFalse(frames[[0, -1], ..., 3].any())
                    self.assertGreater(frames[effect.poster_frame, ..., 3].sum(), 1000)
                    if name == 'ray-beam':
                        self.assertGreater(frames[4, 46:50, 6:90, 3].min(), 80)
                        self.assertLess(frames[1, :, 60:, 3].max(), 5)
                    else:
                        self.assertLess(frames[:, :, :8, 3].max(), 5)
                        self.assertLess(frames[:, :, -8:, 3].max(), 5)
                        self.assertGreater(frames[effect.cue_frame, 44:52, 44:52, 3].sum(), 100)
            entries = {entry['id']: entry for entry in build_viewer_catalog(output)['effects']}
            for name, pairing in expected.items():
                self.assertEqual(entries[name]['pairing'], pairing)
                self.assertIn('eldritch', entries[name]['variants'])


if __name__ == '__main__':
    unittest.main()
