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
from animation_fx.profiles import ExportProfile
from animation_fx.viewer_catalog import build_viewer_catalog


CASTERS = ('ray-cast-1', 'ray-cast-2', 'ray-cast-3')


class PairedRayTests(unittest.TestCase):
    def pixels(self, name, frame, color='purple'):
        return np.asarray(EFFECTS[name].render(frame, color))

    def test_public_render_has_transparent_endpoints_and_all_palette_posters(self):
        self.assertEqual(len(PALETTES), 17)
        for name, frames in zip((*CASTERS, 'ray-hit'), (36, 46, 56, 42)):
            effect = EFFECTS[name]
            self.assertEqual((effect.size, effect.fps, effect.frames, effect.loop),
                             (640, 30, frames, False))
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

    def test_rendered_right_edge_has_exact_burst_count_with_charge_and_gaps(self):
        for count, name in enumerate(CASTERS, 1):
            with self.subTest(effect=name):
                alpha = [self.pixels(name, frame)[..., 3]
                         for frame in range(EFFECTS[name].frames)]
                # Measure actual edge light, not release metadata or painter calls.
                edge = [bool(image[290:350, -40:-24].max() > 20) for image in alpha]
                starts = [i for i, on in enumerate(edge) if on and not edge[i-1]]
                self.assertEqual(len(starts), count, edge)
                self.assertEqual(starts, [16+10*i for i in range(count)])
                self.assertGreater(alpha[8][240:400, 240:400].sum(), 1000)
                self.assertFalse(any(edge[:12]))
                for onset in (12+10*i for i in range(count)):
                    self.assertGreater(alpha[onset+4][290:350, 500:].sum(), 1000)
                    for frame in (onset+8, onset+9):
                        self.assertFalse(alpha[frame][290:350, 500:].any())

    def test_beams_feather_to_zero_at_both_frame_edges(self):
        for name, frame, reverse in [('ray-cast-3', 16, True), ('ray-hit', 4, False)]:
            alpha = self.pixels(name, frame)[..., 3]
            self.assertFalse(alpha[:, 0].any())
            self.assertFalse(alpha[:, -1].any())
            row = alpha[320, ::-1] if reverse else alpha[320]
            self.assertLess(row[8], row[24])
            self.assertLess(row[24], row[48])
            self.assertGreater(row[64], 150)

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

    def test_caster_beam_origin_is_feathered_and_orb_is_painted_last(self):
        from animation_fx.primitives.canvas import Canvas
        events = []
        beam_painter, charge_painter = beams.draw_beam, paired_rays.charge
        def beam(*args, **kwargs):
            events.append(('beam', kwargs.get('origin_fade')))
            return beam_painter(*args, **kwargs)
        def charge(*args):
            events.append(('orb', None))
            return charge_painter(*args)
        with patch.object(beams, 'draw_beam', side_effect=beam), \
                patch.object(paired_rays, 'charge', side_effect=charge):
            rendered = self.pixels('ray-cast-1', 16)
        self.assertEqual(events, [('beam', 24), ('orb', None)])
        with patch.object(paired_rays, 'charge'):
            without_orb = self.pixels('ray-cast-1', 16)
        self.assertGreater(rendered[310:330, 310:330, 3].sum(), without_orb[310:330, 310:330, 3].sum())
        isolated = Canvas(size=640)
        beam_painter(isolated, 4, (256, 256), (530, 256), origin_fade=24)
        row = np.asarray(isolated.image)[512, :, 3]
        self.assertEqual(row[512], 0)
        self.assertLess(row[520], row[536])
        self.assertLess(row[536], row[560])

    def test_target_enters_left_before_frame_four_then_impacts_at_center(self):
        for frame in (1, 2, 3):
            alpha = self.pixels('ray-hit', frame)[..., 3]
            self.assertGreater(alpha[290:350, :80].sum(), 1000)
            self.assertFalse(alpha[:, 320:].any())
        cue = self.pixels('ray-hit', 4)[..., 3]
        self.assertGreater(cue[300:340, 300:340].sum(), 1000)
        alpha = self.pixels('ray-hit', 10)[..., 3].astype(float)
        y, x = np.indices(alpha.shape)
        self.assertLess(abs((x*alpha).sum()/alpha.sum()-320), 8)
        self.assertLess(abs((y*alpha).sum()/alpha.sum()-320), 8)
        self.assertGreater(alpha[:280].sum(), 1000)
        self.assertGreater(alpha[360:].sum(), 1000)

    def test_caster_recipes_share_one_count_parameterized_renderer(self):
        for count, name in enumerate(CASTERS, 1):
            recipe = EFFECTS[name].renderer.render
            self.assertIs(recipe.func, paired_rays.caster)
            self.assertEqual(recipe.keywords, {'count': count})
            self.assertTrue(self.pixels(name, 16)[..., 3].any())

    def test_shared_beam_painter_visibly_contributes_to_all_four_effects(self):
        for name in (*CASTERS, 'ray-hit'):
            frame = 2 if name == 'ray-hit' else 16
            with self.subTest(effect=name):
                with patch.object(beams, 'draw_beam', wraps=beams.draw_beam) as spy:
                    complete = self.pixels(name, frame)
                self.assertTrue(spy.called)
                with patch.object(beams, 'draw_beam', return_value=None):
                    removed = self.pixels(name, frame)
                self.assertGreater(np.abs(complete.astype(float)-removed).sum(), 1000)
                region = np.s_[:, :160, 3] if name == 'ray-hit' else np.s_[:, 500:, 3]
                self.assertGreater(complete[region].sum(), removed[region].sum()+1000)

    def test_separate_target_impact_has_visible_contribution_only_after_arrival(self):
        for frame in (3, 4, 10):
            with patch.object(paired_rays, 'impact', wraps=paired_rays.impact) as spy:
                complete = self.pixels('ray-hit', frame)
            spy.assert_called_once_with(frame-4)
            with patch.object(paired_rays, 'impact', return_value=Image.new('RGBA', (640, 640))):
                removed = self.pixels('ray-hit', frame)
            if frame < 4:
                np.testing.assert_array_equal(complete, removed)
            else:
                self.assertGreater(complete[280:360, 280:360, 3].sum(),
                                   removed[280:360, 280:360, 3].sum()+1000)

    def test_real_exports_preserve_local_cues_pairing_and_decodable_alpha(self):
        profile = ExportProfile('test', scale=1, max_size=96, crf=22, cpu_used=8)
        expected = {
            'ray-cast-1': {'effects': ['ray-hit'], 'event': 'Release',
                           'times': [12/30], 'direction': 'right'},
            'ray-hit': {'effects': list(CASTERS), 'event': 'Impact',
                        'times': [4/30], 'direction': 'from-left'},
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
                    if name == 'ray-cast-1':
                        self.assertGreater(frames[16, 40:56, -4:, 3].sum(), 100)
                        self.assertLess(frames[21, 40:56, -4:, 3].max(), 5)
                    else:
                        self.assertGreater(frames[2, 40:56, :8, 3].sum(), 100)
                        self.assertGreater(frames[4, 44:52, 44:52, 3].sum(), 100)
            entries = {entry['id']: entry for entry in build_viewer_catalog(output)['effects']}
            for name, pairing in expected.items():
                self.assertEqual(entries[name]['pairing'], pairing)
                self.assertIn('eldritch', entries[name]['variants'])


if __name__ == '__main__':
    unittest.main()
