"""Build the viewer manifest from registered effects and completed delivery exports."""
from dataclasses import asdict
import colorsys
import json
import math
from pathlib import Path
import tempfile

from animation_fx.catalog import COMPOSITIONS, EFFECTS, JOURNEYS, ORIGINAL_COLORS, SEQUENCES, THEMED_COLORS
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
            if pairing.get('direction') not in ('right', 'center'):
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
        if effect.anchor_side is not None and (effect.role != 'anchor' or effect.anchor_side not in ('left', 'right')):
            raise ValueError(f'{name}: invalid anchor side')
        if effect.mount is not None:
            targets = set(EFFECTS) | set(SEQUENCES) | set(COMPOSITIONS) | set(JOURNEYS)
            if effect.role != 'anchor' or effect.mount.effect not in targets or effect.mount.effect == name:
                raise ValueError(f'{name}: invalid anchor preview target')
            if any(partner not in EFFECTS or EFFECTS[partner].role != 'anchor'
                   or not EFFECTS[partner].loop for partner in (effect.mount.left, effect.mount.right)):
                raise ValueError(f'{name}: mount partners must be registered looping anchors')
            if (not 15 <= effect.mount.size <= 70 or not 4 <= effect.mount.spacing <= 35):
                raise ValueError(f'{name}: anchor mount is outside the viewer placement range')
        effects.append({
            'id': name, 'title': effect.title or name.replace('-', ' ').title(),
            'description': effect.description,
            'kind': 'loop' if metadata['loop'] else 'one-shot',
            'role': effect.role, 'tags': list(effect.tags),
            'default_color': 'radiant' if effect.role == 'anchor' and 'radiant' in variants
                             else effect.default_color,
            **{key: metadata[key] for key in ('duration', 'fps', 'frames', 'size', 'cue_time')},
            'variants': variants,
            **({'mount': asdict(effect.mount)} if effect.mount is not None else {}),
            **({'anchor_side': effect.anchor_side} if effect.anchor_side is not None else {}),
            **({'pairing': metadata['pairing']} if 'pairing' in metadata else {}),
        })
    by_id = {effect['id']: effect for effect in effects}
    for entry in effects:
        if 'mount' in entry and any(by_id[entry['mount'][side]]['kind'] != 'loop' for side in ('left', 'right')):
            raise ValueError(f"{entry['id']}: mount partners must be exported as looping anchors")
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
    compositions = []
    for name, recipe in COMPOSITIONS.items():
        references = (recipe.caster, recipe.beam, recipe.impact)
        if any(ref not in by_id or by_id[ref]['kind'] != 'one-shot' for ref in references):
            raise ValueError(f'{name}: composition components must reference registered one-shots')
        caster, beam, impact = (by_id[ref] for ref in references)
        if (not caster.get('pairing') or beam['cue_time'] is None or impact['cue_time'] is None):
            raise ValueError(f'{name}: composition requires release, arrival and impact timing')
        if recipe.default_color not in PALETTES:
            raise ValueError(f'{name}: unknown default color')
        tracks = [{'role': 'caster', 'effect': recipe.caster, 'start': 0}]
        for release in caster['pairing']['times']:
            impact_start = release + beam['cue_time'] - impact['cue_time']
            if impact_start < 0:
                raise ValueError(f'{name}: impact would start before the composition')
            tracks.extend([{'role': 'beam', 'effect': recipe.beam, 'start': release},
                           {'role': 'target', 'effect': recipe.impact, 'start': impact_start}])
        colors = set.intersection(*(set(by_id[ref]['variants']) for ref in references))
        compositions.append({'id': name, 'kind': 'composition', 'title': recipe.title,
            'description': 'Caster charge, stretched connecting rays and independently overlapping target impacts.',
            'tags': ['paired', 'ray', 'scorching-ray', 'eldritch-blast'],
            'default_color': recipe.default_color,
            'colors': [color for color in PALETTES if color in colors], 'tracks': tracks,
            'duration': max(track['start']+by_id[track['effect']]['duration'] for track in tracks)})
    journeys = []
    by_sequence = {sequence['id']: sequence for sequence in sequences}
    for name, recipe in JOURNEYS.items():
        if recipe.projectile not in by_id or by_id[recipe.projectile]['kind'] != 'loop':
            raise ValueError(f'{name}: journey requires a registered looping projectile')
        if recipe.sequence not in by_sequence:
            raise ValueError(f'{name}: unknown ground sequence')
        if not math.isfinite(recipe.travel_duration) or recipe.travel_duration <= 0:
            raise ValueError(f'{name}: travel duration must be positive')
        if recipe.default_color not in PALETTES:
            raise ValueError(f'{name}: unknown default color')
        sequence = by_sequence[recipe.sequence]
        colors = set(sequence['colors']) & set(by_id[recipe.projectile]['variants'])
        journeys.append({'id': name, 'kind': 'journey', 'title': recipe.title,
            'description': 'Move a twisting fireball to To, detonate, then burn until closed or timed out.',
            'tags': ['fireball', 'projectile', 'persistent', 'scorch'],
            'default_color': recipe.default_color,
            'colors': [color for color in PALETTES if color in colors],
            'projectile': recipe.projectile, 'travel_duration': recipe.travel_duration,
            'steps': sequence['steps']})
    palettes = []
    for name, palette in PALETTES.items():
        rgb = colorsys.hsv_to_rgb(palette.hue / 360, palette.saturation_scale, 1)
        palettes.append({'id': name, 'label': name.title(),
                         'group': 'Original colors' if name in ORIGINAL_COLORS else
                                  'Themed colors' if name in THEMED_COLORS else 'Damage types',
                         'swatch': '#' + ''.join(f'{round(channel * 255):02x}' for channel in rgb)})
    catalog = {'schema': 1, 'palettes': palettes, 'effects': effects, 'sequences': sequences,
               'compositions': compositions, 'journeys': journeys}
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
