"""Build the viewer manifest from registered effects and completed delivery exports."""
import colorsys
import json
import math
from pathlib import Path
import tempfile

from animation_fx.catalog import EFFECTS, ORIGINAL_COLORS, SEQUENCES, THEMED_COLORS
from animation_fx.palettes import PALETTES


def _metadata(effect, directory, has_variants):
    path = directory / 'effect.json'
    if not path.exists():
        if has_variants:
            raise ValueError(f'{path}: missing delivery metadata for exported variants')
        return {'loop': effect.loop, 'duration': effect.frames / effect.fps,
                'fps': effect.fps, 'frames': effect.frames, 'size': effect.size,
                'cue_time': None if effect.cue_frame is None else effect.cue_frame / effect.fps,
                **({'pairing': effect.pairing} if effect.pairing is not None else {})}
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict) or type(data.get('loop')) is not bool:
            raise ValueError('loop must be a boolean')
        for key in ('fps', 'frames', 'size', 'duration'):
            value = data.get(key)
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError(f'{key} must be a finite positive number')
            if key in ('frames', 'size') and type(value) is not int:
                raise ValueError(f'{key} must be an integer')
        if not math.isclose(data['duration'], data['frames'] / data['fps'], rel_tol=1e-6):
            raise ValueError('duration must match frames / fps')
        pairing = data.get('pairing')
        if effect.pairing is not None and pairing is None:
            raise ValueError('paired effect is missing pairing metadata; render it again')
        if pairing is not None:
            if not isinstance(pairing, dict):
                raise ValueError('pairing must be an object')
            partners, times = pairing.get('effects'), pairing.get('times')
            if (not isinstance(partners, list) or not partners
                    or any(not isinstance(item, str) or not item for item in partners)
                    or len(set(partners)) != len(partners)):
                raise ValueError('pairing effects must be distinct effect IDs')
            if (not isinstance(times, list) or not times
                    or any(type(t) not in (int, float) or not math.isfinite(t)
                           or not 0 <= t < data['duration'] for t in times)
                    or any(a >= b for a, b in zip(times, times[1:]))):
                raise ValueError('pairing times must increase within the clip duration')
            if not isinstance(pairing.get('event'), str) or not pairing['event']:
                raise ValueError('pairing event must be a label')
            if pairing.get('direction') not in ('right', 'from-left'):
                raise ValueError('invalid pairing direction')
        cue = data['cue_time']
        if cue is not None and (type(cue) not in (int, float) or not math.isfinite(cue)
                                or not 0 <= cue <= data['duration']):
            raise ValueError('cue_time must be null or within the clip duration')
    except (ValueError, KeyError) as error:
        raise ValueError(f'{path}: invalid delivery metadata: {error}') from error
    return data


def build_viewer_catalog(output_dir: Path | str) -> dict:
    """Atomically write catalog.json and return its schema-1 payload.

    Paths are relative to the manifest. bytes is the WebM length; version covers
    both WebM and poster mtimes. Missing exports retain source timing and size.
    Invalid delivery metadata or sequence definitions leave the old file intact.
    """
    output_dir = Path(output_dir)
    effects = []
    for name, effect in EFFECTS.items():
        directory = output_dir / name
        variants = {}
        for color in PALETTES:
            webm, poster = directory / f'{color}.webm', directory / f'{color}.png'
            if not webm.is_file() or not poster.is_file():
                continue
            video_stat, poster_stat = webm.stat(), poster.stat()
            variants[color] = {
                'webm': webm.relative_to(output_dir).as_posix(),
                'poster': poster.relative_to(output_dir).as_posix(),
                'bytes': video_stat.st_size,
                'version': f'{video_stat.st_mtime_ns}-{poster_stat.st_mtime_ns}',
            }
        metadata = _metadata(effect, directory, bool(variants))
        if effect.role not in ('effect', 'anchor'):
            raise ValueError(f'{name}: invalid role {effect.role!r}')
        if effect.default_color not in PALETTES:
            raise ValueError(f'{name}: unknown default color {effect.default_color!r}')
        effects.append({
            'id': name, 'title': effect.title or name.replace('-', ' ').title(),
            'description': effect.description,
            'kind': 'loop' if metadata['loop'] else 'one-shot',
            'role': effect.role, 'tags': list(effect.tags),
            'default_color': 'radiant' if effect.role == 'anchor' and 'radiant' in variants
                             else effect.default_color,
            **{key: metadata[key] for key in ('duration', 'fps', 'frames', 'size', 'cue_time')},
            'variants': variants,
            **({'pairing': metadata['pairing']} if 'pairing' in metadata else {}),
        })
    by_id = {effect['id']: effect for effect in effects}
    for entry in effects:
        if 'pairing' in entry:
            for partner in entry['pairing']['effects']:
                if partner not in by_id or partner == entry['id']:
                    raise ValueError(f"{entry['id']}: unknown or self-referencing paired effect {partner!r}")
    sequences = []
    for name, sequence in SEQUENCES.items():
        steps = []
        colors = set(PALETTES)
        for phase in ('opening', 'looping', 'closing'):
            reference = getattr(sequence, phase)
            if reference not in by_id:
                raise ValueError(f'{name}: unknown {phase} effect {reference!r}')
            expected_loop = phase == 'looping'
            if (EFFECTS[reference].loop != expected_loop or
                    (by_id[reference]['kind'] == 'loop') != expected_loop):
                raise ValueError(f'{name}: {phase} effect {reference!r} has invalid loop kind')
            steps.append({'phase': phase, 'effect': reference})
            colors.intersection_update(by_id[reference]['variants'])
        if sequence.default_color not in PALETTES:
            raise ValueError(f'{name}: unknown default color {sequence.default_color!r}')
        sequences.append({'id': name, 'title': sequence.title,
                          'description': sequence.description, 'kind': 'sequence',
                          'tags': list(sequence.tags), 'default_color': sequence.default_color,
                          'steps': steps, 'colors': [color for color in PALETTES if color in colors]})
    palettes = []
    for name, palette in PALETTES.items():
        rgb = colorsys.hsv_to_rgb(palette.hue / 360, palette.saturation_scale, 1)
        palettes.append({'id': name, 'label': name.title(),
                         'group': 'Original colors' if name in ORIGINAL_COLORS else
                                  'Themed colors' if name in THEMED_COLORS else 'Damage types',
                         'swatch': '#' + ''.join(f'{round(channel * 255):02x}' for channel in rgb)})
    catalog = {'schema': 1, 'palettes': palettes, 'effects': effects, 'sequences': sequences}
    output_dir.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=output_dir,
                                         prefix='.catalog-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(catalog, stream, indent=2, allow_nan=False)
            stream.write('\n')
        temporary.replace(output_dir / 'catalog.json')
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return catalog
