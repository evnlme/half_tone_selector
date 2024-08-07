# Half Tone Selector

This plugin generates half tones from user defined light and dark tones. It is useful for shading and practice. If you know the angle between the light rays and what you are drawing, you will know which tone to use. By default, 5 half tones are generated at 15, 30, 45, 60, and 75 degrees. The light and dark tones correspond to 0 and 90 degrees.

![Default](./images/selection.png)

## Usage

1. Select the light and dark tones. Clicking on the color brings up the color dialog. "FG" and "BG" copy the foreground and background colors respectively. "Half" computes the tone halfway between the light tone and black. Use LCH inputs to fine tune the colors.
2. "Curve" controls how the hue and chroma changes as the tone moves from light to dark.
3. "Count" is the number of half tones between the light and dark tones.
4. Distribution controls which tones are chosen. "Linear" produces a linear distribution of tones. "Cosine" will produce tones according to a linear distribution of angles.
5. The button "Create" generates a set of tones below the button. Multiple sets of tones can be generated. A set of tones can be cleared by clicking on the delete button. Clicking on a tone updates the foreground color to that tone.

The "Settings" checkbox can be toggled to show and hide the settings. This option is provided to make using the half tones easier. If you want to create or manage half tones, the settings can be unhidden.

## Install

Please follow Krita's official docs for [installing a custom plugin](https://docs.krita.org/en/user_manual/python_scripting/install_custom_python_plugin.html).

## Example

![Example](./images/example01.png)

## Tech

### Color space

Interpolation is done in the OKLCH color space. OKLCH is a perceptual color space. It represents color as lightness, chroma, and hue. This color space is used because it is more predictable for artists.

### Curve

There are many paths that connect two points in the polar coordinate space. I identified 3 key paths to include:

1. If chroma is the same between light and dark, hold chroma constant and take the short path through hue.
2. If chroma is the same between light and dark, hold chroma constant and take the long path through hue.
3. Shortest path in regular grid coordinate space.

The inbetween paths are generated as a linear interpolation of the key paths.

![Curves](./images/curves.png)

The current method works when chroma is the same. But when chroma is different, it's not as elegant. The key paths may need to be reevaluated.

## References

Plugin development:

* https://scripting.krita.org/lessons/plugins-create
* https://api.kde.org/krita/html/index.html
* https://doc.qt.io/qt-6/widget-classes.html
* https://www.riverbankcomputing.com/static/Docs/PyQt6/index.html
* https://invent.kde.org/graphics/krita/-/blob/master/plugins/python/plugin_importer/plugin_importer.py
* https://registry.khronos.org/OpenGL-Refpages/gl4/index.php
* https://numpy.org/doc/stable/reference/index.html

Plugins:

* https://github.com/kaichi1342/PaletteGenerator
* https://github.com/KnowZero/Krita-PythonPluginDeveloperTools/tree/main
* https://github.com/EyeOdin/Pigment.O

Color spaces:

* https://developer.chrome.com/docs/css-ui/high-definition-css-color-guide
* https://bottosson.github.io/posts/oklab/
* https://cie.co.at/data-tables
* https://stackoverflow.com/questions/3407942/rgb-values-of-visible-spectrum
* https://jcgt.org/published/0002/02/01/
* https://oklch.com
* https://en.wikipedia.org/wiki/Color_difference
* https://en.wikipedia.org/wiki/CIELAB_color_space
* https://colour.readthedocs.io/en/latest/index.html#