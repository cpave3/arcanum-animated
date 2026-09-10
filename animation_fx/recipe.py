"""A callable frame recipe with the same rendering contract as effect modules."""
from dataclasses import dataclass
from typing import Callable

from PIL import Image


@dataclass(frozen=True)
class FrameRecipe:
    render: Callable[[int], Image.Image]
    SIZE: int = 512
    FPS: int = 30
    FRAMES: int = 60
