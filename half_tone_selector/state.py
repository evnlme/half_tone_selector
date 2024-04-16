import json
from dataclasses import dataclass, field, fields
from math import cos, pi
from pathlib import Path
from typing import List
from .lib import (
    Float3,
    interp3,
    scale3,
)
from .color import (
    fromHexRgb,
    rgbToOklch,
    linearRgbToOklch,
    oklchToLinearRgb,
    interpolateOklch,
)

@dataclass
class HalfToneSet:
    name: str
    tones: List[Float3]

    def to_dict(self) -> dict:
        return {f.name: getattr(self, f.name) for f in fields(HalfToneSet)}

    @staticmethod
    def _old_from_dict(d: List[str]) -> 'HalfToneSet':
        """Old version used a list of rgb hex strings."""
        return HalfToneSet(
            name='Migrated',
            tones=[rgbToOklch(fromHexRgb(tone)) for tone in d])

    @staticmethod
    def from_dict(d: dict) -> 'HalfToneSet':
        if isinstance(d, list):
            # Backwards compatibility.
            return HalfToneSet._old_from_dict(d)
        return HalfToneSet(**d)

halfToneSetFields = {f.name for f in fields(HalfToneSet)}

@dataclass
class AppState:
    # [Oklch] Tone when fully lit.
    light: Float3 = field(default_factory=lambda: [0.5, 0, 0])
    # [Oklch] Tone when fully unlit (in shadow).
    dark: Float3 = field(default_factory=lambda: [0.25, 0, 0])
    # Chroma control.
    k: float = 1.0
    # [Oklch] Emitter.
    emitter: Float3 = field(default_factory=lambda: [1, 0, 0])
    # Normalize the emitter lightness to 1.
    normalize: bool = True
    # Intensity of the emitter.
    intensity: float = 1.0
    # Controls how much the emitter affects the output.
    white: float = 0.5
    # Number of half tones to generate.
    count: int = 5
    # Non-linear selection of half tones.
    cos: bool = True
    # Half tones.
    halfTones: List[HalfToneSet] = field(default_factory=list)

    def to_dict(self) -> dict:
        def serialize(name: str):
            if name == 'halfTones':
                return [hts.to_dict() for hts in self.halfTones]
            else:
                return getattr(self, name)
        return {
            f.name: serialize(f.name)
            for f in fields(AppState)
            if f.name not in ['emitter', 'normalize', 'intensity', 'white']
        }

    def to_file(self, path: Path) -> None:
        with path.open('w') as f:
            json.dump(self.to_dict(), f)

    @staticmethod
    def from_dict(d: dict) -> 'AppState':
        s = AppState()
        for f in fields(AppState):
            if f.name in ['emitter', 'normalize', 'intensity', 'white']:
                # Ignore emitter settings.
                continue
            if f.name in d:
                if f.name == 'halfTones':
                    halfToneSets = [HalfToneSet.from_dict(hts) for hts in d[f.name]]
                    setattr(s, f.name, halfToneSets)
                elif f.name in ('light', 'dark', 'emitter'):
                    if isinstance(d[f.name], str):
                        # Backwards compatibility.
                        setattr(s, f.name, rgbToOklch(fromHexRgb(d[f.name])))
                    else:
                        setattr(s, f.name, d[f.name])
                else:
                    setattr(s, f.name, d[f.name])
        return s

    @staticmethod
    def from_file(path: Path) -> 'AppState':
        with path.open() as f:
            return AppState.from_dict(json.load(f))

appStateFields = {f.name for f in fields(AppState)}

def computeIntervals(n: int, useCos: bool) -> List[float]:
    intervals = [i / (n+1) for i in range(n+2)]
    if useCos:
        # Cos for linear. Cos**(1/3) for oklch.
        return [cos(x * pi / 2)**(1/3) for x in intervals]
    else:
        return list(reversed(intervals))

def generateColors(s: AppState) -> HalfToneSet:
    ts = computeIntervals(s.count, s.cos)
    lchs = [interpolateOklch(s.dark, s.light, t, s.k) for t in ts]
    # linears = [oklchToLinearRgb(lch) for lch in lchs]

    # emitterLch = list(s.emitter)
    # if s.normalize:
    #     emitterLch[0] = 1.0
    # emitterLinear = oklchToLinearRgb(emitterLch)
    # emitterWhiten = interp3(emitterLinear, [1, 1, 1], s.white)
    # emitterScaled = scale3(emitterWhiten, s.intensity)
    # emitterIntervals = [interp3([1, 1, 1], emitterScaled, t) for t in ts]
    # finalLinears = [
    #     [e[i]*rgb[i] for i in range(3)]
    #     for e, rgb in zip(emitterIntervals, linears)]

    # tones = [linearRgbToOklch(rgb) for rgb in finalLinears]
    return HalfToneSet(name='', tones=lchs)
