import krita as K # type: ignore
from typing import Callable, Optional, List, Tuple
from .lib import (
    Float3,
)
from .state import (
    HalfToneSet,
    generateColors,
)
from .app import HalfToneSelectorApp
from .ki import (
    getFGColor,
    getBGColor,
    setFGColor,
    openFGColorDialog,
    scaleColor,
    oklchToQColor,
    qcolorToOklch,
    qcolorToOklchFunc,
)

def addLayout(
        qlayout: Callable[[], K.QLayout],
        qwidget: Optional[Callable[[], K.QWidget]]=None,
        childWidgets: List[K.QWidget]=[],
        ) -> Tuple[K.QWidget, K.QLayout]:
    widget = K.QWidget() if qwidget is None else qwidget()
    layout = qlayout()
    widget.setLayout(layout)
    for child in childWidgets:
        layout.addWidget(child)
    return widget, layout

def labeledInput(
        name: str,
        qwidget: Callable[[], K.QWidget],
        ) -> Tuple[K.QWidget, K.QWidget, K.QLayout]:
    label = K.QLabel(f'{name}:')
    input = qwidget()
    widget, layout = addLayout(
        qlayout=K.QHBoxLayout,
        childWidgets=[label, input])
    layout.setContentsMargins(0, 0, 0, 0)
    return input, widget, layout

def toneSelectOption(app: HalfToneSelectorApp, field: str, opt: dict) -> K.QPushButton:
    button = K.QPushButton(opt['name'])
    button.setStyleSheet(f'''
        QPushButton {{
            border: 0px solid transparent;
            border-radius: 0px;
            padding: 5px 10px;
            background-color: {app.style['button'].name()};
        }}
        QPushButton::hover {{
            background-color: {app.style['window'].name()};
        }}
    ''')

    def handleClick(getColor):
        color = getColor()
        if color:
            app.setState(**{field: color})

    button.clicked.connect(lambda: handleClick(opt['getColor']))
    return button

def toneSelectColorStyle(app: HalfToneSelectorApp, field: str):
    lch = getattr(app.s, field)
    color = oklchToQColor(lch)
    fontColor = scaleColor(color, 1, 96 if color.value() < 128 else -96)
    return f'''
        QPushButton {{
            border: 0px solid transparent;
            border-radius: 0px;
            padding: 5px 10px;
            background-color: {color.name()};
            color: {fontColor.name()};
        }}
        QPushButton::hover {{
            border: 1px solid {app.style['window'].name()};
        }}
    '''

def handleColorDialog(app: HalfToneSelectorApp, field: str) -> None:
    def handler(color: K.QColor) -> None:
        if color and color.isValid():
            lch = qcolorToOklch(color)
            app.setState(**{field: lch})
    lch = getattr(app.s, field)
    openFGColorDialog(oklchToQColor(lch), handler)

def toneSelectColor(app: HalfToneSelectorApp, field: str) -> K.QPushButton:
    button = K.QPushButton('Color')
    button.setSizePolicy(K.QSizePolicy.Expanding, K.QSizePolicy.Fixed)
    def updateColor():
        button.setStyleSheet(toneSelectColorStyle(app, field))
    updateColor()
    button.clicked.connect(lambda: handleColorDialog(app, field))
    app.registerCallback([field], updateColor)
    return button

def toneSelectLabel(app: HalfToneSelectorApp, name: str) -> K.QLabel:
    label = K.QLabel(name)
    label.setStyleSheet(f'''
        QLabel {{
            border: 0px solid transparent;
            border-radius: 0px;
            padding: 5px 10px;
            background-color: {app.style['label'].name()};
        }}
    ''')
    return label

def toneSelectWidget(
        app: HalfToneSelectorApp,
        field: str,
        name: str,
        opts: List[dict],
        ) -> K.QWidget:
    childWidgets = [
        toneSelectLabel(app, name),
        toneSelectColor(app, field),
        *[toneSelectOption(app, field, opt) for opt in opts]
    ]
    widget, layout = addLayout(qlayout=K.QHBoxLayout, childWidgets=childWidgets)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(1)
    return widget

def toneLightWidget(app: HalfToneSelectorApp) -> K.QWidget:
    widget = toneSelectWidget(
        app, 'light', 'Light',
        [
            {'name': 'FG', 'getColor': qcolorToOklchFunc(getFGColor)},
            {'name': 'BG', 'getColor': qcolorToOklchFunc(getBGColor)},
        ],
    )
    return widget

def toneDarkWidget(app: HalfToneSelectorApp) -> K.QWidget:
    widget = toneSelectWidget(
        app, 'dark', 'Dark',
        [
            {'name': 'Half', 'getColor': app.halfLight},
            {'name': 'FG', 'getColor': qcolorToOklchFunc(getFGColor)},
            {'name': 'BG', 'getColor': qcolorToOklchFunc(getBGColor)},
        ],
    )
    return widget

def toneChromaWidget(app: HalfToneSelectorApp) -> K.QDoubleSpinBox:
    input, widget, _  = labeledInput('Chroma', K.QDoubleSpinBox)
    input.setRange(-1, 1)
    input.setSingleStep(0.05)
    input.setValue(app.s.k)
    input.valueChanged.connect(lambda d: app.setState(k=d))
    return widget

def toneSettings(app: HalfToneSelectorApp) -> K.QWidget:
    widget, layout = addLayout(
        qlayout=K.QVBoxLayout,
        qwidget=lambda: K.QGroupBox('Base Tones'),
        childWidgets=[
            toneLightWidget(app),
            toneDarkWidget(app),
            toneChromaWidget(app),
        ])
    layout.setContentsMargins(2, 2, 2, 2)
    layout.setSpacing(5)
    return widget

def colorBarPatch(app: HalfToneSelectorApp, lch: Float3) -> K.QPushButton:
    patch = K.QPushButton()
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
            border: 0.5px solid {app.style['background'].name()};
        }}
    ''')
    patch.clicked.connect(lambda: setFGColor(color))
    return patch

def colorBarPatches(app: HalfToneSelectorApp, hts: HalfToneSet) -> K.QWidget:
    patches = [colorBarPatch(app, tone) for tone in hts.tones]
    widget, layout = addLayout(qlayout=K.QHBoxLayout, childWidgets=patches)
    widget.setStyleSheet(f'''
        QWidget {{
            border: 0px solid transparent;
            border-radius: 0px;
            background-color: {app.style['background'].name()};
        }}
    ''')
    layout.setContentsMargins(1, 1, 1, 1)
    layout.setSpacing(1)
    return widget

def colorBarName(app: HalfToneSelectorApp, hts: HalfToneSet) -> K.QLineEdit:
    line = K.QLineEdit(hts.name)
    line.textChanged.connect(lambda text: setattr(hts, 'name', text))
    font = line.font()
    font.setPointSize(8)
    line.setFont(font)
    fm = K.QFontMetrics(line.font())
    line.setFixedHeight(fm.height())
    line.setStyleSheet(f'''
        QLineEdit {{
            font-size: 8pt;
            padding: 0px;
            margin: 0px;
            border: 0px solid transparent;
        }}
        QLineEdit::Hover {{
            background-color: {app.style['background'].name()};
        }}
    ''')
    return line

def colorBarMain(app: HalfToneSelectorApp, hts: HalfToneSet) -> K.QWidget:
    widget, layout = addLayout(
        qlayout=K.QVBoxLayout,
        childWidgets=[
            colorBarPatches(app, hts),
            colorBarName(app, hts),
        ])
    widget.setStyleSheet(f'''
        QWidget {{
            background-color: {app.style['label'].name()};
        }}
    ''')
    layout.setContentsMargins(5, 2, 5, 2)
    layout.setSpacing(1)
    return widget

def colorBarDelete(app: HalfToneSelectorApp, hts: HalfToneSet) -> K.QWidget:
    button = K.QPushButton()
    button.setIcon(K.Krita.instance().icon('deletelayer'))
    button.setSizePolicy(K.QSizePolicy.Fixed, K.QSizePolicy.Fixed)
    button.clicked.connect(lambda: app.removeHalfToneSet(hts))
    return button

def colorBarWidget(app: HalfToneSelectorApp, hts: HalfToneSet) -> K.QWidget:
    widget, layout = addLayout(
        qlayout=K.QHBoxLayout,
        childWidgets=[
            colorBarMain(app, hts),
            colorBarDelete(app, hts),
        ])
    layout.setAlignment(K.Qt.AlignTop)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(1)
    return widget

def samplingCountWidget(app: HalfToneSelectorApp) -> K.QWidget:
    spinBox, widget, _ = labeledInput('Count', K.QSpinBox)
    spinBox.setRange(1, 10)
    spinBox.setValue(app.s.count)
    spinBox.valueChanged.connect(lambda i: app.setState(count=i))
    return widget

def toggleButton(name: str, state: bool, onClick: Callable[[], None]) -> K.QPushButton:
    button = K.QPushButton(name)
    button.setCheckable(True)
    button.setChecked(state)
    button.clicked.connect(onClick)
    return button

def samplingChoiceWidget(app: HalfToneSelectorApp) -> K.QWidget:
    linear = toggleButton('Linear', not app.s.cos, lambda: app.setState(cos=False))
    cosine = toggleButton('Cosine', app.s.cos, lambda: app.setState(cos=True))

    def handleCos():
        linear.setChecked(not app.s.cos)
        cosine.setChecked(app.s.cos)

    app.registerCallback(['cos'], handleCos)
    widget, layout = addLayout(qlayout=K.QHBoxLayout, childWidgets=[linear, cosine])
    layout.setContentsMargins(0, 0, 0, 0)
    return widget

def samplingSettings(app: HalfToneSelectorApp) -> K.QWidget:
    widget, layout = addLayout(
        qlayout=K.QVBoxLayout,
        qwidget=lambda: K.QGroupBox('Sampling'),
        childWidgets=[
            samplingCountWidget(app),
            K.QLabel('Distribution:'),
            samplingChoiceWidget(app),
        ])
    layout.setContentsMargins(2, 2, 2, 2)
    layout.setSpacing(5)
    return widget

def visCheckBox(app: HalfToneSelectorApp) -> K.QCheckBox:
    def text():
        return 'Settings (visible)' if app.visible else 'Settings (hidden)'

    def handleToggle(box: K.QCheckBox, checked: bool):
        app.visible = checked
        box.setText(text())

    box = K.QCheckBox(text())
    box.setChecked(app.visible)
    box.toggled.connect(lambda checked: handleToggle(box, checked))
    return box

def settingsWidget(app: HalfToneSelectorApp) -> K.QWidget:
    def create():
        hts = generateColors(app.s)
        app.addHalfToneSet(hts)

    createButton = K.QPushButton('Create half tones')
    createButton.clicked.connect(create)

    widget, layout = addLayout(
        qlayout=K.QVBoxLayout,
        childWidgets=[
            toneSettings(app),
            samplingSettings(app),
            createButton,
        ])
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(5)
    layout.setAlignment(K.Qt.AlignTop)
    app.registerCallback(['visible'], lambda: widget.setVisible(app.visible))
    return widget

def addScrollArea(widget: K.QWidget) -> K.QScrollArea:
    scrollArea = K.QScrollArea()
    scrollArea.setWidgetResizable(True)
    scrollArea.setWidget(widget)
    return scrollArea

def palette(app: HalfToneSelectorApp) -> K.QWidget:
    colorBars = [colorBarWidget(app, hts) for hts in app.s.halfTones]
    widget, layout = addLayout(qlayout=K.QVBoxLayout, childWidgets=colorBars)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(5)

    def handleAdd(i: int):
        hts = app.s.halfTones[i]
        layout.addWidget(colorBarWidget(app, hts))

    def handleRemove(i: int):
        item = layout.itemAt(i)
        layout.removeItem(item)
        item.widget().deleteLater()

    app.registerCallback(['addHalfToneSet'], handleAdd)
    app.registerCallback(['removeHalfToneSet'], handleRemove)
    return widget

def halfToneSelectorWidget(app: HalfToneSelectorApp) -> K.QWidget:
    widget, layout = addLayout(
        qlayout=K.QVBoxLayout,
        childWidgets=[
            visCheckBox(app),
            settingsWidget(app),
            palette(app),
        ])
    layout.setSpacing(5)
    layout.setAlignment(K.Qt.AlignTop)
    widget.setStyleSheet(f'''
        QWidget {{
            background-color: {app.style['background'].name()};
        }}
    ''')
    scrollArea = addScrollArea(widget)
    return scrollArea
