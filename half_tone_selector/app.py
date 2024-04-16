from typing import (
    Callable,
    Dict,
    List,
    Set,
)
from .lib import (
    Float3,
)
from .state import (
    AppState,
    HalfToneSet,
)
from .ki import (
    getWindowColor,
    scaleColor,
)

def getStyle() -> dict:
    windowColor = getWindowColor()
    isDark = windowColor.value() < 128
    style = {
        'window': windowColor,
        'background': scaleColor(windowColor, 1, 8 if isDark else -8),
        'label': scaleColor(windowColor, 1, 16 if isDark else -16),
        'button': scaleColor(windowColor, 1, 32 if isDark else -32),
    }
    return style

class HalfToneSelectorApp:
    """Class for interacting with AppState"""
    def __init__(self, s: AppState) -> None:
        self.s = s
        # Style settings for widgets.
        self.style = getStyle()
        # If settings are visible, True. If settings are hidden, False.
        self._visible = True
        self._cbs: Dict[str, Set[Callable[..., None]]] = {}

    def setState(self, **kwargs) -> None:
        callbacks = set()
        for k, v in kwargs.items():
            setattr(self.s, k, v)
            if k in self._cbs:
                callbacks |= self._cbs[k]

        for cb in callbacks:
            cb()

    def registerCallback(self, fields: List[str], cb: Callable[..., None]) -> None:
        for f in fields:
            if f not in self._cbs:
                self._cbs[f] = set()
            self._cbs[f].add(cb)

    def unregisterCallback(self, fields: List[str], cb: Callable[..., None]) -> None:
        for f in fields:
            if f in self._cbs:
                self._cbs[f].remove(cb)

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._visible = value
        for cb in self._cbs.get('visible', []):
            cb()

    def halfLight(self) -> Float3:
        l, c, h = self.s.light
        return [l/2, c, h]

    def addHalfToneSet(self, hts: HalfToneSet) -> int:
        i = len(self.s.halfTones)
        self.s.halfTones.append(hts)
        for cb in self._cbs.get('addHalfToneSet', []):
            cb(i)
        return i

    def removeHalfToneSet(self, hts: HalfToneSet) -> int:
        i = self.s.halfTones.index(hts)
        self.s.halfTones.pop(i)
        for cb in self._cbs.get('removeHalfToneSet', []):
            cb(i)
        return i
