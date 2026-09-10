"""Named glyph geometry, transforms, fracture motion, and binding brackets."""
import math

GLYPHS = {
    'spire': (((-8, 8), (0, -9), (8, 8)), ((-5, 2), (5, 2)), ((0, -9), (0, -14))),
    'fork': (((-8, -8), (0, 0), (-8, 8)), ((0, -11), (0, 11)), ((0, 0), (8, -6))),
    'eye': (((0, -11), (9, 0), (0, 11), (-9, 0), (0, -11)), ((-4, 0), (4, 0))),
    'chalice': (((-8, -7), (0, -1), (8, -7)), ((0, -1), (0, 11)), ((-7, 6), (7, 6))),
    'gate': (((-8, -9), (-8, 7), (0, 11), (8, 7), (8, -9)), ((-8, -1), (8, -1))),
    'hourglass': (((-8, -10), (8, -10), (-8, 10), (8, 10), (-8, -10)),),
    'branch': (((0, -12), (0, 12)), ((-8, -5), (0, 2), (8, -5)), ((0, -3), (7, -10))),
    'hook': (((-7, -10), (7, -10), (7, 1), (-5, 1), (-5, 10), (4, 10)),),
}
ANCHOR_GLYPHS = ('spire', 'fork', 'eye', 'chalice', 'gate')


def draw_rune(draw, glyph, *, center, size=1, rotation=0, opacity=1, scale=1,
              color=(169, 55, 255), highlight=(236, 199, 255),
              outer_alpha=255, inner_alpha=255, fragmentation=0):
    """Draw any named rune. Fragmentation separates its strokes into drifting shards."""
    cosine, sine = math.cos(rotation), math.sin(rotation)
    for index, stroke in enumerate(GLYPHS[glyph]):
        if fragmentation:
            pieces = [stroke[i:i+2] for i in range(len(stroke)-1)]
        else:
            pieces = [stroke]
        for part, piece in enumerate(pieces):
            angle = index*2.4 + part*1.7
            dx = 16*fragmentation*math.cos(angle)
            dy = 16*fragmentation*math.sin(angle)
            points = [((center[0] + size*((x+dx)*cosine-(y+dy)*sine))*scale,
                       (center[1] + size*((x+dx)*sine+(y+dy)*cosine))*scale) for x,y in piece]
            draw.line(points, fill=(*color, int(outer_alpha*opacity)), width=3*scale)
            draw.line(points, fill=(*highlight, int(inner_alpha*opacity)), width=scale)


def draw_brackets(draw, *, center=(160, 160), height=190, gap=25, bow=8, scale=2,
                  color=(255, 183, 44), highlight=(255, 225, 126)):
    for side in (-1, 1):
        points = [((center[0] + side*(gap+bow*math.sin(math.pi*i/40)))*scale,
                   (center[1]-height/2+height*i/40)*scale) for i in range(41)]
        draw.line(points, fill=(*color, 215), width=2*scale)
        for y, direction in [(center[1]-height/2, 1), (center[1]+height/2, -1)]:
            draw.line([((center[0]+side*gap)*scale, y*scale),
                       ((center[0]+side*(gap-9))*scale, (y+direction*8)*scale)],
                      fill=(*highlight, 240), width=2*scale)
