"""Delivery settings are separate from source geometry and animation timing."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ExportProfile:
    name: str
    scale: float
    max_size: int | None
    crf: int
    cpu_used: int

    def size_for(self, source_size: int) -> int:
        size = source_size * self.scale
        if self.max_size is not None:
            size = min(size, self.max_size)
        return max(2, 2 * round(size / 2))


PROFILES = {
    'vtt': ExportProfile('vtt', scale=.8, max_size=384, crf=36, cpu_used=2),
    'high': ExportProfile('high', scale=1, max_size=None, crf=22, cpu_used=4),
}
