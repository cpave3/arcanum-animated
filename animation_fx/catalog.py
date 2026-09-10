"""Register effects here; each master renderer returns a straight-alpha RGBA frame."""
from dataclasses import dataclass
from typing import Protocol

from PIL import Image

from animation_fx.effects import miasma_pool, one_shots, vortex_transitions
from animation_fx.effects import orb_anchor, rift, rune_anchor, vortex, vortex_black_hole, vortex_open
from animation_fx.palettes import PALETTES, colorize
from animation_fx.recipe import FrameRecipe


class FrameRenderer(Protocol):
    SIZE: int
    FPS: int
    FRAMES: int

    def render(self, frame: int) -> Image.Image: ...


@dataclass(frozen=True)
class Effect:
    renderer: FrameRenderer
    source_color: str
    loop: bool = True
    cue_frame: int | None = None
    poster_frame: int = 0
    title: str | None = None
    description: str = ''
    role: str = 'effect'
    tags: tuple[str, ...] = ()
    default_color: str = 'purple'

    @property
    def size(self):
        return self.renderer.SIZE

    @property
    def fps(self):
        return self.renderer.FPS

    @property
    def frames(self):
        return self.renderer.FRAMES

    def master(self, frame: int) -> Image.Image:
        index = frame % self.frames if self.loop else min(self.frames-1, max(0, frame))
        return self.renderer.render(index)

    def render(self, frame: int, color: str) -> Image.Image:
        return colorize(self.master(frame), PALETTES[self.source_color], PALETTES[color])


EFFECTS = {
    'rift': Effect(rift, 'purple', description='Neon slit with an opaque dark tear.'),
    'miasma-pool': Effect(miasma_pool, 'purple', description='Smoky ground pools with billowing vents.'),
    'vortex': Effect(vortex, 'purple', description='Layered outward spirals with a shimmering core.'),
    'vortex-open': Effect(vortex_open, 'purple', description='Outward spirals with a transparent center.'),
    'vortex-black-hole': Effect(vortex_black_hole, 'purple', description='Circular dark core with a photon ring and orbiting light.'),
    'orb-anchor': Effect(orb_anchor, 'gold', role='anchor',
                         description='Glowing orb with lightning.', tags=('anchor',)),
    'rune-anchor': Effect(rune_anchor, 'gold', role='anchor',
                          description='Rune brackets with sparks.', tags=('anchor',)),
    'teleport-departure': Effect(FrameRecipe(one_shots.teleport_departure), 'purple',
                    loop=False, cue_frame=30, poster_frame=24,
                    description='Power gathers inward, flashes, then scatters into sparks.'),
    'teleport-arrival': Effect(FrameRecipe(one_shots.teleport_arrival), 'purple',
                    loop=False, cue_frame=12, poster_frame=12,
                    description='An arrival flash expands into rings and curling wisps.'),
    'impact-burst': Effect(FrameRecipe(one_shots.impact_burst), 'purple',
                    loop=False, cue_frame=7, poster_frame=7,
                    description='A sharp flash, traveling sparks, and an expanding shock ring.'),
    'ground-eruption': Effect(FrameRecipe(one_shots.ground_eruption), 'purple',
                    loop=False, cue_frame=25, poster_frame=25,
                    description='Top-down branching cracks vent energy through the floor.'),
    'casting-release': Effect(FrameRecipe(one_shots.casting_release), 'purple',
                    loop=False, cue_frame=33, poster_frame=25,
                    description='Varied runes gather power, then discharge in a burst.'),
    'dispel': Effect(FrameRecipe(one_shots.dispel), 'purple',
                    loop=False, cue_frame=20, poster_frame=24,
                    description='A rune ward fractures into drifting glyph fragments.'),
    'portal-open': Effect(FrameRecipe(one_shots.portal_open), 'purple',
                    loop=False, cue_frame=59, poster_frame=59),
    'vortex-opening': Effect(FrameRecipe(vortex_transitions.opening, SIZE=640), 'purple',
                             loop=False, cue_frame=59, poster_frame=59),
    'vortex-closing': Effect(FrameRecipe(vortex_transitions.closing, SIZE=640), 'purple',
                             loop=False, cue_frame=0, poster_frame=0),
    'portal-close': Effect(FrameRecipe(one_shots.portal_close), 'purple',
                    loop=False, cue_frame=0, poster_frame=0),
}


@dataclass(frozen=True)
class Sequence:
    title: str
    opening: str
    looping: str
    closing: str
    description: str = 'Open, sustain the loop, then close at a loop boundary.'
    tags: tuple[str, ...] = ()
    default_color: str = 'purple'


SEQUENCES = {
    'rift-sequence': Sequence('Rift sequence', 'portal-open', 'rift', 'portal-close',
                              tags=('portal',)),
    'vortex-sequence': Sequence('Vortex sequence', 'vortex-opening', 'vortex',
                                'vortex-closing', tags=('vortex',)),
}

# Palette geometry stays in palettes.py; viewer grouping is presentation only.
ORIGINAL_COLORS = frozenset(('purple', 'gold', 'red', 'orange'))
