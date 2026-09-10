"""Generate a colorway collection: python3 render.py --effect all --color all."""
import argparse
from pathlib import Path

from animation_fx.catalog import EFFECTS
from animation_fx.export import export_effect
from animation_fx.palettes import PALETTES
from animation_fx.profiles import PROFILES
from animation_fx.viewer_catalog import build_viewer_catalog


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
    for name, effect in effects.items():
        print(f'Rendering {name} ({args.profile}): {", ".join(colors)}', flush=True)
        export_effect(effect, colors, output / name, PROFILES[args.profile])
        build_viewer_catalog(output)
    print(f'Collection ready: {output.resolve()}', flush=True)


if __name__ == '__main__':
    main()
