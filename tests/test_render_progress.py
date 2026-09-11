import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from PIL import Image

from animation_fx.catalog import EFFECTS, Effect
from animation_fx.export import export_effect
from animation_fx.recipe import FrameRecipe
import render

ROOT = Path(__file__).resolve().parents[1]


def small_effect():
    return Effect(FrameRecipe(lambda frame: Image.new('RGBA', (16, 16),
                                                      (120, 30, 180, 100+frame)),
                              SIZE=16, FRAMES=6), 'purple')


class ProgressStream(io.StringIO):
    def __init__(self, tty=False):
        super().__init__()
        self.tty = tty
        self.flushes = 0

    def isatty(self):
        return self.tty

    def flush(self):
        self.flushes += 1
        super().flush()


class RenderProgressTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name)

    def test_cli_real_ray_export_reports_progress_and_publishes_assets(self):
        result = subprocess.run([sys.executable, str(ROOT / 'render.py'),
                                 '--effect', 'ray-cast-1', '--color', 'eldritch',
                                 '--output', str(self.output)],
                                capture_output=True, text=True, check=True, timeout=120)
        lines = result.stderr.splitlines()
        frames = EFFECTS['ray-cast-1'].frames
        self.assertIn(f'[1/1] ray-cast-1 rendering: frame 0/{frames} (0%)', lines[0])
        self.assertTrue(any('rendering:' in line and 'frame 0/' not in line
                            and '(100%)' not in line for line in lines))
        self.assertIn(f'frame {frames}/{frames} (100%)', result.stderr)
        self.assertIn('elapsed ', result.stderr)
        self.assertIn('frame ETA ', result.stderr)
        self.assertNotIn('\r', result.stderr)
        phases = [line.split('ray-cast-1 ')[1].split(':')[0] for line in lines]
        self.assertEqual(phases[-3:], ['encoding', 'finalizing', 'complete'])
        self.assertIn('output not published', lines[-3])
        self.assertIn('output published', lines[-1])
        self.assertIn('Collection ready:', result.stdout)
        folder = self.output / 'ray-cast-1'
        metadata = json.loads((folder / 'effect.json').read_text())
        self.assertEqual(metadata['pairing'], EFFECTS['ray-cast-1'].pairing)
        with Image.open(folder / 'eldritch.png') as poster:
            self.assertIsNotNone(poster.getchannel('A').getbbox())
        probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                                'stream=codec_name', '-of', 'json',
                                str(folder / 'eldritch.webm')],
                               capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(probe.stdout)['streams'][0]['codec_name'], 'vp9')
        catalog = json.loads((self.output / 'catalog.json').read_text())
        entry = next(e for e in catalog['effects'] if e['id'] == 'ray-cast-1')
        self.assertIn('eldritch', entry['variants'])

    def test_export_callback_orders_frames_and_completion_after_publication(self):
        events = []
        colors = ['purple', 'eldritch']

        def progress(event):
            events.append(event)
            for name in ['effect.json', *(f'{c}.{s}' for c in colors for s in ('png', 'webm'))]:
                self.assertEqual((self.output / name).exists(), event.phase == 'complete')

        export_effect(small_effect(), colors, self.output, progress=progress)
        self.assertEqual([e.phase for e in events], ['rendering'] * 7 +
                         ['encoding', 'finalizing', 'complete'])
        self.assertEqual([e.frame for e in events[:7]], list(range(7)))
        self.assertTrue(all(e.total == 6 for e in events))
        self.assertEqual([e.elapsed for e in events], sorted(e.elapsed for e in events))
        self.assertIsNone(events[0].eta)
        self.assertGreater(events[1].eta, 0)
        self.assertEqual(events[6].eta, 0)
        self.assertTrue(all(e.eta is None for e in events[7:]))

    def test_export_without_callback_is_quiet(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            export_effect(small_effect(), ['purple'], self.output)
        self.assertEqual(stdout.getvalue() + stderr.getvalue(), '')
        self.assertGreater((self.output / 'purple.webm').stat().st_size, 0)

    def failing_encoder(self):
        bin_dir = self.output / 'bin'
        bin_dir.mkdir()
        encoder = bin_dir / 'ffmpeg'
        encoder.write_text(f'#!{sys.executable}\nimport sys\nsys.stdin.buffer.read()\n'
                           'print("encoder intentionally failed", file=sys.stderr)\nsys.exit(7)\n')
        encoder.chmod(0o755)
        return {'PATH': str(bin_dir) + os.pathsep + os.environ['PATH']}

    def test_failed_encoder_never_completes_or_replaces_existing_files(self):
        events = []
        for name in ('purple.png', 'purple.webm', 'effect.json'):
            (self.output / name).write_bytes(b'original')
        with patch.dict(os.environ, self.failing_encoder()):
            with self.assertRaisesRegex(RuntimeError, 'Encoding purple failed'):
                export_effect(small_effect(), ['purple'], self.output, progress=events.append)
        self.assertEqual(events[-1].phase, 'encoding')
        self.assertNotIn('complete', [e.phase for e in events])
        for name in ('purple.png', 'purple.webm', 'effect.json'):
            self.assertEqual((self.output / name).read_bytes(), b'original')

    def test_cli_failed_encoder_surfaces_error_without_success(self):
        stream, stdout = ProgressStream(tty=True), io.StringIO()
        with patch.dict(os.environ, self.failing_encoder()), \
                patch.object(render, 'EFFECTS', {'tiny': small_effect()}), \
                patch.object(sys, 'argv', ['render.py', '--effect', 'tiny', '--color',
                                          'purple', '--output', str(self.output)]), \
                redirect_stderr(stream), redirect_stdout(stdout):
            with self.assertRaisesRegex(RuntimeError, 'Encoding purple failed'):
                render.main()
        self.assertNotIn('complete:', stream.getvalue())
        self.assertNotIn('Collection ready:', stdout.getvalue())
        self.assertTrue(stream.getvalue().endswith('\n'))
        self.assertFalse((self.output / 'tiny/effect.json').exists())

    def test_cli_throttles_real_exports_and_formats_tty_and_redirected_logs(self):
        for tty in (False, True):
            with self.subTest(tty=tty):
                stream = ProgressStream(tty)
                # Public CLI -> real export; deterministic time isolates throttling from ffmpeg speed.
                with patch.object(render, 'EFFECTS', {'first': small_effect(), 'second': small_effect()}), \
                        patch.object(sys, 'argv', ['render.py', '--color', 'purple',
                                                  '--output', str(self.output)]), \
                        patch('animation_fx.export.monotonic', side_effect=[
                            0, 0, .1, .2, .5, .6, .7, .8, .9, 1, 1.1] * 2), \
                        redirect_stderr(stream), redirect_stdout(io.StringIO()):
                    render.main()
                text = stream.getvalue()
                self.assertEqual(text.count('rendering:'), 6)
                self.assertIn('[1/2] first rendering: frame 3/6 (50%)', text)
                self.assertIn('[2/2] second complete:', text)
                self.assertNotIn('frame 1/6', text)
                self.assertEqual('\r' in text, tty)
                self.assertEqual(text.count('\n'), 2 if tty else 12)
                self.assertGreaterEqual(stream.flushes, 12)

    def test_catalog_only_has_no_render_progress(self):
        result = subprocess.run([sys.executable, str(ROOT / 'render.py'), '--catalog-only',
                                 '--output', str(self.output)], capture_output=True,
                                text=True, check=True)
        self.assertEqual(result.stderr, '')
        self.assertIn('Catalog ready:', result.stdout)
        self.assertEqual(list(self.output.iterdir()), [self.output / 'catalog.json'])


if __name__ == '__main__':
    unittest.main()
