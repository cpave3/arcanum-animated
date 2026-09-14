"""Register effects here; each master renderer returns a straight-alpha RGBA frame."""
from dataclasses import dataclass
from functools import partial
from typing import Protocol

from PIL import Image

from animation_fx.effects import celestial_revelation, fireball, fireball_stylized, miasma_pool, one_shots, paired_rays, turn_undead, vortex_transitions
from animation_fx.effects import orb_anchor, rift, rift_edge_anchor, rune_anchor, vortex, vortex_black_hole, vortex_open
from animation_fx.palettes import PALETTES, colorize
from animation_fx.recipe import FrameRecipe


class FrameRenderer(Protocol):
    SIZE: int
    FPS: int
    FRAMES: int

    def render(self, frame: int) -> Image.Image: ...


@dataclass(frozen=True)
class AnchorMount:
    effect: str
    size: float
    spacing: float
    left: str
    right: str


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
    paired_effects: tuple[str, ...] = ()
    event_frames: tuple[int, ...] = ()
    event_label: str | None = None
    direction: str | None = None
    mount: AnchorMount | None = None
    anchor_side: str | None = None

    @property
    def pairing(self):
        if not self.paired_effects:
            return None
        return {'effects': list(self.paired_effects), 'event': self.event_label,
                'times': [frame/self.fps for frame in self.event_frames],
                'direction': self.direction}

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
    'celestial-revelation': Effect(celestial_revelation, 'purple', loop=False,
                          cue_frame=celestial_revelation.BLAST_FRAME,
                          poster_frame=celestial_revelation.POSTER_FRAME,
                          default_color='divine', title='Celestial Revelation',
                          description='Light pools around the caster, spirals into a brilliant core, and explodes into a feathered corona.',
                          tags=('aasimar', 'celestial', 'sacred', 'burst', 'radial')),
    'turn-undead': Effect(turn_undead, 'purple', loop=False,
                          cue_frame=turn_undead.BLAST_FRAME, poster_frame=turn_undead.POSTER_FRAME,
                          default_color='divine', title='Turn Undead',
                          description='A sacred seal releases searing caster-centered light and rapid radiant echoes.',
                          tags=('sacred', 'explosion', 'radial')),
    'fireball': Effect(FrameRecipe(fireball.one_shot, SIZE=640, FRAMES=fireball.SHOT_FRAMES),
                       'purple', loop=False, cue_frame=fireball.IMPACT_FRAME, poster_frame=34, default_color='fire',
                       description='A side-on bolt detonates in a top-down blast, leaving fissures and embers that fade.',
                       tags=('projectile', 'explosion', 'scorch')),
    'fireball-stylized': Effect(fireball_stylized, 'purple', loop=False,
                                cue_frame=fireball.IMPACT_FRAME, poster_frame=26, default_color='fire',
                                title='Fireball · Stylized',
                                description='Abstract rounded flame lobes, bold hot-color bands, and flying cinders; the original scorch finish.',
                                tags=('projectile', 'explosion', 'stylized', 'scorch')),
    'fireball-projectile': Effect(
        FrameRecipe(fireball.traveling_projectile, SIZE=640, FRAMES=fireball.PROJECTILE_FRAMES),
        'purple', default_color='fire', title='Fireball · Moving projectile',
        description='Centered right-facing orb and tail. Move and rotate the sprite; do not stretch it.',
        tags=('fireball', 'projectile', 'flight')),
    'fireball-detonation': Effect(
        FrameRecipe(fireball.detonation, SIZE=640, FRAMES=fireball.DETONATION_FRAMES),
        'purple', loop=False, cue_frame=1, poster_frame=21, default_color='fire',
        title='Fireball · Detonation',
        description='Explosion-only opening at the destination, settling into the shared burning ground.',
        tags=('fireball', 'explosion', 'scorch')),
    'fireball-opening': Effect(FrameRecipe(fireball.opening, SIZE=640, FRAMES=fireball.OPEN_FRAMES),
                               'purple', loop=False, cue_frame=fireball.IMPACT_FRAME, poster_frame=34, default_color='fire',
                               description='The same fireball impact settles into persistent burning ground.'),
    'fireball-embers': Effect(FrameRecipe(fireball.embers, SIZE=640, FRAMES=fireball.LOOP_FRAMES),
                              'purple', default_color='fire',
                              description='Scorched fissures breathe with hot coals and drifting embers.'),
    'fireball-closing': Effect(FrameRecipe(fireball.closing, SIZE=640, FRAMES=fireball.CLOSE_FRAMES),
                               'purple', loop=False, cue_frame=0, poster_frame=0, default_color='fire',
                               description='Burning ground cools and its scorch marks disappear.'),
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


edge_mount = AnchorMount('vortex', rift_edge_anchor.MOUNT_SIZE, rift_edge_anchor.MOUNT_SPACING,
                         'rift-edge-anchor-left', 'rift-edge-anchor-right')
for side in ('left', 'right'):
    EFFECTS[f'rift-edge-anchor-{side}'] = Effect(
        FrameRecipe(partial(rift_edge_anchor.render, side=side), SIZE=rift_edge_anchor.SIZE,
                    FPS=rift_edge_anchor.FPS, FRAMES=rift_edge_anchor.FRAMES),
        'gold', role='anchor', default_color='radiant', anchor_side=side,
        title=f'Rift edge · {side.title()} force brace',
        description=f'A native {side}-hand brace with three rune-powered stationary orbs and three small contact lights following its own bank.',
        tags=('anchor', 'rift', 'brace', 'runes', 'sparks', side), mount=edge_mount)


for count in (1, 2, 3):
    EFFECTS[f'ray-cast-{count}'] = Effect(
        FrameRecipe(partial(paired_rays.caster, count=count), SIZE=paired_rays.SIZE,
                    FPS=paired_rays.FPS, FRAMES=paired_rays.caster_frames(count)),
        'purple', loop=False, cue_frame=paired_rays.CHARGE_FRAMES,
        poster_frame=paired_rays.CHARGE_FRAMES+2,
        title=f'Ray caster · {count} release' + ('s' if count > 1 else ''), default_color='fire',
        description=f'Caster-only inward charge and {count} rapid release pulse' + ('s.' if count > 1 else '.'),
        tags=('paired', 'caster', 'beam', 'scorching-ray', 'eldritch-blast'),
        paired_effects=('ray-beam', 'ray-hit'), event_frames=paired_rays.release_frames(count),
        event_label='Release', direction='center')

EFFECTS['ray-hit'] = Effect(
    FrameRecipe(paired_rays.target, SIZE=paired_rays.SIZE, FPS=paired_rays.FPS,
                FRAMES=paired_rays.HIT_FRAMES),
    'purple', loop=False, cue_frame=paired_rays.HIT_FRAME, poster_frame=paired_rays.HIT_FRAME+2,
    title='Ray target · Impact', default_color='fire',
    description='Impact-only burst centered on the target; schedule it at the beam arrival.',
    tags=('paired', 'target', 'beam', 'scorching-ray', 'eldritch-blast'),
    paired_effects=('ray-beam', *(f'ray-cast-{count}' for count in (1, 2, 3))),
    event_frames=(paired_rays.HIT_FRAME,), event_label='Impact', direction='center')


EFFECTS['ray-beam'] = Effect(
    FrameRecipe(paired_rays.beam, SIZE=paired_rays.SIZE, FPS=paired_rays.FPS,
                FRAMES=paired_rays.BEAM_FRAMES),
    'purple', loop=False, cue_frame=paired_rays.BEAM_HIT_FRAME,
    poster_frame=paired_rays.BEAM_HIT_FRAME, title='Ray beam · Stretchable', default_color='fire',
    description='Beam-only, full-width left-to-right ray for Sequencer stretchTo with onlyX.',
    tags=('paired', 'beam', 'stretch', 'scorching-ray', 'eldritch-blast'),
    paired_effects=tuple(f'ray-cast-{count}' for count in (1, 2, 3))+('ray-hit',),
    event_frames=(paired_rays.BEAM_HIT_FRAME,), event_label='Arrival', direction='right')


@dataclass(frozen=True)
class Composition:
    title: str
    caster: str
    beam: str
    impact: str
    default_color: str = 'fire'


COMPOSITIONS = {
    f'ray-composition-{count}': Composition(f'Ray · {count}-shot composition',
                                           f'ray-cast-{count}', 'ray-beam', 'ray-hit')
    for count in (1, 2, 3)
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
    'fireball-impact-sequence': Sequence('Fireball · Detonation and burning ground',
        'fireball-detonation', 'fireball-embers', 'fireball-closing',
        default_color='fire', tags=('fireball', 'scorch')),
    'fireball-sequence': Sequence('Fireball sequence', 'fireball-opening', 'fireball-embers',
                                  'fireball-closing', default_color='fire',
                                  description='Incoming bolt, explosive impact, sustained burning ground, then fade.',
                                  tags=('projectile', 'explosion', 'scorch')),
    'rift-sequence': Sequence('Rift sequence', 'portal-open', 'rift', 'portal-close',
                              tags=('portal',)),
    'vortex-sequence': Sequence('Vortex sequence', 'vortex-opening', 'vortex',
                                'vortex-closing', tags=('vortex',)),
}

@dataclass(frozen=True)
class Journey:
    title: str
    projectile: str
    sequence: str
    travel_duration: float = 1
    default_color: str = 'fire'


JOURNEYS = {
    'fireball-journey': Journey('Fireball · Projectile + burning ground',
                               'fireball-projectile', 'fireball-impact-sequence'),
}


# Palette geometry stays in palettes.py; viewer grouping is presentation only.
ORIGINAL_COLORS = frozenset(('purple', 'gold', 'red', 'orange'))

THEMED_COLORS = frozenset(('divine', 'eldritch'))
