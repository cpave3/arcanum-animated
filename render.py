"""Generate a colorway collection: python3 render.py --effect all --color all."""
import argparse
import sys
from pathlib import Path

from animation_fx.catalog import EFFECTS
from animation_fx.export import ExportProgress, export_effect
from animation_fx.palettes import PALETTES
from animation_fx.profiles import PROFILES
from animation_fx.viewer_catalog import build_viewer_catalog


class RenderProgress:
    """Throttle frame updates, but always show phase transitions and endpoints."""

    def __init__(self, name, index, total):
        self.label = f'[{index}/{total}] {name}'
        self.last_elapsed = None
        self.last_phase = None
        self.line_open = False
        self.width = 0

    def __call__(self, event: ExportProgress):
        if (event.phase == self.last_phase and event.frame != event.total
                and self.last_elapsed is not None and event.elapsed-self.last_elapsed < .5):
            return
        self.last_elapsed = event.elapsed
        self.last_phase = event.phase
        percent = 100 * event.frame / event.total
        text = (f'{self.label} {event.phase}: frame {event.frame}/{event.total} '
                f'({percent:.0f}%) | elapsed {event.elapsed:.1f}s')
        if event.phase == 'rendering':
            eta = 'estimating' if event.eta is None else f'{event.eta:.1f}s'
            text += f' | frame ETA {eta}'
        elif event.phase == 'encoding':
            text += ' | waiting for encoders; output not published'
        elif event.phase == 'finalizing':
            text += ' | publishing files'
        else:
            text += ' | output published'
        if sys.stderr.isatty():
            self.width = max(self.width, len(text))
            print('\r' + text.ljust(self.width), end='', file=sys.stderr, flush=True)
            self.line_open = True
            if event.phase == 'complete':
                self.close()
        else:
            print(text, file=sys.stderr, flush=True)

    def close(self):
        if self.line_open:
            print(file=sys.stderr, flush=True)
            self.line_open = False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--effect', choices=['all', 'one-shots', *EFFECTS], default='all')
    parser.add_argument('--color', choices=['all', *PALETTES], default='all')
    parser.add_argument('--profile', choices=PROFILES, default='vtt')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--catalog-only', action='store_true',
                        help='Refresh catalog.json from existing exports without rendering')
    args = parser.parse_args()
    output = args.output or Path(__file__).resolve().parent / ('assets' if args.profile == 'vtt' else 'assets-high')
    if args.catalog_only:
        build_viewer_catalog(output)
        print(f'Catalog ready: {(output / "catalog.json").resolve()}', flush=True)
        return
    if args.effect == 'one-shots':
        effects = {name: effect for name, effect in EFFECTS.items() if not effect.loop}
    else:
        effects = EFFECTS if args.effect == 'all' else {args.effect: EFFECTS[args.effect]}
    colors = list(PALETTES) if args.color == 'all' else [args.color]
    for index, (name, effect) in enumerate(effects.items(), 1):
        progress = RenderProgress(name, index, len(effects))
        try:
            export_effect(effect, colors, output / name, PROFILES[args.profile], progress=progress)
        finally:
            progress.close()
        build_viewer_catalog(output)
    print(f'Collection ready: {output.resolve()}', flush=True)


if __name__ == '__main__':
    main()
