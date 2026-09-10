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
    'rift': Effect(rift, 'purple'),
    'miasma-pool': Effect(miasma_pool, 'purple'),
    'vortex': Effect(vortex, 'purple'),
    'vortex-open': Effect(vortex_open, 'purple'),
    'vortex-black-hole': Effect(vortex_black_hole, 'purple'),
    'orb-anchor': Effect(orb_anchor, 'gold'),
    'rune-anchor': Effect(rune_anchor, 'gold'),
    'teleport-departure': Effect(FrameRecipe(one_shots.teleport_departure), 'purple',
                    loop=False, cue_frame=30, poster_frame=24),
    'teleport-arrival': Effect(FrameRecipe(one_shots.teleport_arrival), 'purple',
                    loop=False, cue_frame=12, poster_frame=12),
    'impact-burst': Effect(FrameRecipe(one_shots.impact_burst), 'purple',
                    loop=False, cue_frame=7, poster_frame=7),
    'ground-eruption': Effect(FrameRecipe(one_shots.ground_eruption), 'purple',
                    loop=False, cue_frame=25, poster_frame=25),
    'casting-release': Effect(FrameRecipe(one_shots.casting_release), 'purple',
                    loop=False, cue_frame=33, poster_frame=25),
    'dispel': Effect(FrameRecipe(one_shots.dispel), 'purple',
                    loop=False, cue_frame=20, poster_frame=24),
    'portal-open': Effect(FrameRecipe(one_shots.portal_open), 'purple',
                    loop=False, cue_frame=59, poster_frame=59),
    'vortex-opening': Effect(FrameRecipe(vortex_transitions.opening, SIZE=640), 'purple',
                             loop=False, cue_frame=59, poster_frame=59),
    'vortex-closing': Effect(FrameRecipe(vortex_transitions.closing, SIZE=640), 'purple',
                             loop=False, cue_frame=0, poster_frame=0),
    'portal-close': Effect(FrameRecipe(one_shots.portal_close), 'purple',
                    loop=False, cue_frame=0, poster_frame=0),
}
