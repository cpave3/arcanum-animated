"""Render a seamless, transparent VP9 rift asset. Requires Pillow, NumPy, ffmpeg."""
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SIZE = 512
SCALE = 2
FPS = 24
FRAMES = 72
OUT = Path(__file__).resolve().parent


def render(frame):
    phase = 2 * math.pi * frame / FRAMES
    left, right = [], []
    for i in range(49):
        t = i / 48
        y = 57 + 398 * t
        taper = math.sin(math.pi * t)
        center = 256 + 12 * math.sin(t * 8) + 6 * math.sin(t * 27)
        center += 3 * taper * math.sin(t * 19 + phase)
        width = taper ** 0.85 * (24 + 7 * math.sin(t * 17) ** 2)
        width *= 1 + 0.065 * math.sin(phase + t * 5)
        jag = taper * (4 * math.sin(i * 2.7) + 3 * math.cos(i * 1.8))
        left.append(((center - width + jag) * SCALE, y * SCALE))
        right.append(((center + width + 3 * taper * math.sin(i * 2.3)) * SCALE, y * SCALE))
    polygon = left + right[::-1]
    dimensions = (SIZE * SCALE,) * 2
    edge = Image.new('L', dimensions)
    ImageDraw.Draw(edge).line(polygon + [polygon[0]], fill=255, width=3 * SCALE, joint='curve')
    result = Image.new('RGBA', dimensions)
    pulse = 0.85 + 0.15 * math.sin(phase)
    for radius, color, opacity in [(15, (104, 0, 255), .40), (6, (143, 15, 255), .65), (2, (177, 40, 255), .85)]:
        mask = edge.filter(ImageFilter.GaussianBlur(radius * SCALE))
        mask = mask.point(lambda p: round(p * opacity * pulse))
        layer = Image.new('RGBA', dimensions, color + (0,))
        layer.putalpha(mask)
        result = Image.alpha_composite(result, layer)
    mask = Image.new('L', dimensions)
    ImageDraw.Draw(mask).polygon(polygon, fill=255)
    yy, xx = np.mgrid[:SIZE*SCALE, :SIZE*SCALE].astype(np.float32)
    x, y = (xx / SCALE - 256) / 100, (yy / SCALE - 256) / 100
    shimmer = (.5 + .5 * np.sin(12 * x + 3 * y + phase
                               + 2 * np.sin(4 * y - 2 * phase))) ** 3
    folds = (.5 + .5 * np.sin(7 * x - 5 * y - phase)) ** 2
    interior = np.zeros((SIZE*SCALE, SIZE*SCALE, 4), dtype=np.uint8)
    interior[:, :, 0] = (3 + 40 * shimmer * folds).astype(np.uint8)
    interior[:, :, 1] = (1 + 8 * shimmer).astype(np.uint8)
    interior[:, :, 2] = (7 + 68 * shimmer * folds).astype(np.uint8)
    interior[:, :, 3] = np.asarray(mask)
    result = Image.alpha_composite(result, Image.fromarray(interior))
    draw = ImageDraw.Draw(result)
    draw.line(polygon + [polygon[0]], fill=(159, 35, 255, 255), width=3 * SCALE, joint='curve')
    draw.line(polygon + [polygon[0]], fill=(225, 149, 255, 255), width=SCALE, joint='curve')
    return result.resize((SIZE, SIZE), Image.Resampling.LANCZOS)


def main():
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
               '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{SIZE}x{SIZE}',
               '-r', str(FPS), '-i', '-', '-an', '-c:v', 'libvpx-vp9',
               '-pix_fmt', 'yuva420p', '-b:v', '0', '-crf', '24',
               '-deadline', 'good', '-cpu-used', '4', '-auto-alt-ref', '0',
               str(OUT / 'purple-rift.rendering.webm')]
    with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
        for frame in range(FRAMES):
            image = render(frame)
            if frame == 0:
                image.save(OUT / 'purple-rift.png')
                yy, xx = np.indices((SIZE, SIZE))
                checks = np.where((xx // 32 + yy // 32) % 2, 58, 40).astype('uint8')
                background = Image.fromarray(np.stack([checks, checks, checks, np.full_like(checks, 255)], axis=-1))
                Image.alpha_composite(background, image).save(OUT / 'preview.png')
            encoder.stdin.write(image.tobytes())
        encoder.stdin.close()
        if encoder.wait() != 0:
            raise RuntimeError('WebM encoding failed')
    (OUT / 'purple-rift.rendering.webm').replace(OUT / 'purple-rift.webm')
    print(OUT / 'purple-rift.webm')


if __name__ == '__main__':
    main()
