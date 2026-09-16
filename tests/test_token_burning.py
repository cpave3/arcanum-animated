import json
from pathlib import Path
import tempfile
import unittest
from dataclasses import replace

import numpy as np

from animation_fx.catalog import EFFECTS
from animation_fx.export import export_effect
from animation_fx.palettes import PALETTES
from animation_fx.profiles import PROFILES
from animation_fx.recipe import FrameRecipe


class TokenBurningTests(unittest.TestCase):
    def setUp(self):
        self.effect = EFFECTS['token-burning']

    def test_public_render_has_front_flames_but_stays_token_sized_and_seamless(self):
        images = [np.asarray(self.effect.render(f, 'fire')) for f in (0, 1, 29, 30, 59, 60)]
        np.testing.assert_array_equal(images[0], images[-1])
        delta = lambda a, b: np.abs(a.astype(float)-b).mean()
        seam = delta(images[4], images[0])
        self.assertGreater(seam, .01)
        self.assertLess(seam, 2*delta(images[0], images[1]))
        for image in images:
            alpha = image[..., 3]
            self.assertGreater((alpha > 30).mean(), .15)
            self.assertLess((alpha > 30).mean(), .30)
            self.assertGreater(alpha[260:380, 260:380].mean(), 40)
            self.assertLess(alpha[260:380, 260:380].mean(), 140)
            self.assertFalse(alpha[[0, -1], :].any())
            self.assertFalse(alpha[:, [0, -1]].any())
        self.assertTrue(self.effect.loop)
        self.assertEqual(self.effect.default_color, 'fire')
        self.assertEqual(self.effect.frames/self.effect.fps, 2)

    def test_all_palettes_share_geometry(self):
        master = np.asarray(self.effect.render(24, 'purple'))
        for color in PALETTES:
            image = np.asarray(self.effect.render(24, color))
            np.testing.assert_array_equal(image[..., 3], master[..., 3])
            if color != 'purple':
                self.assertFalse(np.array_equal(image[..., :3], master[..., :3]))

    def test_vtt_export_keeps_native_resolution_for_huge_tokens(self):
        # Exercise the actual exporter with two real frames, not merely the registry floor.
        short = replace(self.effect, renderer=FrameRecipe(self.effect.master, SIZE=640, FPS=30, FRAMES=2))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            export_effect(short, ['fire'], output, PROFILES['vtt'])
            metadata = json.loads((output/'effect.json').read_text())
            self.assertEqual(metadata['size'], 640)
            self.assertGreater((output/'fire.webm').stat().st_size, 1000)
            from PIL import Image
            with Image.open(output/'fire.png') as image:
                self.assertEqual(image.size, (640, 640))


if __name__ == '__main__':
    unittest.main()
