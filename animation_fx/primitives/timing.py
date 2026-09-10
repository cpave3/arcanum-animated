"""Clamped timeline progress and easing, shared by finite compositions."""


def progress(frame, frames=60):
    return min(1, max(0, frame / (frames - 1)))


def smooth(value):
    value = min(1, max(0, value))
    return value * value * (3 - 2 * value)
