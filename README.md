# Half Tone Selector

Generate half tones from light and dark tones depending on the angle of incidence.

By default, it will compute 5 tones at angles 15, 30, 45, 60, and 75 degrees.

## Usage

1. Select the light and dark tones. Clicking on the color brings up the color dialog. "FG" and "BG" copy the foreground and background colors respectively. "Half" computes the tone halfway between the light tone and black.
2. "Count" is the number of half tones between the light and dark tones.
3. "Cosine" and "Exponent" control which tones are chosen. A linear set of tones can be achieved by toggling off "Cosine" and setting "Exponent" to 1.
4. The button "Create" generates a set of tones below the button. Multiple sets of tones can be generated. A set of tones can be cleared by clicking on the delete button. Clicking on a tone updates the foreground color to that tone.

## Example

![Example](./example.png)