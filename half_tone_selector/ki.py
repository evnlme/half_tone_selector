from typing import (
    Callable,
    Optional,
)
from .matrix import (
    Vec,
    clamp,
)
from .color import (
    convertColorSpace,
)
from krita import ( # type: ignore
    Krita,
    ManagedColor,
    View,
    QApplication,
    QColor,
    QDialog,
    QPalette,
)

def getActiveView() -> Optional[View]:
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

def openFGColorDialog(color: QColor, callback: Callable[[QColor], None]) -> None:
    qwin = Krita.instance().activeWindow().qwindow()
    dialogColorSelector = qwin.findChild(QDialog,'WdgDlgInternalColorSelector')
    dualColorButton = dialogColorSelector.parentWidget()

    tempColor = getFGColor() # Assert not None
    setFGColor(color)

    def _callback(result: int):
        if result == QDialog.Accepted:
            selectedColor = getFGColor() # Assert not None
            callback(selectedColor)
        dialogColorSelector.finished.disconnect(_callback)
        setFGColor(tempColor)

    dialogColorSelector.finished.connect(_callback)
    dualColorButton.openForegroundDialog()

def getWindowColor() -> QColor:
    return QApplication.palette().color(QPalette.Window)

def scaleColor(color: QColor, scale: float, b: int = 0) -> QColor:
    rgb = color.getRgb()[:3]
    scaledRgb = [round(clamp(x*scale + b, 0, 255)) for x in rgb]
    return QColor(*scaledRgb)

def oklchToQColor(lch: Vec) -> QColor:
    rgb = convertColorSpace(lch, 'Oklch', 'sRGB')
    c = QColor.fromRgbF(*rgb)
    return c

def qcolorToOklch(c: QColor) -> Vec:
    rgb = list(c.getRgbF()[:3])
    lch = convertColorSpace(rgb, 'sRGB', 'Oklch')
    return lch

def qcolorToOklchFunc(
        getColor: Callable[[], Optional[QColor]],
        ) -> Callable[[], Optional[Vec]]:
    def _func():
        color = getColor()
        return qcolorToOklch(color) if color else None
    return _func
