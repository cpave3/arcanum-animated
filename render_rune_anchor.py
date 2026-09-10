"""Render a golden rune-column anchor with brackets and sparks. Requires Pillow, NumPy, and ffmpeg."""
import math
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent
SIZE = 320
SCALE = 2
FPS = 30
FRAMES = 90
PARTICLES = np.random.default_rng(128).random((150, 5))


def render(frame):
    time = (frame % FRAMES) / FRAMES
    phase = math.tau * time
    sparks = Image.new('RGBA', (SIZE * SCALE, SIZE * SCALE))
    draw = ImageDraw.Draw(sparks)

    def line(points, color, width=1):
        draw.line([(x * SCALE, y * SCALE) for x, y in points], fill=color, width=width * SCALE)

    # Distinct geometric glyphs brighten in sequence down the binding column.
    glyphs = [
        [[(-8, 8), (0, -9), (8, 8)], [(-5, 2), (5, 2)], [(0, -9), (0, -14)]],
        [[(-8, -8), (0, 0), (-8, 8)], [(0, -11), (0, 11)], [(0, 0), (8, -6)]],
        [[(0, -11), (9, 0), (0, 11), (-9, 0), (0, -11)], [(-4, 0), (4, 0)]],
        [[(-8, -7), (0, -1), (8, -7)], [(0, -1), (0, 11)], [(-7, 6), (7, 6)]],
        [[(-8, -9), (-8, 7), (0, 11), (8, 7), (8, -9)], [(-8, -1), (8, -1)]],
    ]
    for index, strokes in enumerate(glyphs):
        y = 88 + index * 36
        pulse = .72 + .28 * math.sin(phase - index * .8) ** 2
        for stroke in strokes:
            points = [(160 + x, y + dy) for x, dy in stroke]
            line(points, (255, 174, 30, int(245 * pulse)), 3)
            line(points, (255, 239, 159, int(255 * pulse)))
    for side in (-1, 1):
        points = [(160 + side * (25 + 8 * math.sin(math.pi * i / 40)),
                   65 + 190 * i / 40) for i in range(41)]
        line(points, (255, 183, 44, 215), 2)
        for y, direction in [(65, 1), (255, -1)]:
            line([(160 + side * 25, y), (160 + side * 16, y + direction * 8)],
                 (255, 225, 126, 240), 2)
    for offset, direction, velocity, size, brightness in PARTICLES:
        cycles = 1 + int(velocity * 3)
        age = (time * cycles + offset) % 1
        theta = math.tau * direction
        radius = 7 + (65 + 55 * velocity) * age
        x = 160 + math.cos(theta) * radius * .75
        y = 160 + math.sin(theta) * radius + 15 * age * age
        fade = math.sin(math.pi * age) ** 1.3
        opacity = int(255 * fade * (.5 + .5 * brightness))
        trail = 3 + 9 * velocity
        tail = (x - math.cos(theta) * trail * .75, y - math.sin(theta) * trail)
        line([tail, (x, y)], (255, 161, 24, opacity // 2))
        dot = .45 + .65 * size
        draw.ellipse(((x-dot)*SCALE, (y-dot)*SCALE, (x+dot)*SCALE, (y+dot)*SCALE),
                     fill=(255, 211 + int(35 * brightness), 100 + int(90 * brightness), opacity))
        if brightness > .93:
            line([(x-2, y), (x+2, y)], (255, 237, 166, opacity))
            line([(x, y-2), (x, y+2)], (255, 237, 166, opacity))
    glow = sparks.filter(ImageFilter.GaussianBlur(6 * SCALE))
    image = Image.alpha_composite(glow, sparks.filter(ImageFilter.GaussianBlur(2 * SCALE)))
    image = Image.alpha_composite(image, sparks)
    return image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)


def main():
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo',
               '-pix_fmt', 'rgba', '-s', f'{SIZE}x{SIZE}', '-r', str(FPS), '-i', '-',
               '-an', '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '0',
               '-crf', '22', '-deadline', 'good', '-cpu-used', '4', '-auto-alt-ref', '0',
               str(OUT / 'golden-rune-anchor.rendering.webm')]
    with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
        for frame in range(FRAMES):
            image = render(frame)
            if frame == 0:
                image.save(OUT / 'golden-rune-anchor.png')
            encoder.stdin.write(image.tobytes())
        encoder.stdin.close()
        if encoder.wait() != 0:
            raise RuntimeError('Anchor encoding failed')
    (OUT / 'golden-rune-anchor.rendering.webm').replace(OUT / 'golden-rune-anchor.webm')
    print('Rendered golden-rune-anchor.webm')


if __name__ == '__main__':
    main()
