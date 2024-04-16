import krita as K # type: ignore
from pathlib import Path
from .state import AppState
from .app import HalfToneSelectorApp
from .widget import halfToneSelectorWidget

def loadAppState() -> AppState:
    # Data store so state isn't lost when Krita closes.
    dataPath = Path(__file__).resolve().parent / '_data.json'
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
        self.setWindowTitle('Half Tone Selector')
        widget = halfToneSelectorWidget(app)
        self.setWidget(widget)

    # notifies when views are added or removed
    def canvasChanged(self, canvas):
        pass

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
