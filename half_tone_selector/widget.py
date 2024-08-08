import math
import krita as K # type: ignore
from typing import Callable, Optional, List, Tuple
from .matrix import (
    Vec,
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
    input, widget, _  = labeledInput('Curve', K.QDoubleSpinBox)
    input.setRange(-1, 1)
    input.setSingleStep(0.05)
    input.setValue(app.s.k)
    input.valueChanged.connect(lambda d: app.setState(k=d))
    return widget

def toneNumbers(app: HalfToneSelectorApp, field: str) -> K.QWidget:
    l, c, h = getattr(app.s, field)
    def updateState(l, c, h):
        l0, c0, h0 = getattr(app.s, field)
        app.setState(**{field: (
            l0 if l is None else l,
            c0 if c is None else c,
            h0 if h is None else h,
        )})
    def degrees(radians: float) -> float:
        return math.degrees(radians) % 360
    def radians(degrees: float) -> float:
        return math.radians(degrees) % (2*math.pi)

    lInput = K.QDoubleSpinBox()
    lInput.setPrefix('L: ')
    lInput.setRange(0, 1)
    lInput.setSingleStep(0.050)
    lInput.setDecimals(3)
    lInput.setValue(l)
    lInput.valueChanged.connect(lambda d: updateState(d, None, None))

    cInput = K.QDoubleSpinBox()
    cInput.setPrefix('C: ')
    cInput.setRange(0, 0.333)
    cInput.setSingleStep(0.010)
    cInput.setDecimals(3)
    cInput.setValue(c)
    cInput.valueChanged.connect(lambda d: updateState(None, d, None))

    hInput = K.QDoubleSpinBox()
    hInput.setPrefix('H: ')
    hInput.setRange(-10, 370)
    hInput.setSingleStep(10)
    hInput.setDecimals(0)
    hInput.setValue(degrees(h))
    hInput.valueChanged.connect(lambda d: updateState(None, None, radians(d)))

    def handleUpdate():
        l, c, h = getattr(app.s, field)
        if not math.isclose(l, lInput.value()):
            lInput.setValue(l)
        if not math.isclose(c, cInput.value()):
            cInput.setValue(c)
        if not math.isclose(degrees(h), hInput.value()):
            hInput.setValue(degrees(h))

    app.registerCallback([field], handleUpdate)

    childWidgets = [lInput, cInput, hInput]
    widget, layout = addLayout(qlayout=K.QHBoxLayout, childWidgets=childWidgets)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setAlignment(K.Qt.AlignRight)
    return widget

def toneSettings(app: HalfToneSelectorApp) -> K.QWidget:
    widget, layout = addLayout(
        qlayout=K.QVBoxLayout,
        qwidget=lambda: K.QGroupBox('Base Tones'),
        childWidgets=[
            toneLightWidget(app),
            toneNumbers(app, 'light'),
            toneDarkWidget(app),
            toneNumbers(app, 'dark'),
            toneChromaWidget(app),
        ])
    layout.setContentsMargins(2, 2, 2, 2)
    layout.setSpacing(5)
    return widget

def updatePatchColor(app: HalfToneSelectorApp, patch: K.QWidget, lch: Vec) -> None:
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
    patch.setToolTip(str(lch))
    patch.clicked.connect(lambda: setFGColor(color))

def colorBarPatch(app: HalfToneSelectorApp, lch: Vec) -> K.QPushButton:
    patch = K.QPushButton()
    patch.setMinimumSize(18, 18)
    updatePatchColor(app, patch, lch)
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

def setLineHeight(line: K.QLineEdit, pt: int) -> None:
    font = line.font()
    font.setPointSize(pt)
    line.setFont(font)
    fm = K.QFontMetrics(line.font())
    line.setFixedHeight(fm.height())

def colorBarName(app: HalfToneSelectorApp, hts: HalfToneSet) -> K.QLineEdit:
    line = K.QLineEdit(hts.name)
    line.setPlaceholderText('Name')
    line.textChanged.connect(lambda text: setattr(hts, 'name', text))
    setLineHeight(line, 8)
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
    def handleVisible():
        return line.setVisible(app.visible or bool(line.text()))
    handleVisible()
    app.registerCallback(['visible'], handleVisible)
    line.destroyed.connect(
        lambda: app.unregisterCallback(['visible'], handleVisible))
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
    def handleVisible():
        button.setVisible(app.visible)
    handleVisible()
    app.registerCallback(['visible'], handleVisible)
    button.destroyed.connect(
        lambda: app.unregisterCallback(['visible'], handleVisible))
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

def updatePreviewPatches(app: HalfToneSelectorApp, patches: K.QWidget) -> None:
    hts = generateColors(app.s)
    patchesLayout = patches.layout().itemAt(0).widget().layout()
    n = len(hts.tones)
    m = patchesLayout.count()

    for i in range(m):
        patch = patchesLayout.itemAt(i).widget()
        patch.setVisible(i < n)
    for i, tone in zip(range(n), hts.tones):
        if i < m:
            patch = patchesLayout.itemAt(i).widget()
            patch.clicked.disconnect()
            updatePatchColor(app, patch, tone)
        else:
            patchesLayout.addWidget(colorBarPatch(app, tone))

def previewPatches(app: HalfToneSelectorApp) -> K.QWidget:
    hts = generateColors(app.s)
    hts.name = 'Preview'
    widget = colorBarMain(app, hts)
    # Make name read only
    widget.layout().itemAt(1).widget().setReadOnly(True)

    app.registerCallback(
        fields=['light', 'dark', 'k', 'count', 'cos'],
        cb=lambda: updatePreviewPatches(app, widget))
    return widget

def previewSettings(app: HalfToneSelectorApp) -> K.QWidget:
    widget, layout = addLayout(
        qlayout=K.QVBoxLayout,
        qwidget=lambda: K.QGroupBox('Preview'),
        childWidgets=[
            previewPatches(app),
        ])
    layout.setContentsMargins(2, 2, 2, 2)
    layout.setSpacing(5)
    return widget

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
            previewSettings(app),
            createButton,
        ])
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(5)
    layout.setAlignment(K.Qt.AlignTop)
    widget.setVisible(app.visible)
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

from .toneSettings import toneSettings as ts

class HalfToneSelectorWidget(K.QSplitter):
    def __init__(self, app: HalfToneSelectorApp) -> None:
        super().__init__()
        self._app = app
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
        tsVisuals = ts(app)
        self.addWidget(addScrollArea(widget))
        self.addWidget(tsVisuals)

        self.setSizes(self._app.s.visibleMeta.splitterSizes)
        self.splitterMoved.connect(lambda pos, index: self._updateSplitterSizes())

        tsVisuals.setVisible(app.visible)
        app.registerCallback(['visible'], lambda: tsVisuals.setVisible(app.visible))

    def _updateSplitterSizes(self) -> None:
        if self._app.visible:
            self._app.s.visibleMeta.splitterSizes = self.sizes()
