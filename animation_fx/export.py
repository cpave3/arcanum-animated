"""Atomic transparent VP9 exports; render geometry once for all requested colors."""
from contextlib import ExitStack
from pathlib import Path
import json
import subprocess
import tempfile

from animation_fx.catalog import Effect
from animation_fx.palettes import PALETTES, colorize
from animation_fx.profiles import ExportProfile, PROFILES
from PIL import Image


def export_effect(effect: Effect, colors: list[str], directory: Path,
                  profile: ExportProfile = PROFILES['vtt']):
    directory.mkdir(parents=True, exist_ok=True)
    size = profile.size_for(effect.size)
    other_colors = {path.stem for path in directory.glob('*.webm')} - set(colors)
    if other_colors:
        metadata_path = directory / 'effect.json'
        existing = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
        expected = {'profile': profile.name, 'size': size, 'fps': effect.fps,
                    'frames': effect.frames, 'loop': effect.loop}
        if any(existing.get(key) != value for key, value in expected.items()):
            raise ValueError('Cannot mix export profiles or timing in one effect directory. '
                             'Use a separate --output folder or regenerate --color all.')
    # A unique workspace prevents browsers from reading an incomplete video.
    with tempfile.TemporaryDirectory(prefix='.render-', dir=directory) as work:
        work = Path(work)
        with ExitStack() as stack:
            encoders = {}
            for color in colors:
                command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                           '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{size}x{size}',
                           '-r', str(effect.fps), '-i', '-', '-an', '-c:v', 'libvpx-vp9',
                           '-pix_fmt', 'yuva420p', '-b:v', '0', '-crf', str(profile.crf),
                           '-deadline', 'good', '-cpu-used', str(profile.cpu_used), '-threads', '2',
                           '-auto-alt-ref', '0']
                if not effect.loop:
                    # Reset alpha prediction so a fully clear endpoint cannot retain quantized residue.
                    command.extend(['-force_key_frames', f'expr:eq(n,{effect.frames-1})'])
                command.append(str(work / f'{color}.webm'))
                encoders[color] = stack.enter_context(subprocess.Popen(command, stdin=subprocess.PIPE))
            for frame in range(effect.frames):
                master = effect.master(frame)
                if size != effect.size:
                    master = master.resize((size, size), Image.Resampling.LANCZOS)
                for color, encoder in encoders.items():
                    image = colorize(master, PALETTES[effect.source_color], PALETTES[color])
                    if frame == effect.poster_frame:
                        image.save(work / f'{color}.png')
                    encoder.stdin.write(image.tobytes())
            for color, encoder in encoders.items():
                encoder.stdin.close()
                if encoder.wait() != 0:
                    raise RuntimeError(f'Encoding {color} failed; existing exports were not changed')
        metadata = {'loop': effect.loop, 'fps': effect.fps, 'frames': effect.frames,
                    'duration': effect.frames/effect.fps, 'size': size,
                    'source_size': effect.size, 'profile': profile.name,
                    'cue_time': None if effect.cue_frame is None else effect.cue_frame/effect.fps,
                    'poster_time': effect.poster_frame/effect.fps}
        (work / 'effect.json').write_text(json.dumps(metadata, indent=2) + '\n')
        for color in colors:
            for suffix in ('png', 'webm'):
                (work / f'{color}.{suffix}').replace(directory / f'{color}.{suffix}')
        (work / 'effect.json').replace(directory / 'effect.json')
