try:
    from .widget import registerPlugin

    registerPlugin()
except ModuleNotFoundError:
    pass
