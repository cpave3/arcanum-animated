from contextlib import ExitStack
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from animation_fx.catalog import EFFECTS
from animation_fx.effects import fireball
from animation_fx.palettes import PALETTES


class FireballTests(unittest.TestCase):
    def test_render_uses_separate_projectile_explosion_and_ground_layers(self):
        for name, frame, active in [
                ('fireball', 12, {'projectile'}),
                ('fireball-opening', 12, {'projectile'}),
                ('fireball', 34, {'explosion', 'ground'}),
                ('fireball-opening', 34, {'explosion', 'ground'}),
                ('fireball-embers', 30, {'ground'}),
                ('fireball-closing', 30, {'ground'}),
                ('fireball', 149, {'ground'})]:
            with self.subTest(effect=name, frame=frame):
                effect = EFFECTS[name]
                with ExitStack() as stack:
                    spies = {layer: stack.enter_context(patch.object(
                        fireball, layer, wraps=getattr(fireball, layer)))
                        for layer in ('projectile', 'explosion', 'ground')}
                    complete = np.asarray(effect.render(frame, 'fire'))
                    self.assertEqual({layer for layer, spy in spies.items() if spy.called}, active)
                    for layer in active:
                        spies[layer].assert_called_once()
                for layer in active:
                    with patch.object(fireball, layer, return_value=Image.new('RGBA', (640, 640))):
                        removed = np.asarray(effect.render(frame, 'fire'))
                    self.assertFalse(np.array_equal(complete, removed), layer)
                    self.assertGreater(complete[:, :, 3].sum(), removed[:, :, 3].sum())

    def test_projectile_travels_from_left_to_center(self):
        for name in ('fireball', 'fireball-opening'):
            centers = []
            for frame in (2, 7, 13):
                pixels = np.asarray(EFFECTS[name].render(frame, 'fire'))
                ys, xs = np.where(pixels[:, :, 3] > 128)
                centers.append((xs.min()+xs.max())/2)
                self.assertLess(abs((ys.min()+ys.max())/2-320), 20)
                self.assertGreater(np.ptp(xs), np.ptp(ys)*.8)
            self.assertLess(centers[0], 100)
            self.assertTrue(centers[0] < centers[1] < centers[2])
            self.assertLess(abs(centers[-1]-320), 65)

    def test_export_cooling_endpoint_decodes_fully_transparent(self):
        import subprocess
        import tempfile
        from pathlib import Path
        from animation_fx.catalog import Effect
        from animation_fx.export import export_effect
        from animation_fx.recipe import FrameRecipe
        cooling = Effect(FrameRecipe(lambda f: fireball.closing(f+76), SIZE=640, FRAMES=14),
                         'purple', loop=False)
        with tempfile.TemporaryDirectory() as directory:
            export_effect(cooling, ['fire'], Path(directory))
            raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-c:v', 'libvpx-vp9',
                '-i', str(Path(directory)/'fire.webm'), '-vf', 'select=eq(n\\,13)',
                '-pix_fmt', 'rgba', '-f', 'rawvideo', '-'])
            endpoint = np.frombuffer(raw, np.uint8).reshape(384, 384, 4)
            self.assertEqual(endpoint[:, :, 3].max(), 0)

    def test_fast_bolt_has_a_round_dense_shell_and_hot_inner_core(self):
        effect = EFFECTS['fireball']
        self.assertLess(effect.cue_frame/effect.fps, .5)
        image = np.asarray(effect.render(10, 'fire'))
        ys, xs = np.where(image[:, :, 3] > 240)
        self.assertLess(abs(np.ptp(xs)/np.ptp(ys)-1), .15)
        cx, cy = (xs.min()+xs.max())/2, (ys.min()+ys.max())/2
        yy, xx = np.mgrid[:640, :640]
        radius = np.hypot(xx-cx, yy-cy)
        self.assertGreater(image[radius < 7, :3].mean(),
                           image[(radius > 27) & (radius < 32), :3].mean()+20)

    def test_gas_pockets_ignite_in_succession_expand_and_move_outward(self):
        from animation_fx.primitives import gas
        original = gas.billow
        samples = {}
        for frame in (16, 20, 26, 32):
            with patch.object(gas, 'billow', wraps=original) as spy:
                image = np.asarray(EFFECTS['fireball'].render(frame, 'fire'))
            self.assertGreater(image[..., 3].sum(), 0)
            samples[frame] = {call.kwargs['seed']: call.args for call in spy.call_args_list}
        self.assertEqual(set(samples[16]), {0})
        self.assertGreater(len(samples[26]), len(samples[20]))
        self.assertGreater(len(samples[32]), len(samples[26]))
        early, late = samples[20][1], samples[32][1]
        self.assertGreater(late[2], early[2])
        self.assertGreater(np.linalg.norm(late[1]), np.linalg.norm(early[1]))
        complete = np.asarray(EFFECTS['fireball'].render(32, 'fire'))
        for omitted in (1, 4, 6):
            def without_pocket(*args, **kwargs):
                if kwargs['seed'] == omitted:
                    return Image.new('RGBA', (640, 640))
                return original(*args, **kwargs)
            with patch.object(gas, 'billow', side_effect=without_pocket):
                changed = np.asarray(EFFECTS['fireball'].render(32, 'fire'))
            self.assertGreater(np.abs(complete.astype(float)-changed).mean(), .1)

    def test_blast_is_broad_centered_and_top_down_without_other_layers(self):
        with patch.object(fireball, 'ground', return_value=Image.new('RGBA', (640, 640))):
            pixels = np.asarray(EFFECTS['fireball-opening'].render(38, 'fire'))
        ys, xs = np.where(pixels[:, :, 3] > 128)
        self.assertGreater(np.ptp(xs), 300)
        self.assertGreater(np.ptp(ys), 300)
        self.assertLess(abs(np.ptp(xs)-np.ptp(ys)), 70)
        self.assertLess(abs((xs.min()+xs.max())/2-320), 25)
        self.assertLess(abs((ys.min()+ys.max())/2-320), 25)

    def test_finite_endpoints_are_empty_and_clamped_in_every_palette(self):
        for name, endpoints in [('fireball', (0, 208)), ('fireball-opening', (0,)),
                                ('fireball-closing', (89,))]:
            effect = EFFECTS[name]
            for color in PALETTES:
                with self.subTest(effect=name, color=color):
                    for frame in endpoints:
                        image = effect.render(frame, color)
                        self.assertEqual(image.mode, 'RGBA')
                        self.assertEqual(image.size, (640, 640))
                        self.assertEqual(np.asarray(image)[:, :, 3].max(), 0)
                    for frame, clamped in [(-10, 0), (effect.frames+10, effect.frames-1)]:
                        np.testing.assert_array_equal(np.asarray(effect.render(frame, color)),
                                                      np.asarray(effect.render(clamped, color)))

    def test_embers_loop_seam_is_smooth_in_every_palette(self):
        effect = EFFECTS['fireball-embers']
        for color in PALETTES:
            with self.subTest(color=color):
                first, following, last = [np.asarray(effect.render(f, color)).astype(float)
                                          for f in (0, 1, effect.frames-1)]
                step = np.abs(following-first).mean()
                self.assertGreater(step, 0)
                self.assertLess(np.abs(last-first).mean(), 2*step)
                np.testing.assert_array_equal(first, np.asarray(effect.render(effect.frames, color)))
                self.assertGreater(first[:, :, 3].max(), 100)

    def test_one_shot_matches_shared_impact_and_close_in_every_palette(self):
        shot = EFFECTS['fireball']
        for color in PALETTES:
            for frame in (0, 12, 23, 24, 34, 75, 118, 119, 120, 149, 180, 208):
                with self.subTest(color=color, frame=frame):
                    name, local = ('fireball-opening', frame) if frame < 120 else (
                        'fireball-closing', frame-119)
                    np.testing.assert_array_equal(np.asarray(shot.render(frame, color)),
                                                  np.asarray(EFFECTS[name].render(local, color)))


if __name__ == '__main__':
    unittest.main()
