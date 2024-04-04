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
from PyQt5.QtGui import (
    QColor,
    QPalette,
)
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
    QApplication,
    QScrollArea,
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

def createSelectToneWidget(
        name: str,
        options: list,
        defaultTone: QColor,
        updateTone: Callable[[QColor], None],
        style: dict,
        ) -> QWidget:
    def setLabelStyle(widget):
        widget.setFixedWidth(80)
        widget.setStyleSheet(f'''
            QLabel {{
                border: 0px solid transparent;
                border-radius: 0px;
                padding: 5px 10px;
                background-color: {style['label'].name()};
            }}
        ''')

    def setColor(widget, color):
        updateTone(color)
        fontColor = scaleColor(color, 1, 96 if color.value() < 128 else -96)
        widget.setStyleSheet(f'''
            QPushButton {{
                border: 0px solid transparent;
                border-radius: 0px;
                padding: 5px 10px;
                background-color: {color.name()};
                color: {fontColor.name()};
            }}
            QPushButton::hover {{
                border: 1px solid {style['window'].name()};
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
        widget.setStyleSheet(f'''
            QPushButton {{
                border: 0px solid transparent;
                border-radius: 0px;
                padding: 5px 10px;
                background-color: {style['button'].name()};
            }}
            QPushButton::hover {{
                background-color: {style['window'].name()};
            }}
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

def createColorBarWidget(colors: List[QColor], style: dict) -> QWidget:
    def createColorPatch(color):
        patch = QPushButton()
        patch.setMinimumSize(16, 16)
        patch.setStyleSheet(f'''
            QPushButton {{
                border: 0px solid transparent;
                border-radius: 0px;
                background-color: {color.name()};
            }}
            QPushButton::hover {{
                border: 0.5px solid {style['window'].name()};
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

    deleteButton = QPushButton()
    deleteButton.setIcon(Krita.instance().icon('deletelayer'))
    deleteButton.clicked.connect(lambda: widget.deleteLater())
    layout.addWidget(deleteButton)

    return widget

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

def createHalfToneSelectorWidget() -> QWidget:
    state = {
        'light': QColor(128, 128, 128),
        'dark': QColor(64, 64, 64),
    }
    windowColor = getWindowColor()
    isDark = windowColor.value() < 128
    style = {
        'window': windowColor,
        'background': scaleColor(windowColor, 1, 8 if isDark else -8),
        'label': scaleColor(windowColor, 1, 16 if isDark else -16),
        'button': scaleColor(windowColor, 1, 32 if isDark else -32),
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
        style,
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
        style,
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
        layout.addWidget(createColorBarWidget(colors, style))

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
    widget.setStyleSheet(f'''
        QWidget {{
            background-color: {style['background'].name()};
        }}
    ''')

    scrollArea = QScrollArea()
    scrollArea.setWidgetResizable(True)
    scrollArea.setWidget(widget)
    return scrollArea

class HalfToneSelector(DockWidget):
    def __init__(self):
        super().__init__()
        widget = createHalfToneSelectorWidget()
        self.setWindowTitle('Half Tone Selector')
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
