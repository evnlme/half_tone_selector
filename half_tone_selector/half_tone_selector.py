import krita as K # type: ignore
from pathlib import Path
from .state import AppState
from .app import HalfToneSelectorApp
from .widget import HalfToneSelectorWidget

def loadAppState() -> AppState:
    # Data store so state isn't lost when Krita closes.
    dataPath = Path(__file__).resolve().parent.parent / 'half_tone_selector_data.json'
    s = AppState()
    if dataPath.exists():
        s = AppState.from_file(dataPath)
    # Save when Krita closes.
    notifier = K.Krita.instance().notifier()
    notifier.applicationClosing.connect(lambda: s.to_file(dataPath))
    return s

class HalfToneSelector(K.DockWidget):
    def __init__(self, app: HalfToneSelectorApp) -> None:
        super().__init__()
        self.app = app
        self.setWindowTitle('Half Tone Selector')
        self._appWidget = HalfToneSelectorWidget(app)
        self.setWidget(self._appWidget)

        app.registerCallback(['visible'], self.handleVisible)

    # notifies when views are added or removed
    def canvasChanged(self, canvas):
        pass

    def handleVisible(self) -> None:
        tempWidth = self.width()
        tempHeight = self.height()
        w = self.app.s.visibleMeta.width
        h = self.app.s.visibleMeta.height
        if w and h:
            self.resize(w, h)
        self.app.s.visibleMeta.width = tempWidth
        self.app.s.visibleMeta.height = tempHeight

    @staticmethod
    def addToKrita() -> None:
        s = loadAppState()
        app = HalfToneSelectorApp(s)

        half_tone_selector_factory = K.DockWidgetFactory(
            'half_tone_selector',
            K.DockWidgetFactoryBase.DockRight,
            lambda: HalfToneSelector(app))
        instance = K.Krita.instance()
        instance.addDockWidgetFactory(half_tone_selector_factory)
