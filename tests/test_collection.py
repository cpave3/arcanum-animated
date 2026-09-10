import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from animation_fx.catalog import EFFECTS
from animation_fx.palettes import PALETTES

ROOT = Path(__file__).resolve().parents[1]


class CollectionTests(unittest.TestCase):
    def test_render_colorways_preserve_alpha_and_animate(self):
        for name, effect in EFFECTS.items():
            sample = effect.poster_frame
            original = np.asarray(effect.render(sample, effect.source_color))
            for color in PALETTES:
                with self.subTest(effect=name, color=color):
                    first = np.asarray(effect.render(sample, color))
                    later = np.asarray(effect.render(effect.fps, color))
                    np.testing.assert_array_equal(first[:, :, 3], original[:, :, 3])
                    if effect.loop:
                        np.testing.assert_array_equal(first, np.asarray(effect.render(effect.frames, color)))
                    else:
                        np.testing.assert_array_equal(np.asarray(effect.render(effect.frames-1, color)),
                                                      np.asarray(effect.render(effect.frames+10, color)))
                    self.assertEqual(first[0, 0, 3], 0)
                    self.assertFalse(np.array_equal(first, later))
                    if PALETTES[color] != PALETTES[effect.source_color]:
                        visible = first[:, :, 3] > 100
                        self.assertFalse(np.array_equal(first[visible, :3], original[visible, :3]))
                    if name in ('rift', 'vortex', 'vortex-black-hole'):
                        center = first[effect.size//2-4:effect.size//2+4, effect.size//2-4:effect.size//2+4]
                        self.assertTrue(np.all(center[:, :, 3] == 255))
                        self.assertLess(center[:, :, :3].max(), 90)

    def test_one_shots_start_end_and_portal_handoff(self):
        for name, effect in EFFECTS.items():
            if effect.loop:
                continue
            with self.subTest(effect=name):
                first = np.asarray(effect.render(0, 'purple'))
                last = np.asarray(effect.render(effect.frames-1, 'purple'))
                peak = np.asarray(effect.render(effect.poster_frame, 'purple'))
                self.assertGreater(peak[:, :, 3].max(), 100)
                if name not in ('portal-close', 'vortex-closing'):
                    self.assertTrue(np.all(first[:, :, 3] == 0))
                if name not in ('portal-open', 'vortex-opening'):
                    self.assertTrue(np.all(last[:, :, 3] == 0))
                np.testing.assert_array_equal(last, np.asarray(effect.render(effect.frames, 'purple')))
        for color in PALETTES:
            steady = np.asarray(EFFECTS['rift'].render(0, color))
            np.testing.assert_array_equal(steady, np.asarray(EFFECTS['portal-open'].render(59, color)))
            np.testing.assert_array_equal(steady, np.asarray(EFFECTS['portal-close'].render(0, color)))
        departure = np.asarray(EFFECTS['teleport-departure'].render(24, 'purple'))
        reversed_arrival = np.asarray(EFFECTS['teleport-arrival'].render(59-24, 'purple'))
        self.assertFalse(np.array_equal(departure, reversed_arrival))

    def test_one_shot_cli_export_has_visible_poster_and_finite_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run([sys.executable, str(ROOT / 'render.py'), '--effect', 'teleport-arrival',
                            '--color', 'necrotic', '--output', directory], check=True, stdout=subprocess.PIPE)
            folder = Path(directory) / 'teleport-arrival'
            metadata = json.loads((folder / 'effect.json').read_text())
            self.assertFalse(metadata['loop'])
            self.assertEqual(metadata['duration'], 2)
            self.assertEqual(metadata['profile'], 'vtt')
            self.assertEqual(metadata['size'], 384)
            self.assertEqual(metadata['frames'], 60)
            self.assertEqual(metadata['fps'], 30)
            self.assertEqual(metadata['cue_time'], .4)
            self.assertGreater(np.asarray(Image.open(folder / 'necrotic.png'))[:, :, 3].max(), 100)
            raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-c:v', 'libvpx-vp9',
                    '-i', str(folder / 'necrotic.webm'), '-vf', 'select=eq(n\\,0)+eq(n\\,59)',
                    '-fps_mode', 'passthrough', '-pix_fmt', 'rgba', '-f', 'rawvideo', '-'])
            endpoints = np.frombuffer(raw, dtype=np.uint8).reshape(2, 384, 384, 4)
            self.assertTrue(np.all(endpoints[:, :, :, 3] == 0))

    def test_ground_eruption_is_crack_focused_and_top_down(self):
        from animation_fx.primitives import cracks
        effect = EFFECTS['ground-eruption']
        early = np.asarray(effect.render(8, 'purple'))
        peak = np.asarray(effect.render(effect.poster_frame, 'purple'))
        with patch.object(cracks, 'draw_cracks'):
            accents = np.asarray(effect.render(effect.poster_frame, 'purple'))
        self.assertGreater(peak[:, :, 3].sum(), 4*accents[:, :, 3].sum())
        ys, xs = np.where(peak[:, :, 3] > 128)
        self.assertGreater(np.ptp(xs), 300)
        self.assertGreater(np.ptp(ys), 300)
        self.assertLess(abs(np.ptp(xs)-np.ptp(ys)), 70)
        self.assertLess(abs((xs.min()+xs.max())/2-256), 25)
        self.assertLess(abs((ys.min()+ys.max())/2-256), 25)
        early_y, early_x = np.where(early[:, :, 3] > 128)
        self.assertLess(np.ptp(early_x), np.ptp(xs)*.6)
        self.assertLess(np.ptp(early_y), np.ptp(ys)*.6)
        self.assertTrue(np.all(np.asarray(effect.render(0, 'purple'))[:, :, 3] == 0))
        self.assertTrue(np.all(np.asarray(effect.render(59, 'purple'))[:, :, 3] == 0))

    def test_miasma_is_dark_translucent_and_loops(self):
        effect = EFFECTS['miasma-pool']
        frames = [np.asarray(effect.render(f, 'purple')) for f in (0, 1, effect.frames-1)]
        image = frames[0]
        self.assertEqual(effect.frames/effect.fps, 4)
        self.assertTrue(np.all(image[0, :, 3] == 0))
        self.assertTrue(np.all(image[:, 0, 3] == 0))
        self.assertLess(image[:, :, 3].max(), 255)
        self.assertGreater(np.count_nonzero(image[:, :, 3] > 180), 5000)
        self.assertLess(image[:, :, :3][image[:, :, 3] > 180].mean(), 70)
        jump = np.abs(frames[0].astype(float) - frames[-1]).mean()
        step = np.abs(frames[0].astype(float) - frames[1]).mean()
        self.assertLess(jump, 2*step)

    def test_impact_uses_short_trails_that_keep_moving(self):
        from animation_fx.primitives import particles
        original = particles.draw_spark
        captured = []
        def record(draw, head, tail, **style):
            captured.append(np.asarray([tail, head]))
            return original(draw, head, tail, **style)
        samples = []
        for frame in (18, 36):
            captured.clear()
            with patch.object(particles, 'draw_spark', record):
                image = EFFECTS['impact-burst'].render(frame, 'purple')
            self.assertGreater(np.asarray(image)[:, :, 3].max(), 0)
            samples.append(np.asarray(captured))
        self.assertGreater(len(samples[0]), 20)
        for before, after in zip(*samples):
            self.assertLess(np.linalg.norm(before[1]-before[0]), 12)
            self.assertGreater(np.linalg.norm(after[1]-256), np.linalg.norm(before[1]-256)+15)
            self.assertGreater(np.linalg.norm(after[0]-256), np.linalg.norm(before[0]-256)+15)
            self.assertLess(np.linalg.norm(after[1]-after[0]), np.linalg.norm(before[1]-before[0]))

    def test_rune_library_is_shared_and_varied(self):
        from animation_fx.primitives import runes
        original = runes.draw_rune
        for name, frame in [('rune-anchor', 0), ('casting-release', 18), ('dispel', 18)]:
            with self.subTest(effect=name):
                glyphs = []
                def record(draw, glyph, **options):
                    glyphs.append(glyph)
                    return original(draw, glyph, **options)
                with patch.object(runes, 'draw_rune', record):
                    before = np.asarray(EFFECTS[name].render(frame, EFFECTS[name].source_color))
                self.assertGreaterEqual(len(set(glyphs)), 5)
                with patch.dict(runes.GLYPHS, {'spire': (((0, -14), (0, 14)),)}):
                    changed = np.asarray(EFFECTS[name].render(frame, EFFECTS[name].source_color))
                self.assertFalse(np.array_equal(before, changed))

    def test_both_closings_use_the_same_finishing_sparks(self):
        from animation_fx.primitives import particles
        original = particles.draw_burst
        calls = []
        for name in ('portal-close', 'vortex-closing'):
            effect = EFFECTS[name]
            with self.subTest(effect=name):
                def record(draw, age, **options):
                    calls.append((age, options))
                    return original(draw, age, **options)
                with patch.object(particles, 'draw_burst', record):
                    complete = np.asarray(effect.render(52, 'purple'))
                with patch.object(particles, 'draw_burst'):
                    no_sparks = np.asarray(effect.render(52, 'purple'))
                yy, xx = np.mgrid[:effect.size, :effect.size]
                outside_flash = np.hypot(xx-effect.size/2, yy-effect.size/2) > effect.size*.125
                self.assertGreater(complete[outside_flash, 3].sum(), no_sparks[outside_flash, 3].sum()+100)
        self.assertEqual(calls[0], calls[1])

    def test_all_spark_emitters_use_the_same_painter(self):
        from animation_fx.primitives import particles
        for name in ('orb-anchor', 'rune-anchor', 'vortex', 'teleport-departure', 'impact-burst'):
            effect = EFFECTS[name]
            with self.subTest(effect=name):
                before = np.asarray(effect.render(36, effect.source_color))
                with patch.object(particles, 'draw_spark'):
                    changed = np.asarray(effect.render(36, effect.source_color))
                self.assertFalse(np.array_equal(before, changed))

    def test_vortex_transitions_match_loop_and_swallow_swirl_before_closing(self):
        for color in PALETTES:
            loop = np.asarray(EFFECTS['vortex'].render(0, color))
            np.testing.assert_array_equal(loop, np.asarray(EFFECTS['vortex-opening'].render(59, color)))
            np.testing.assert_array_equal(loop, np.asarray(EFFECTS['vortex-closing'].render(0, color)))
        opening = EFFECTS['vortex-opening']
        closing = EFFECTS['vortex-closing']
        yy, xx = np.mgrid[:640, :640]
        outer = np.hypot(xx-320, yy-320) > 170
        first = np.asarray(opening.render(15, 'purple'))
        later = np.asarray(opening.render(45, 'purple'))
        self.assertGreater(later[outer, 3].sum(), first[outer, 3].sum()+10000)
        swallowed = np.asarray(closing.render(36, 'purple'))
        self.assertTrue(np.all(swallowed[outer, 3] == 0))
        self.assertEqual(swallowed[320, 320, 3], 255)

    def test_vortex_variants_have_distinct_centers_and_shared_spirals(self):
        for frame in (0, 22, 45, 67):
            with self.subTest(frame=frame):
                opened = np.asarray(EFFECTS['vortex-open'].render(frame, 'purple'))
                hole = np.asarray(EFFECTS['vortex-black-hole'].render(frame, 'purple'))
                original = np.asarray(EFFECTS['vortex'].render(frame, 'purple'))
                self.assertTrue(np.all(opened[312:328, 312:328, 3] == 0))
                self.assertTrue(np.any(opened[:, :, 3] > 100))
                self.assertTrue(np.all(hole[300:340, 300:340, 3] == 255))
                self.assertLess(hole[300:340, 300:340, :3].max(), 90)
                outside = np.ones((640, 640), dtype=bool)
                outside[170:470, 170:470] = False
                np.testing.assert_array_equal(opened[outside], hole[outside])
                np.testing.assert_array_equal(opened[outside], original[outside])
                yy, xx = np.mgrid[:640, :640]
                radius = np.hypot(xx-320, yy-320)
                disk = radius < 62
                self.assertTrue(np.all(hole[disk, 3] == 255))
                self.assertLess(hole[disk, :3].max(), 40)
                ring = (radius > 65) & (radius < 67)
                self.assertGreater(hole[ring, :3].mean(), 150)
                self.assertGreater(hole[ring, :3].mean(), opened[ring, :3].mean() + 50)
        effect = EFFECTS['vortex-black-hole']
        frames = [np.asarray(effect.render(frame, 'purple')) for frame in (0, 22)]
        for pixels in frames:
            silhouette = (pixels[:, :, 3] == 255) & (pixels[:, :, :3].max(axis=2) < 40)
            np.testing.assert_array_equal(silhouette[radius < 64], (radius <= 62.5)[radius < 64])
        orbit_ring = (radius > 73) & (radius < 77)
        self.assertGreater(np.abs(frames[0][orbit_ring].astype(float) - frames[1][orbit_ring]).mean(), 10)
        for name in ('vortex-open', 'vortex-black-hole'):
            effect = EFFECTS[name]
            first, following, last = [np.asarray(effect.render(f, 'purple')).astype(float)
                                      for f in (0, 1, effect.frames-1)]
            self.assertLess(np.abs(last-first).mean(), 2*np.abs(following-first).mean())

    def test_damage_aliases_preserve_gold_and_red_artwork(self):
        for name, effect in EFFECTS.items():
            for damage, color in [('radiant', 'gold'), ('force', 'red')]:
                with self.subTest(effect=name, damage=damage):
                    np.testing.assert_array_equal(np.asarray(effect.render(17, damage)),
                                                  np.asarray(effect.render(17, color)))

    def test_necrotic_vortex_has_green_shadows_and_cyan_highlights(self):
        effect = EFFECTS['vortex']
        image = effect.render(0, 'necrotic')
        pixels = np.asarray(image)
        hsv = np.asarray(image.convert('RGB').convert('HSV')).astype(float)
        hue = hsv[:, :, 0] * 360 / 255
        visible = (pixels[:, :, 3] > 20) & (hsv[:, :, 1] > 80)
        self.assertTrue(np.any(visible & (hue > 135) & (hue < 165)))
        self.assertTrue(np.any(visible & (hue > 170) & (hue < 195)))
        source = np.asarray(effect.render(0, 'purple'))
        np.testing.assert_array_equal(pixels[:, :, 3], source[:, :, 3])
        np.testing.assert_array_equal(pixels[:, :, :3].max(axis=2), source[:, :, :3].max(axis=2))

    def test_original_colorways_keep_existing_artwork(self):
        snapshots = {'rift': 'purple-rift.png', 'vortex': 'purple-rift-outward.png',
                     'orb-anchor': 'golden-anchor.png', 'rune-anchor': 'golden-rune-anchor.png'}
        for name, snapshot in snapshots.items():
            effect = EFFECTS[name]
            with self.subTest(effect=name):
                np.testing.assert_array_equal(np.asarray(effect.render(0, effect.source_color)),
                                              np.asarray(Image.open(ROOT / snapshot)))

    def test_cli_exports_real_transparent_webm_and_png(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run([sys.executable, str(ROOT / 'render.py'), '--effect', 'rune-anchor',
                            '--color', 'melee', '--output', directory], cwd=directory, check=True,
                           stdout=subprocess.PIPE)
            webm = Path(directory) / 'rune-anchor/melee.webm'
            png = webm.with_suffix('.png')
            self.assertTrue(png.is_file())
            catalog = json.loads((Path(directory) / 'catalog.json').read_text())
            self.assertEqual(catalog['schema'], 1)
            entry = next(effect for effect in catalog['effects'] if effect['id'] == 'rune-anchor')
            self.assertEqual(entry['kind'], 'loop')
            self.assertEqual(entry['role'], 'anchor')
            self.assertEqual({key: entry[key] for key in ('size', 'fps', 'frames', 'duration', 'cue_time')},
                             {'size': 256, 'fps': 30, 'frames': 90, 'duration': 3, 'cue_time': None})
            self.assertEqual(entry['variants'], {'melee': {
                'webm': 'rune-anchor/melee.webm',
                'poster': 'rune-anchor/melee.png',
                'bytes': webm.stat().st_size,
                'version': f'{webm.stat().st_mtime_ns}-{png.stat().st_mtime_ns}',
            }})
            info = json.loads(subprocess.check_output(['ffprobe', '-v', 'error',
                              '-show_entries', 'stream=width,height:format=duration', '-of', 'json', str(webm)]))
            self.assertEqual(info['streams'][0]['width'], 256)
            self.assertEqual(float(info['format']['duration']), 3)
            decoded = subprocess.check_output(['ffmpeg', '-v', 'error', '-c:v', 'libvpx-vp9',
                       '-i', str(webm), '-frames:v', '1', '-pix_fmt', 'rgba', '-f', 'rawvideo', '-'])
            pixels = np.frombuffer(decoded, dtype=np.uint8).reshape(256, 256, 4)
            self.assertEqual(pixels[0, 0, 3], 0)
            self.assertGreater(pixels[:, :, 3].max(), 230)
            mixed = subprocess.run([sys.executable, str(ROOT / 'render.py'), '--effect', 'rune-anchor',
                                    '--color', 'purple', '--profile', 'high', '--output', directory],
                                   capture_output=True, text=True)
            self.assertNotEqual(mixed.returncode, 0)
            self.assertIn('Cannot mix export profiles', mixed.stderr)
            self.assertFalse((webm.parent / 'purple.webm').exists())
            self.assertEqual(json.loads((webm.parent / 'effect.json').read_text())['profile'], 'vtt')
            native_directory = Path(directory) / 'native'
            subprocess.run([sys.executable, str(ROOT / 'render.py'), '--effect', 'rune-anchor',
                            '--color', 'melee', '--profile', 'high', '--output', str(native_directory)],
                           check=True, stdout=subprocess.PIPE)
            native = native_directory / 'rune-anchor/melee.webm'
            self.assertLess(webm.stat().st_size, native.stat().st_size * .8)
            native_meta = json.loads((native.parent / 'effect.json').read_text())
            self.assertEqual(native_meta['size'], 320)
            self.assertEqual(native_meta['profile'], 'high')
            self.assertEqual(native_meta['fps'], 30)
            self.assertEqual(list(Path(directory).glob('**/.render-*')), [])
            for removed in ('typo', 'bludgeoning', 'piercing', 'slashing'):
                invalid = subprocess.run([sys.executable, str(ROOT / 'render.py'), '--color', removed],
                                         capture_output=True, text=True)
                self.assertNotEqual(invalid.returncode, 0)
                self.assertIn('invalid choice', invalid.stderr)


if __name__ == '__main__':
    unittest.main()
