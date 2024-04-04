import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, List, Tuple
from krita import (
    Krita,
    ManagedColor,
    View,
    QColor,
    QPalette,
    QApplication,
    QLayout,
    QWidget,
)

@dataclass
class AppState:
    light: QColor = field(default_factory=lambda: QColor(128, 128, 128))
    dark: QColor = field(default_factory=lambda: QColor(64, 64, 64))
    count: int = 5
    cos: bool = True
    exp: float = 0.45
    halfTones: List[List[QColor]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'light': self.light.name(),
            'dark': self.dark.name(),
            'count': self.count,
            'cos': self.cos,
            'exp': self.exp,
            'halfTones': [[tone.name() for tone in ht] for ht in self.halfTones]
        }

    def to_file(self, path: Path) -> None:
        with path.open('w') as f:
            json.dump(self.to_dict(), f)

    @staticmethod
    def from_dict(d: dict) -> 'AppState':
        return AppState(
            light=QColor(d['light']),
            dark=QColor(d['dark']),
            count=d['count'],
            cos=d['cos'],
            exp=d['exp'],
            halfTones=[[QColor(tone) for tone in ht] for ht in d['halfTones']]
        )

    @staticmethod
    def from_file(path: Path) -> 'AppState':
        with path.open() as f:
            return AppState.from_dict(json.load(f))

def getActiveView() -> View:
    instance = Krita.instance()
    window = instance.activeWindow() if instance else None
    view = window.activeView() if window else None
    return view if view else None

def getFGColor() -> Optional[QColor]:
    view = getActiveView()
    canvas = view.canvas() if view else None
    fg = view.foregroundColor() if view else None
    return fg.colorForCanvas(canvas) if canvas and fg else None

def getBGColor() -> Optional[QColor]:
    view = getActiveView()
    canvas = view.canvas() if view else None
    bg = view.backgroundColor() if view else None
    return bg.colorForCanvas(canvas) if canvas and bg else None

def setFGColor(color: QColor) -> None:
    view = getActiveView()
    if view:
        view.setForeGroundColor(ManagedColor.fromQColor(color))

def getWindowColor() -> QColor:
    return QApplication.palette().color(QPalette.Window)

def halfLight(state: AppState) -> QColor:
    rgba = state.light.getRgb()
    halfRgb = [round(x / 2) for x in rgba[:3]]
    return QColor(*halfRgb, rgba[3])

def computeIntervals(n: int, cos: bool, exp: float) -> List[float]:
    intervals = [i / (n+1) for i in range(n+2)]
    if cos:
        intervals = [math.cos(x * math.pi / 2) for x in intervals]
    intervals = [round(x**exp, 2) for x in intervals]
    return intervals

def interpolateColors(c1: QColor, c2: QColor, t: float) -> QColor:
    # Computes c1*t + c2*(1-t)
    rgba1 = c1.getRgb()
    rgba2 = c2.getRgb()
    rgba = [round(x1*t + x2*(1-t)) for x1, x2 in zip(rgba1, rgba2)]
    return QColor(*rgba)

def clamp(xmin: float, xmax: float, x: float) -> float:
    return max(min(x, xmax), xmin)

def scaleColor(color: QColor, scale: float, b: int = 0) -> QColor:
    rgb = color.getRgb()[:3]
    scaledRgb = [round(clamp(0, 255, x*scale + b)) for x in rgb]
    return QColor(*scaledRgb)

def addLayout(
        qlayout: Callable[[], QLayout],
        qwidget: Callable[[], QWidget]=None,
        childWidgets: List[QWidget]=[],
        ) -> Tuple[QWidget, QLayout]:
    widget = QWidget() if qwidget is None else qwidget()
    layout = qlayout()
    widget.setLayout(layout)
    for child in childWidgets:
        layout.addWidget(child)
    return widget, layout