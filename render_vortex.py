"""Original outward-flowing rift inspired by a smoky cosmic vortex.

Run with Python, NumPy, Pillow, and ffmpeg installed.
"""
import math
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent
SIZE = 640
FPS = 30
FRAMES = 90
Y, X = np.mgrid[:SIZE, :SIZE].astype(np.float32)
X = (X - SIZE / 2) / 275
Y = (Y - SIZE / 2) / 275
R = np.sqrt(X * X + Y * Y)
ANGLE = np.arctan2(Y, X)
RNG = np.random.default_rng(73)
PARTICLES = RNG.random((220, 5))


def render(frame):
    time = (frame % FRAMES) / FRAMES
    phase = math.tau * time
    # Integer temporal harmonics make every field periodic over one loop.
    noise = (np.sin(19 * X + 11 * Y + 2 * np.sin(9 * Y + phase))
             + np.sin(31 * Y - 13 * X + np.sin(15 * X - phase))
             + .5 * np.sin(57 * X + 39 * Y + 2 * np.sin(21 * Y + phase))) / 2.5
    spiral = 3 * ANGLE - 17 * R + 2 * phase + .65 * noise
    ribbons = np.exp(-((np.sin(spiral / 2) / .105) ** 2))
    wisps = np.exp(-((np.sin((spiral + .65 + .25 * noise) / 2) / .30) ** 2))
    envelope = np.clip((1.03 - R) / .30, 0, 1) ** 2
    envelope *= np.clip((R - .12) / .18, 0, 1)
    clouds = (0.5 + 0.5 * noise) ** 2
    broken = .45 + .55 * (.5 + .5 * np.sin(13 * R + 4 * ANGLE - phase))
    slow_spiral = 2 * ANGLE - 12 * R + phase + .35 * noise
    fast_spiral = 4 * ANGLE - 21 * R + 3 * phase + .45 * noise
    slow = np.exp(-(np.sin(slow_spiral / 2) / .24) ** 2)
    fast = np.exp(-(np.sin(fast_spiral / 2) / .075) ** 2)
    strength = envelope * (.12 * clouds + .36 * ribbons * broken
                           + .12 * wisps + .18 * slow + .20 * fast * broken)
    alpha = np.clip(envelope * (.13 + .40 * clouds) + strength, 0, .90)
    pixels = np.zeros((SIZE, SIZE, 4), dtype=np.uint8)
    pixels[:, :, 0] = np.clip(65 + 190 * strength, 0, 255)
    pixels[:, :, 1] = np.clip(12 + 115 * strength, 0, 255)
    pixels[:, :, 2] = np.clip(106 + 170 * strength, 0, 255)
    pixels[:, :, 3] = (alpha * 255).astype(np.uint8)
    image = Image.fromarray(pixels)

    sparks = Image.new('RGBA', (SIZE, SIZE))
    draw = ImageDraw.Draw(sparks)
    for offset, direction, speed, size, brightness in PARTICLES:
        age = (time + offset) % 1
        radius = .16 + .84 * age
        theta = direction * math.tau + 3.5 * age
        x = SIZE / 2 + 275 * radius * math.cos(theta)
        y = SIZE / 2 + 275 * radius * math.sin(theta)
        opacity = int(230 * math.sin(math.pi * age) ** 1.4 * (.4 + .6 * brightness))
        length = .012 + .022 * speed
        tail_r = radius - length
        tail_theta = theta - length * 3.5 / .84
        tail = (SIZE / 2 + 275 * tail_r * math.cos(tail_theta),
                SIZE / 2 + 275 * tail_r * math.sin(tail_theta))
        draw.line([tail, (x, y)], fill=(187, 80, 255, opacity // 2), width=1)
        dot = .55 + .75 * size
        draw.ellipse((x-dot, y-dot, x+dot, y+dot), fill=(239, 184, 255, opacity))
    image = Image.alpha_composite(image, sparks.filter(ImageFilter.GaussianBlur(2)))
    image = Image.alpha_composite(image, sparks)

    # Sparse contour points give the tear broad fractures instead of a serrated rim.
    left, right = [], []
    for i in range(25):
        t = i / 24
        taper = math.sin(math.pi * t)
        y = 211 + 218 * t
        center = 320 + 7 * math.sin(9 * t) + 3 * taper * math.sin(phase + 17 * t)
        width = 25 * taper ** .8 * (1 + .13 * math.sin(13 * t + phase))
        jagged = 3.2 * taper * math.sin(i * 2.4)
        left.append((center - width + jagged, y))
        right.append((center + width + jagged, y))
    contour = left + right[::-1]
    rim = Image.new('RGBA', (SIZE, SIZE))
    d = ImageDraw.Draw(rim)
    d.line(contour + [contour[0]], fill=(186, 32, 255, 230), width=5)
    image = Image.alpha_composite(image, rim.filter(ImageFilter.GaussianBlur(10)))
    image = Image.alpha_composite(image, rim.filter(ImageFilter.GaussianBlur(3)))
    mask = Image.new('L', (SIZE, SIZE))
    ImageDraw.Draw(mask).polygon(contour, fill=255)
    shimmer = (.5 + .5 * np.sin(36 * X + 8 * Y + phase
                               + 2 * np.sin(13 * Y - 2 * phase))) ** 3
    folds = (.5 + .5 * np.sin(19 * X - 17 * Y - phase)) ** 2
    darkness = np.exp(-((X / .10) ** 2))
    interior = np.zeros((SIZE, SIZE, 4), dtype=np.uint8)
    interior[:, :, 0] = (3 + 40 * shimmer * folds * darkness).astype(np.uint8)
    interior[:, :, 1] = (1 + 8 * shimmer * darkness).astype(np.uint8)
    interior[:, :, 2] = (7 + 68 * shimmer * folds * darkness).astype(np.uint8)
    interior[:, :, 3] = np.asarray(mask)
    image = Image.alpha_composite(image, Image.fromarray(interior))
    d = ImageDraw.Draw(image)
    d.line(contour + [contour[0]], fill=(191, 58, 249, 255), width=2)
    return image


def main():
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo',
               '-pix_fmt', 'rgba', '-s', f'{SIZE}x{SIZE}', '-r', str(FPS), '-i', '-',
               '-an', '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '0',
               '-crf', '25', '-deadline', 'good', '-cpu-used', '4', '-auto-alt-ref', '0',
               str(OUT / 'purple-rift-outward.rendering.webm')]
    with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
        for frame in range(FRAMES):
            image = render(frame)
            if frame == 0:
                image.save(OUT / 'purple-rift-outward.png')
                bg = Image.new('RGBA', image.size, (36, 36, 40, 255))
                Image.alpha_composite(bg, image).convert('RGB').save(OUT / 'preview-outward.jpg')
            encoder.stdin.write(image.tobytes())
        encoder.stdin.close()
        if encoder.wait() != 0:
            raise RuntimeError('WebM encoding failed')
    (OUT / 'purple-rift-outward.rendering.webm').replace(OUT / 'purple-rift-outward.webm')
    assert np.array_equal(np.asarray(render(0)), np.asarray(render(FRAMES)))
    print('Rendered outward vortex; exact loop periodicity verified.')


if __name__ == '__main__':
    main()
