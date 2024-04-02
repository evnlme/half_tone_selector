"""

References:
https://scripting.krita.org/lessons/plugins-create
https://github.com/kaichi1342/PaletteGenerator
https://api.kde.org/krita/html/index.html
https://doc.qt.io/qt-6/widget-classes.html
https://www.riverbankcomputing.com/static/Docs/PyQt6/index.html
"""

import math
from typing import Callable, Optional, List, Tuple
from krita import (
    DockWidget,
    DockWidgetFactory,
    DockWidgetFactoryBase,
    Krita,
    ManagedColor,
    View,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget,
    QLayout,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QSizePolicy,
    QLabel,
    QColorDialog,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
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

def createSelectToneWidget(name, options, defaultTone, updateTone):
    def setLabelStyle(widget):
        widget.setFixedWidth(80)
        widget.setStyleSheet('''
            QLabel {
                border: 0px solid transparent;
                border-radius: 0px;
                padding: 5px 10px;
                background-color: #404040;
            }
        ''')

    def setColor(widget, color):
        updateTone(color)
        widget.setStyleSheet(f'''
            QPushButton {{
                border: 0px solid transparent;
                border-radius: 0px;
                padding: 5px 10px;
                background-color: {color.name()};
            }}
        ''')

    def setColorStyle(widget):
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        setColor(widget, defaultTone)

    def handleColorDialog(widget):
        color = QColorDialog.getColor(options=QColorDialog.ShowAlphaChannel)
        if color.isValid():
            setColor(widget, color)

    def setOptionStyle(widget):
        widget.setStyleSheet('''
            QPushButton {
                border: 0px solid transparent;
                border-radius: 0px;
                padding: 5px 10px;
                background-color: #606060;
            }
            QPushButton::hover {
                background-color: #505050;
            }
        ''')

    def handleOptionClick(widget, getColor):
        color = getColor()
        if color and color.isValid():
            setColor(widget, color)

    def createOptionButton(widget, opt):
        button = QPushButton(opt['name'])
        setOptionStyle(button)
        button.clicked.connect(lambda: handleOptionClick(widget, opt['getColor']))
        return button

    widget, layout = addLayout(QHBoxLayout)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(1)

    label = QLabel(name)
    setLabelStyle(label)
    layout.addWidget(label)

    colorButton = QPushButton('Color')
    setColorStyle(colorButton)
    colorButton.clicked.connect(lambda: handleColorDialog(colorButton))
    layout.addWidget(colorButton)

    for opt in options:
        button = createOptionButton(colorButton, opt)
        layout.addWidget(button)

    return widget

def createColorBarWidget(colors: List[QColor]) -> QWidget:
    def createColorPatch(color):
        patch = QPushButton()
        patch.setStyleSheet(f'''
            QPushButton {{
                border: 0px solid transparent;
                border-radius: 0px;
                background-color: {color.name()};
            }}
        ''')
        patch.clicked.connect(lambda: setFGColor(color))
        return patch

    widget, layout = addLayout(QHBoxLayout)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(1)

    for color in colors:
        patch = createColorPatch(color)
        layout.addWidget(patch)

    deleteButton = QPushButton('Delete')
    deleteButton.clicked.connect(lambda: widget.deleteLater())
    layout.addWidget(deleteButton)

    return widget

def halfLight(state: dict) -> QColor:
    r, g, b, a = state['light'].getRgb()
    r2 = round(r / 2)
    g2 = round(g / 2)
    b2 = round(b / 2)
    return QColor(r2, g2, b2, a)

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

def createHalfToneSelectorWidget() -> QWidget:
    state = {
        'light': QColor(128, 128, 128),
        'dark': QColor(64, 64, 64),
    }

    # Select light tone
    #   Choice [FG | BG | Custom]
    lightToneWidget = createSelectToneWidget(
        'Light tone',
        [
            {'name': 'FG', 'getColor': getFGColor},
            {'name': 'BG', 'getColor': getBGColor},
        ],
        state['light'],
        lambda tone: state.update(light=tone),
    )

    # Select dark tone
    #   Choice [Half | FG | BG | Custom]
    darkToneWidget = createSelectToneWidget(
        'Dark tone',
        [
            {'name': 'Half', 'getColor': lambda: halfLight(state)},
            {'name': 'FG', 'getColor': getFGColor},
            {'name': 'BG', 'getColor': getBGColor},
        ],
        state['dark'],
        lambda tone: state.update(dark=tone),
    )

    # Select half tone count - Positive integer
    countLabel = QLabel('Count:')
    spinBox = QSpinBox()
    spinBox.setRange(1, 10)
    spinBox.setValue(5)
    countWidget, countLayout = addLayout(
        qlayout=QHBoxLayout,
        childWidgets=[countLabel, spinBox])
    countLayout.setContentsMargins(0, 0, 0, 0)

    # Cosine - Toggle
    cosineLabel = QLabel('Cosine:')
    cosineCheckBox = QCheckBox()
    cosineCheckBox.setChecked(True)
    cosineWidget, cosineLayout = addLayout(
        qlayout=QHBoxLayout,
        childWidgets=[cosineLabel, cosineCheckBox])
    cosineLayout.setContentsMargins(0, 0, 0, 0)

    # Exponent - Float
    exponentLabel = QLabel('Exponent:')
    doubleSpinBox = QDoubleSpinBox()
    doubleSpinBox.setValue(0.45)
    exponentWidget, exponentLayout = addLayout(
        qlayout=QHBoxLayout,
        childWidgets=[exponentLabel, doubleSpinBox])
    exponentLayout.setContentsMargins(0, 0, 0, 0)

    # Tones
    #   Create half tones - Button
    #   Color[0] Color[1] ...
    def create():
        intervals = computeIntervals(
            getN=spinBox.value,
            getExp=doubleSpinBox.value,
            getCos=cosineCheckBox.isChecked)
        colors = [interpolateColors(state['light'], state['dark'], i) for i in intervals]
        layout.addWidget(createColorBarWidget(colors))

    createButton = QPushButton('Create half tones')
    createButton.clicked.connect(create)

    widget, layout = addLayout(
        qlayout=QVBoxLayout,
        childWidgets=[
            lightToneWidget, darkToneWidget,
            countWidget, cosineWidget, exponentWidget,
            createButton,
        ])
    layout.setSpacing(5)
    layout.setAlignment(Qt.AlignTop)

    wrapperWidget, _ = addLayout(
        qlayout=QVBoxLayout,
        childWidgets=[widget])

    return wrapperWidget

class HalfToneSelector(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Half Tone Selector')
        widget = createHalfToneSelectorWidget()
        self.setWidget(widget)

    # notifies when views are added or removed
    # 'pass' means do not do anything
    def canvasChanged(self, canvas):
        pass

def addHalfToneSelector():
    instance = Krita.instance()
    dock_widget_factory = DockWidgetFactory(
        'half_tone_selector',
        DockWidgetFactoryBase.DockRight,
        HalfToneSelector)
    instance.addDockWidgetFactory(dock_widget_factory)

addHalfToneSelector()