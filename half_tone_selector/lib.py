import math
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

def halfLight(state: dict) -> QColor:
    rgba = state['light'].getRgb()
    halfRgb = [round(x / 2) for x in rgba[:3]]
    return QColor(*halfRgb, rgba[3])

def computeIntervals(getN, getExp, getCos) -> List[float]:
    n = getN()
    exp = getExp()
    intervals = [i / (n+1) for i in range(n+2)]
    if getCos():
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