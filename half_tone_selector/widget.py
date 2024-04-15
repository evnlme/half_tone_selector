from typing import Callable, Optional, List, Tuple
from .lib import (
    Float3,
)
from .state import (
    AppState,
    HalfToneSet,
    generateColors,
    halfLight,
)
from .ki import (
    getFGColor,
    getBGColor,
    setFGColor,
    openFGColorDialog,
    getWindowColor,
    scaleColor,
    oklchToQColor,
    qcolorToOklch,
    loadData,
)
from krita import ( # type: ignore
    QLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    DockWidget,
    DockWidgetFactory,
    DockWidgetFactoryBase,
    Krita,
    Qt,
    QColor,
    QFontMetrics,
    QWidget,
    QGroupBox,
    QLayout,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QButtonGroup,
    QSizePolicy,
    QLabel,
    QLineEdit,
    QColorDialog,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QScrollArea,
    QTabWidget,
)

def addLayout(
        qlayout: Callable[[], QLayout],
        qwidget: Optional[Callable[[], QWidget]]=None,
        childWidgets: List[QWidget]=[],
        ) -> Tuple[QWidget, QLayout]:
    widget = QWidget() if qwidget is None else qwidget()
    layout = qlayout()
    widget.setLayout(layout)
    for child in childWidgets:
        layout.addWidget(child)
    return widget, layout

def labeledInput(
        name: str,
        qwidget: Callable[[], QWidget],
        ) -> Tuple[QWidget, QWidget, QLayout]:
    label = QLabel(f'{name}:')
    input = qwidget()
    widget, layout = addLayout(
        qlayout=QHBoxLayout,
        childWidgets=[label, input])
    layout.setContentsMargins(0, 0, 0, 0)
    return input, widget, layout

def createMainLayout(childWidgets: List[QWidget], style: dict) -> QWidget:
    widget, layout = addLayout(
        qlayout=QVBoxLayout,
        childWidgets=childWidgets)
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

def createSelectToneWidget(
        name: str,
        options: list,
        getTone: Callable[[], QColor],
        setTone: Callable[[QColor], None],
        style: dict,
        ) -> QWidget:
    def setLabelStyle(widget):
        widget.setStyleSheet(f'''
            QLabel {{
                border: 0px solid transparent;
                border-radius: 0px;
                padding: 5px 10px;
                background-color: {style['label'].name()};
            }}
        ''')

    def setColor(widget, lch: Float3):
        setTone(lch)
        color = oklchToQColor(lch)
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
        # color = QColorDialog.getColor(oklchToQColor(getTone()))
        def handler(color: QColor):
            if color and color.isValid():
                lch = qcolorToOklch(color)
                setColor(widget, lch)

        openFGColorDialog(oklchToQColor(getTone()), handler)

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
            lch = qcolorToOklch(color)
            setColor(widget, lch)

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

def createColorPatch(lch: Float3, style: dict) -> QWidget:
    patch = QPushButton()
    patch.setMinimumSize(18, 18)
    patch.setToolTip(str(lch))
    color = oklchToQColor(lch)
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

def createColorPatchRow(halfToneSet: HalfToneSet, style: dict) -> QWidget:
    patches = [createColorPatch(tone, style) for tone in halfToneSet.tones]
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
        halfToneSet: HalfToneSet,
        style: dict,
        parentLayout: QLayout,
        s: AppState,
        ) -> QWidget:
    colorPatchRow = createColorPatchRow(halfToneSet, style)

    line = QLineEdit(halfToneSet.name)
    line.textChanged.connect(lambda text: setattr(halfToneSet, 'name', text))
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
        s.halfTones.pop(i)
        widget.deleteLater()

    deleteButton = QPushButton()
    deleteButton.setIcon(Krita.instance().icon('deletelayer'))
    deleteButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    deleteButton.clicked.connect(delete)
    layout.addWidget(deleteButton)

    parentLayout.addWidget(widget)
    return widget

def createToneGroup(s: AppState, style: dict) -> QWidget:
    # Select light tone
    #   Choice [FG | BG | Custom]
    lightToneWidget = createSelectToneWidget(
        'Light',
        [
            {'name': 'FG', 'getColor': getFGColor},
            {'name': 'BG', 'getColor': getBGColor},
        ],
        lambda: s.light,
        lambda tone: setattr(s, 'light', tone),
        style,
    )

    # Select dark tone
    #   Choice [Half | FG | BG | Custom]
    darkToneWidget = createSelectToneWidget(
        'Dark',
        [
            {'name': 'Half', 'getColor': lambda: oklchToQColor(halfLight(s))},
            {'name': 'FG', 'getColor': getFGColor},
            {'name': 'BG', 'getColor': getBGColor},
        ],
        lambda: s.dark,
        lambda tone: setattr(s, 'dark', tone),
        style,
    )

    # Chroma - Float
    chromaInput, chromaWidget, _  = labeledInput('Chroma', QDoubleSpinBox)
    chromaInput.setRange(-1, 1)
    chromaInput.setSingleStep(0.05)
    chromaInput.setValue(s.k)
    chromaInput.valueChanged.connect(lambda d: setattr(s, 'k', d))

    widget, layout = addLayout(
        qlayout=QVBoxLayout,
        qwidget=lambda: QGroupBox('Base Tones'),
        childWidgets=[
            lightToneWidget, darkToneWidget, chromaWidget,
        ])
    widget.setFlat(True)
    layout.setContentsMargins(2, 2, 2, 2)
    layout.setSpacing(5)
    return widget

def createEmitterGroup(s: AppState, style: dict) -> QWidget:
    # Emitter
    emitterWidget = createSelectToneWidget(
        'Emitter',
        [
            {'name': 'Reset', 'getColor': lambda: QColor.fromRgbF(1.0, 1.0, 1.0)},
            {'name': 'FG', 'getColor': getFGColor},
            {'name': 'BG', 'getColor': getBGColor},
        ],
        lambda: s.emitter,
        lambda tone: setattr(s, 'emitter', tone),
        style,
    )

    # Normalize
    normalizeInput, normalizeWidget, _ = labeledInput('Normalize', QCheckBox)
    normalizeInput.setChecked(s.normalize)
    normalizeInput.toggled.connect(lambda checked: setattr(s, 'normalize', checked))

    # Intensity
    intensityInput, intensityWidget, _  = labeledInput('Intensity', QDoubleSpinBox)
    intensityInput.setRange(0, 1000)
    intensityInput.setSingleStep(0.1)
    intensityInput.setValue(s.intensity)
    intensityInput.valueChanged.connect(lambda d: setattr(s, 'intensity', d))

    # White
    whiteInput, whiteWidget, _  = labeledInput('White', QDoubleSpinBox)
    whiteInput.setRange(0, 1)
    whiteInput.setSingleStep(0.05)
    whiteInput.setValue(s.white)
    whiteInput.valueChanged.connect(lambda d: setattr(s, 'white', d))

    widget, layout = addLayout(
        qlayout=QVBoxLayout,
        qwidget=lambda: QGroupBox('Emitter'),
        childWidgets=[
            emitterWidget, normalizeWidget, intensityWidget, whiteWidget,
        ])
    layout.setContentsMargins(2, 2, 2, 2)
    layout.setSpacing(5)
    return widget

def createSamplingGroup(s: AppState, style: dict) -> QWidget:
    # Select half tone count - Positive integer
    countInput, countWidget, _ = labeledInput('Count', QSpinBox)
    countInput.setRange(1, 10)
    countInput.setValue(s.count)
    countInput.valueChanged.connect(lambda i: setattr(s, 'count', i))

    # Cosine - Toggle
    cosineLabel = QLabel('Distribution:')

    linearButton = QPushButton('Linear')
    linearButton.setCheckable(True)
    linearButton.setChecked(not s.cos)

    cosineButton = QPushButton('Cosine')
    cosineButton.setCheckable(True)
    cosineButton.setChecked(s.cos)

    def handleClicked(button, state: bool):
        def _handleClicked():
            linearButton.setChecked(False)
            cosineButton.setChecked(False)
            button.setChecked(True)
            setattr(s, 'cos', state)
        return _handleClicked

    linearButton.clicked.connect(handleClicked(linearButton, False))
    cosineButton.clicked.connect(handleClicked(cosineButton, True))

    cosineWidget, cosineLayout = addLayout(
        qlayout=QHBoxLayout,
        childWidgets=[
             linearButton, cosineButton,
        ])
    cosineLayout.setContentsMargins(0, 0, 0, 0)

    widget, layout = addLayout(
        qlayout=QVBoxLayout,
        qwidget=lambda: QGroupBox('Sampling'),
        childWidgets=[
            countWidget, cosineLabel, cosineWidget,
        ])
    layout.setContentsMargins(2, 2, 2, 2)
    layout.setSpacing(5)
    return widget

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

def createHalfToneSelectorWidget(s: AppState) -> QWidget:
    style = getStyle()
    toneGroup = createToneGroup(s, style)
    # emitterGroup = createEmitterGroup(s, style)
    samplingGroup = createSamplingGroup(s, style)

    # Tones
    #   Create half tones - Button
    #   Color[0] Color[1] ...
    toneWidget, toneLayout = addLayout(QVBoxLayout)
    toneLayout.setContentsMargins(0, 0, 0, 0)
    toneLayout.setSpacing(5)

    def create():
        halfToneSet = generateColors(s)
        s.halfTones.append(halfToneSet)
        createColorBarWidget(halfToneSet, style, toneLayout, s)

    createButton = QPushButton('Create half tones')
    createButton.clicked.connect(create)

    for halfToneSet in s.halfTones:
        createColorBarWidget(halfToneSet, style, toneLayout, s)

    settingsWidget, settingsLayout = addLayout(
        qlayout=QVBoxLayout,
        childWidgets=[
            toneGroup,
            # emitterGroup,
            samplingGroup,
            createButton,
        ])
    settingsLayout.setContentsMargins(0, 0, 0, 0)
    settingsLayout.setSpacing(5)
    settingsLayout.setAlignment(Qt.AlignTop)

    visCheckBox = QCheckBox('Settings (visible)')

    def toggleVis(on: bool):
        settingsWidget.setVisible(on)
        visCheckBox.setText('Settings (visible)' if on else 'Settings (hidden)')

    visCheckBox.setChecked(True)
    visCheckBox.toggled.connect(toggleVis)

    mainWidget = createMainLayout(
        childWidgets=[
            visCheckBox,
            settingsWidget,
            toneWidget,
        ], style=style)
    return mainWidget

class HalfToneSelector(DockWidget):
    def __init__(self):
        super().__init__()
        widget = createHalfToneSelectorWidget(S)
        self.setWindowTitle('Half Tone Selector')
        self.setWidget(widget)

    # notifies when views are added or removed
    def canvasChanged(self, canvas):
        pass

# Global state.
S: AppState

def registerPlugin():
    global S
    S = loadData()
    instance = Krita.instance()

    half_tone_selector_factory = DockWidgetFactory(
        'half_tone_selector',
        DockWidgetFactoryBase.DockRight,
        HalfToneSelector)
    instance.addDockWidgetFactory(half_tone_selector_factory)
