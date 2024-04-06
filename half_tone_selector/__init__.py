from pathlib import Path
from typing import Callable, List
from krita import (
    DockWidget,
    DockWidgetFactory,
    DockWidgetFactoryBase,
    Krita,
    Qt,
    QColor,
    QFontMetrics,
    QWidget,
    QLayout,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QSizePolicy,
    QLabel,
    QLineEdit,
    QColorDialog,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QScrollArea,
)
from .lib import (
    AppState,
    getFGColor,
    getBGColor,
    setFGColor,
    getWindowColor,
    halfLight,
    scaleColor,
    computeIntervals,
    interpolateColors,
    addLayout,
)

# Data store so state isn't lost when Krita closes.
dataPath = Path(__file__).resolve().parent / '_data.json'
S = AppState()
if dataPath.exists():
    S = AppState.from_file(dataPath)
Krita.instance().notifier().applicationClosing.connect(lambda: S.to_file(dataPath))

def createSelectToneWidget(
        name: str,
        options: list,
        getTone: Callable[[], QColor],
        setTone: Callable[[QColor], None],
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
        setTone(color)
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
        setColor(widget, getTone())

    def handleColorDialog(widget):
        color = QColorDialog.getColor(getTone())
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

def createColorPatch(color: QColor, style: dict) -> QWidget:
    patch = QPushButton()
    patch.setMinimumSize(18, 18)
    patch.setToolTip(str(color.getRgb()[:3]))
    patch.setStyleSheet(f'''
        QPushButton {{
            border: 0px solid transparent;
            border-radius: 0px;
            background-color: {color.name()};
        }}
        QPushButton::hover {{
            border: 0.5px solid {style['background'].name()};
        }}
    ''')
    patch.clicked.connect(lambda: setFGColor(color))
    return patch

def createColorPatchRow(colors: List[QColor], style: dict) -> QWidget:
    patches = [createColorPatch(color, style) for color in colors]
    widget, layout = addLayout(qlayout=QHBoxLayout, childWidgets=patches)
    widget.setStyleSheet(f'''
        QWidget {{
            border: 0px solid transparent;
            border-radius: 0px;
            background-color: {style['background'].name()};
        }}
    ''')
    layout.setContentsMargins(1, 1, 1, 1)
    layout.setSpacing(1)
    return widget

def createColorBarWidget(
        colors: List[QColor],
        style: dict,
        parentLayout: QLayout,
        ) -> QWidget:
    colorPatchRow = createColorPatchRow(colors, style)

    line = QLineEdit(colors[0].name())
    font = line.font()
    font.setPointSize(8)
    line.setFont(font)
    fm = QFontMetrics(line.font())
    line.setFixedHeight(fm.height())
    line.setStyleSheet(f'''
        QLineEdit {{
            font-size: 8pt;
            padding: 0px;
            margin: 0px;
            border: 0px solid transparent;
        }}
        QLineEdit::Hover {{
            background-color: {style['background'].name()};
        }}
    ''')

    widgetV, layoutV = addLayout(
        qlayout=QVBoxLayout,
        childWidgets=[colorPatchRow, line])
    widgetV.setStyleSheet(f'''
        QWidget {{
            background-color: {style['label'].name()};
        }}
    ''')
    layoutV.setContentsMargins(5, 2, 5, 2)
    layoutV.setSpacing(1)

    widget, layout = addLayout(qlayout=QHBoxLayout, childWidgets=[widgetV])
    layout.setAlignment(Qt.AlignTop)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(1)

    def delete():
        i = parentLayout.indexOf(widget)
        S.halfTones.pop(i)
        widget.deleteLater()

    deleteButton = QPushButton()
    deleteButton.setIcon(Krita.instance().icon('deletelayer'))
    deleteButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    deleteButton.clicked.connect(delete)
    layout.addWidget(deleteButton)

    parentLayout.addWidget(widget)
    return widget

def createHalfToneSelectorWidget() -> QWidget:
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
        lambda: S.light,
        lambda tone: setattr(S, 'light', tone),
        style,
    )

    # Select dark tone
    #   Choice [Half | FG | BG | Custom]
    darkToneWidget = createSelectToneWidget(
        'Dark tone',
        [
            {'name': 'Half', 'getColor': lambda: halfLight(S)},
            {'name': 'FG', 'getColor': getFGColor},
            {'name': 'BG', 'getColor': getBGColor},
        ],
        lambda: S.dark,
        lambda tone: setattr(S, 'dark', tone),
        style,
    )

    # Select half tone count - Positive integer
    countLabel = QLabel('Count:')
    spinBox = QSpinBox()
    spinBox.setRange(1, 10)
    spinBox.setValue(S.count)
    spinBox.valueChanged.connect(lambda i: setattr(S, 'count', i))
    countWidget, countLayout = addLayout(
        qlayout=QHBoxLayout,
        childWidgets=[countLabel, spinBox])
    countLayout.setContentsMargins(0, 0, 0, 0)

    # Cosine - Toggle
    cosineLabel = QLabel('Cosine:')
    cosineCheckBox = QCheckBox()
    cosineCheckBox.setChecked(S.cos)
    cosineCheckBox.toggled.connect(lambda checked: setattr(S, 'cos', checked))
    cosineWidget, cosineLayout = addLayout(
        qlayout=QHBoxLayout,
        childWidgets=[cosineLabel, cosineCheckBox])
    cosineLayout.setContentsMargins(0, 0, 0, 0)

    # Exponent - Float
    exponentLabel = QLabel('Exponent:')
    doubleSpinBox = QDoubleSpinBox()
    doubleSpinBox.setValue(S.exp)
    doubleSpinBox.valueChanged.connect(lambda d: setattr(S, 'exp', d))
    exponentWidget, exponentLayout = addLayout(
        qlayout=QHBoxLayout,
        childWidgets=[exponentLabel, doubleSpinBox])
    exponentLayout.setContentsMargins(0, 0, 0, 0)

    # Tones
    #   Create half tones - Button
    #   Color[0] Color[1] ...
    toneWidget, toneLayout = addLayout(QVBoxLayout)
    toneLayout.setContentsMargins(0, 0, 0, 0)
    toneLayout.setSpacing(5)

    def create():
        intervals = computeIntervals(S.count, S.cos, S.exp)
        colors = [interpolateColors(S.light, S.dark, i) for i in intervals]
        S.halfTones.append(colors)
        createColorBarWidget(colors, style, toneLayout)

    createButton = QPushButton('Create half tones')
    createButton.clicked.connect(create)

    for tones in S.halfTones:
        createColorBarWidget(tones, style, toneLayout)

    # Main layout
    widget, layout = addLayout(
        qlayout=QVBoxLayout,
        childWidgets=[
            lightToneWidget, darkToneWidget,
            countWidget, cosineWidget, exponentWidget,
            createButton, toneWidget,
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
