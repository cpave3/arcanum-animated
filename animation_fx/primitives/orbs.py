"""Dense golden cores shared by free-standing and mechanical spark anchors."""
import numpy as np
from PIL import Image


def orb_layer(size, center, radius, *, scale=1):
    yy, xx = np.mgrid[:size*scale, :size*scale].astype(np.float32)
    distance = np.sqrt((xx/scale-center[0])**2 + (yy/scale-center[1])**2)
    core = np.clip(1-(distance/radius)**2, 0, 1)
    halo = np.exp(-(distance/(radius*1.8))**2)
    pixels = np.zeros((size*scale, size*scale, 4), dtype=np.uint8)
    pixels[..., 0] = 255
    pixels[..., 1] = (165+90*np.sqrt(core)).astype(np.uint8)
    pixels[..., 2] = (20+210*core).astype(np.uint8)
    pixels[..., 3] = (255*np.clip(core*2+halo*.65, 0, 1)).astype(np.uint8)
    return Image.fromarray(pixels)
