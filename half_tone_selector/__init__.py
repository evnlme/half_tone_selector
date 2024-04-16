try:
    from .half_tone_selector import HalfToneSelector

    HalfToneSelector.addToKrita()
except ModuleNotFoundError:
    pass
