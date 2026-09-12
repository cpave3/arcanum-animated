import json
from dataclasses import replace
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from animation_fx.catalog import COMPOSITIONS, EFFECTS, JOURNEYS, SEQUENCES, Effect
from animation_fx.viewer_catalog import build_viewer_catalog
import render

ROOT = Path(__file__).resolve().parents[1]


class ViewerCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name)

    def export(self, name, colors=('purple',), **overrides):
        directory = self.output / name
        directory.mkdir(exist_ok=True)
        effect = EFFECTS[name]
        metadata = {'loop': effect.loop, 'fps': 20, 'frames': 40,
                    'duration': 2, 'size': 128, 'cue_time': .5}
        metadata.update(overrides)
        (directory / 'effect.json').write_text(json.dumps(metadata))
        for color in colors:
            (directory / f'{color}.webm').write_bytes(b'video')
            (directory / f'{color}.png').write_bytes(b'poster')

    def build(self):
        catalog = build_viewer_catalog(self.output)
        self.assertEqual(catalog, json.loads((self.output / 'catalog.json').read_text()))
        return catalog

    def test_new_registration_appears_with_delivery_metadata_and_stable_version(self):
        synthetic = Effect(EFFECTS['rift'].renderer, 'purple')
        with patch.dict(EFFECTS, {'synthetic-effect': synthetic}):
            self.export('synthetic-effect')
            catalog = self.build()
            entry = next(e for e in catalog['effects'] if e['id'] == 'synthetic-effect')
            self.assertEqual(entry['title'], 'Synthetic Effect')
            self.assertEqual(entry['role'], 'effect')
            self.assertEqual(entry['default_color'], 'purple')
            self.assertEqual(entry['tags'], [])
            self.assertEqual([entry[k] for k in ('duration', 'fps', 'frames', 'size', 'cue_time')],
                             [2, 20, 40, 128, .5])
            variant = entry['variants']['purple']
            self.assertEqual(variant['webm'], 'synthetic-effect/purple.webm')
            self.assertEqual(variant['poster'], 'synthetic-effect/purple.png')
            self.assertEqual(variant['bytes'], 5)
            self.assertTrue(variant['version'])
            self.assertEqual(catalog, self.build())
            self.assertEqual(catalog['schema'], 1)
            self.assertTrue(all(set(p) == {'id', 'label', 'group', 'swatch'}
                                for p in catalog['palettes']))

    def test_partial_variants_omitted_but_unrendered_effects_remain(self):
        self.export('rift', ('purple', 'red'))
        (self.output / 'rift/red.png').unlink()
        (self.output / 'rift/gold.png').write_bytes(b'poster only')
        catalog = self.build()
        entries = {e['id']: e for e in catalog['effects']}
        self.assertEqual(set(entries), set(EFFECTS))
        self.assertEqual(set(entries['rift']['variants']), {'purple'})
        missing = entries['teleport-arrival']
        self.assertEqual(missing['variants'], {})
        effect = EFFECTS['teleport-arrival']
        self.assertEqual(missing['size'], effect.size)
        self.assertEqual(missing['duration'], effect.frames / effect.fps)
        self.assertEqual(missing['cue_time'], effect.cue_frame / effect.fps)
        self.assertEqual(missing['kind'], 'one-shot')

    def test_sequence_colors_intersect_all_three_steps_and_anchor_default(self):
        self.export('portal-open', ('purple', 'red'))
        self.export('rift', ('purple', 'gold'))
        self.export('portal-close', ('purple', 'red', 'gold'))
        self.export('rune-anchor', ('radiant',))
        catalog = self.build()
        sequences = {s['id']: s for s in catalog['sequences']}
        self.assertEqual(set(sequences), set(SEQUENCES))
        self.assertEqual(sequences['rift-sequence']['colors'], ['purple'])
        self.assertEqual(sequences['vortex-sequence']['colors'], [])
        self.assertEqual(sequences['rift-sequence']['steps'], [
            {'phase': 'opening', 'effect': 'portal-open'},
            {'phase': 'looping', 'effect': 'rift'},
            {'phase': 'closing', 'effect': 'portal-close'}])
        anchor = next(e for e in catalog['effects'] if e['id'] == 'rune-anchor')
        self.assertEqual(anchor['default_color'], 'radiant')

    def test_fireball_entries_and_sequence_reach_viewer_catalog(self):
        catalog = self.build()
        entries = {entry['id']: entry for entry in catalog['effects']}
        for name, frames, kind, cue in [
                ('fireball', 209, 'one-shot', 14/30),
                ('fireball-opening', 120, 'one-shot', 14/30),
                ('fireball-embers', 120, 'loop', None),
                ('fireball-closing', 90, 'one-shot', 0)]:
            with self.subTest(effect=name):
                entry = entries[name]
                self.assertEqual([entry[key] for key in
                                  ('frames', 'fps', 'size', 'kind', 'cue_time', 'default_color')],
                                 [frames, 30, 640, kind, cue, 'fire'])
                self.assertEqual(entry['duration'], frames/30)
                self.assertTrue(entry['description'])
        for name in ('fireball-opening', 'fireball-embers', 'fireball-closing'):
            self.export(name, ('fire', 'cold'))
        sequence = next(s for s in self.build()['sequences'] if s['id'] == 'fireball-sequence')
        self.assertEqual(sequence['default_color'], 'fire')
        self.assertEqual(set(sequence['colors']), {'fire', 'cold'})
        self.assertEqual(sequence['tags'], ['projectile', 'explosion', 'scorch'])
        self.assertEqual(sequence['steps'], [
            {'phase': 'opening', 'effect': 'fireball-opening'},
            {'phase': 'looping', 'effect': 'fireball-embers'},
            {'phase': 'closing', 'effect': 'fireball-closing'}])

    def test_fireball_journey_metadata_and_four_component_palette_intersection(self):
        names = ('fireball-projectile', 'fireball-detonation', 'fireball-embers', 'fireball-closing')
        catalog = self.build()
        entries = {entry['id']: entry for entry in catalog['effects']}
        for name, frames, kind, cue in [
                ('fireball-projectile', 60, 'loop', None),
                ('fireball-detonation', 107, 'one-shot', 1/30)]:
            self.assertEqual([entries[name][key] for key in
                              ('frames', 'fps', 'size', 'kind', 'cue_time', 'default_color')],
                             [frames, 30, 640, kind, cue, 'fire'])
            self.assertEqual(entries[name]['duration'], frames/30)
        self.assertEqual({entry['id'] for entry in catalog['journeys']}, set(JOURNEYS))
        journey = next(j for j in catalog['journeys'] if j['id'] == 'fireball-journey')
        self.assertEqual(journey['kind'], 'journey')
        self.assertEqual(journey['title'], 'Fireball · Projectile + burning ground')
        self.assertEqual(journey['projectile'], names[0])
        self.assertEqual(journey['travel_duration'], 1)
        self.assertEqual(journey['default_color'], 'fire')
        self.assertEqual(journey['colors'], [])
        steps = [{'phase': phase, 'effect': name} for phase, name in
                 zip(('opening', 'looping', 'closing'), names[1:])]
        self.assertEqual(journey['steps'], steps)
        sequence = next(s for s in catalog['sequences'] if s['id'] == 'fireball-impact-sequence')
        self.assertEqual(sequence['steps'], steps)
        self.assertEqual(sequence['default_color'], 'fire')
        for name in names:
            self.export(name, ('fire', 'cold'))
        journey = next(j for j in self.build()['journeys'] if j['id'] == 'fireball-journey')
        self.assertEqual(set(journey['colors']), {'fire', 'cold'})
        for name in names:
            for extension in ('webm', 'png'):
                with self.subTest(effect=name, missing=extension):
                    path = self.output / name / f'cold.{extension}'
                    content = path.read_bytes()
                    path.unlink()
                    journey = next(j for j in self.build()['journeys'] if j['id'] == 'fireball-journey')
                    self.assertEqual(journey['colors'], ['fire'])
                    path.write_bytes(content)

    def test_invalid_journey_references_and_settings_fail_atomically(self):
        self.build()
        before = (self.output / 'catalog.json').read_bytes()
        invalid = [({'projectile': 'missing'}, 'looping projectile'),
                   ({'projectile': 'fireball'}, 'looping projectile'),
                   ({'sequence': 'missing'}, 'unknown ground sequence'),
                   ({'sequence': 'fireball-embers'}, 'unknown ground sequence'),
                   ({'default_color': 'missing'}, 'unknown default color')]
        invalid.extend(({'travel_duration': duration}, 'travel duration')
                       for duration in (0, -1, float('nan'), float('inf')))
        for changes, message in invalid:
            with self.subTest(changes=changes), patch.dict(JOURNEYS, {
                    'fireball-journey': replace(JOURNEYS['fireball-journey'], **changes)}):
                with self.assertRaisesRegex(ValueError, message):
                    self.build()
            self.assertEqual((self.output / 'catalog.json').read_bytes(), before)
        self.export('fireball-projectile', loop=False)
        with self.assertRaisesRegex(ValueError, 'looping projectile'):
            self.build()
        self.assertEqual((self.output / 'catalog.json').read_bytes(), before)

    def test_unknown_sequence_reference_and_wrong_loop_kind_fail_atomically(self):
        self.build()
        before = (self.output / 'catalog.json').read_bytes()
        for changes, message in [({'opening': 'missing'}, 'unknown opening effect'),
                                 ({'opening': 'rift'}, 'invalid loop kind'),
                                 ({'looping': 'portal-open'}, 'invalid loop kind')]:
            with self.subTest(changes=changes), patch.dict(SEQUENCES, {
                    'rift-sequence': replace(SEQUENCES['rift-sequence'], **changes)}):
                with self.assertRaisesRegex(ValueError, message):
                    self.build()
            self.assertEqual((self.output / 'catalog.json').read_bytes(), before)

    def test_invalid_delivery_metadata_is_not_silently_replaced(self):
        for overrides in ({'size': 0}, {'loop': 'yes'}, {'cue_time': 9},
                          {'fps': float('nan')}, {'duration': 99}):
            with self.subTest(overrides=overrides):
                self.export('rift', **overrides)
                with self.assertRaisesRegex(ValueError, 'effect.json: invalid delivery metadata'):
                    self.build()
        (self.output / 'rift/effect.json').write_text('{bad json')
        with self.assertRaisesRegex(ValueError, 'invalid delivery metadata'):
            self.build()
        (self.output / 'rift/effect.json').unlink()
        with self.assertRaisesRegex(ValueError, 'missing delivery metadata'):
            self.build()

    def test_sequence_rejects_exported_loop_kind_mismatch(self):
        self.export('portal-open', loop=True)
        with self.assertRaisesRegex(ValueError, 'invalid loop kind'):
            self.build()

    def export_paired_components(self):
        for count in (1, 2, 3):
            pairing = {'effects': ['ray-beam', 'ray-hit'], 'event': 'Release',
                       'times': [(12+10*i)/60 for i in range(count)], 'direction': 'center'}
            self.export(f'ray-cast-{count}', ('fire', 'eldritch'), fps=60,
                        frames=36+10*(count-1), duration=(36+10*(count-1))/60,
                        cue_time=12/60, pairing=pairing)
        hit_pairing = {'effects': ['ray-beam', 'ray-cast-1', 'ray-cast-2', 'ray-cast-3'],
                       'event': 'Impact', 'times': [1/60], 'direction': 'center'}
        self.export('ray-hit', ('fire', 'eldritch'), fps=60, frames=40,
                    duration=40/60, cue_time=1/60, pairing=hit_pairing)
        self.export('ray-beam', ('fire', 'eldritch'), fps=60, frames=9,
                    duration=9/60, cue_time=4/60, pairing={
                        'effects': ['ray-cast-1', 'ray-cast-2', 'ray-cast-3', 'ray-hit'],
                        'event': 'Arrival', 'times': [4/60], 'direction': 'right'})

    def test_paired_entries_use_exported_local_clock_and_themed_palettes(self):
        self.export_paired_components()
        catalog = self.build()
        entries = {entry['id']: entry for entry in catalog['effects']}
        for name in ('ray-beam', 'ray-cast-1', 'ray-cast-2', 'ray-cast-3', 'ray-hit'):
            exported = json.loads((self.output / name / 'effect.json').read_text())
            self.assertEqual(entries[name]['pairing'], exported['pairing'])
            self.assertNotEqual(entries[name]['pairing']['times'], EFFECTS[name].pairing['times'])
            self.assertEqual(set(entries[name]['variants']), {'fire', 'eldritch'})
            for partner in entries[name]['pairing']['effects']:
                self.assertIn('eldritch', entries[partner]['variants'])
        palettes = {palette['id']: palette for palette in catalog['palettes']}
        self.assertEqual(len(palettes), 17)
        for name in ('divine', 'eldritch'):
            self.assertEqual(palettes[name]['group'], 'Themed colors')
            self.assertEqual(palettes[name]['label'], name.title())

    def test_composition_tracks_use_exported_cues_and_maximum_end(self):
        self.export_paired_components()
        catalog = self.build()
        entries = {entry['id']: entry for entry in catalog['effects']}
        self.assertIsInstance(catalog['compositions'], list)
        self.assertEqual({c['id'] for c in catalog['compositions']},
                         {f'ray-composition-{i}' for i in (1, 2, 3)})
        for count, composition in enumerate(catalog['compositions'], 1):
            caster = entries[f'ray-cast-{count}']
            tracks = [{'role': 'caster', 'effect': caster['id'], 'start': 0}]
            for release in caster['pairing']['times']:
                tracks.extend([
                    {'role': 'beam', 'effect': 'ray-beam', 'start': release},
                    {'role': 'target', 'effect': 'ray-hit', 'start':
                     release+entries['ray-beam']['cue_time']-entries['ray-hit']['cue_time']}])
            self.assertEqual(composition['tracks'], tracks)
            self.assertEqual(composition['duration'], max(
                t['start']+entries[t['effect']]['duration'] for t in tracks))
            self.assertEqual(set(composition['colors']), {'fire', 'eldritch'})
        (self.output / 'ray-beam/eldritch.png').unlink()
        for composition in self.build()['compositions']:
            self.assertEqual(composition['colors'], ['fire'])
        (self.output / 'ray-hit/fire.png').unlink()
        for composition in self.build()['compositions']:
            self.assertEqual(composition['colors'], [])

    def test_composition_invalid_references_leave_catalog_intact(self):
        self.build()
        before = (self.output / 'catalog.json').read_bytes()
        for role in ('caster', 'beam', 'impact'):
            for reference in ('missing', 'rift'):
                with self.subTest(role=role, reference=reference), patch.dict(COMPOSITIONS, {
                        'ray-composition-1': replace(COMPOSITIONS['ray-composition-1'],
                                                     **{role: reference})}):
                    with self.assertRaisesRegex(ValueError, 'composition components'):
                        self.build()
                self.assertEqual((self.output / 'catalog.json').read_bytes(), before)

    def test_invalid_pairing_metadata_fails_without_replacing_catalog(self):
        pairing = {'effects': ['ray-beam', 'ray-hit'], 'event': 'Release',
                   'times': [.4], 'direction': 'center'}
        self.export('ray-cast-1', pairing=pairing)
        self.build()
        before = (self.output / 'catalog.json').read_bytes()
        invalid = [None, {}, *({**pairing, 'times': times} for times in
                   ([], [-.1], [2], [float('nan')], [float('inf')], [True], [.7, .4], [.4, .4])),
                   {**pairing, 'effects': []}, {**pairing, 'effects': ['missing']},
                   {**pairing, 'effects': ['ray-cast-1']},
                   {**pairing, 'direction': 'left'}]
        for value in invalid:
            with self.subTest(pairing=value):
                self.export('ray-cast-1', pairing=value)
                with self.assertRaises(ValueError):
                    self.build()
                self.assertEqual((self.output / 'catalog.json').read_bytes(), before)
        self.export('ray-cast-1')
        with self.assertRaisesRegex(ValueError, 'missing pairing metadata'):
            self.build()
        self.assertEqual((self.output / 'catalog.json').read_bytes(), before)

    def test_cli_catalog_only_uses_exports_without_rendering(self):
        self.export('rift')
        before = (self.output / 'rift/purple.webm').stat().st_mtime_ns
        result = subprocess.run([sys.executable, str(ROOT / 'render.py'), '--catalog-only',
                                 '--output', str(self.output), '--profile', 'high',
                                 '--effect', 'one-shots', '--color', 'red'],
                                check=True, capture_output=True, text=True)
        self.assertIn('Catalog ready:', result.stdout)
        catalog = json.loads((self.output / 'catalog.json').read_text())
        self.assertEqual(len(catalog['effects']), len(EFFECTS))
        self.assertEqual((self.output / 'rift/purple.webm').stat().st_mtime_ns, before)
        self.assertFalse((self.output / 'teleport-arrival').exists())

    def test_cli_refreshes_after_each_successful_export(self):
        calls = []

        def export(effect, colors, directory, profile, *, progress=None):
            calls.append(('export', directory.name))
            pairing = {'pairing': effect.pairing} if effect.pairing is not None else {}
            self.export(directory.name, colors, fps=effect.fps, frames=effect.frames,
                        duration=effect.frames/effect.fps,
                        cue_time=None if effect.cue_frame is None else effect.cue_frame/effect.fps,
                        **pairing)

        def build(output):
            calls.append(('catalog', output))
            return build_viewer_catalog(output)

        with patch.object(sys, 'argv', ['render.py', '--effect', 'one-shots', '--color',
                                       'purple', '--output', str(self.output)]), \
                patch.object(render, 'export_effect', side_effect=export), \
                patch.object(render, 'build_viewer_catalog', side_effect=build):
            render.main()
        count = sum(not effect.loop for effect in EFFECTS.values())
        self.assertEqual([kind for kind, _ in calls], ['export', 'catalog'] * count)
        catalog = json.loads((self.output / 'catalog.json').read_text())
        for effect in catalog['effects']:
            self.assertEqual(bool(effect['variants']), not EFFECTS[effect['id']].loop)


if __name__ == '__main__':
    unittest.main()
