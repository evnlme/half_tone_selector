from math import atan2, sqrt, cos, sin, pi, hypot
from .lib import (
    Float3,
    multiply,
    interp,
)

def fromHexRgb(rgb: str) -> Float3:
    # #RRGGBB
    # 0123456
    return [int(rgb[2*x+1:2*x+3], 16) / 255 for x in range(3)]

# For transfer function: https://bottosson.github.io/posts/colorwrong/
def fromLinearRgb(linearRgb: Float3) -> Float3:
    """Linear RGB to sRGB"""
    def fromLinear(x: float) -> float:
        # [0, 1] -> [0, 1]
        if x >= 0.0031308:
            return (1.055) * x**(1.0/2.4) - 0.055
        else:
            return 12.92 * x
    return [fromLinear(x) for x in linearRgb]

def toLinearRgb(rgb: Float3) -> Float3:
    """sRGB to Linear RGB"""
    def toLinear(x: float) -> float:
        # [0, 1] -> [0, 1]
        if x >= 0.04045:
            return ((x + 0.055)/(1 + 0.055))**2.4
        else:
            return x / 12.92
    return [toLinear(x) for x in rgb]

# For oklab: https://bottosson.github.io/posts/oklab/
def toOklab(linearRgb: Float3) -> Float3:
    """Linear RGB to Oklab"""
    mat1 = [
        [0.4122214708, 0.5363325363, 0.0514459929],
        [0.2119034982, 0.6806995451, 0.1073969566],
        [0.0883024619, 0.2817188376, 0.6299787005],
    ]
    mat2 = [
        [0.2104542553,  0.7936177850, -0.0040720468],
        [1.9779984951, -2.4285922050,  0.4505937099],
        [0.0259040371,  0.7827717662, -0.8086757660],
    ]
    x1 = multiply(mat1, linearRgb)
    x2 = [x**(1/3) for x in x1]
    lab = multiply(mat2, x2)
    return lab

def fromOklab(lab: Float3) -> Float3:
    """Oklab to linear RGB"""
    mat1 = [
        [1,  0.3963377774,  0.2158037573],
        [1, -0.1055613458, -0.0638541728],
        [1, -0.0894841775, -1.2914855480],
    ]
    mat2 = [
        [ 4.0767416621, -3.3077115913,  0.2309699292],
        [-1.2684380046,  2.6097574011, -0.3413193965],
        [-0.0041960863, -0.7034186147,  1.7076147010],
    ]
    x1 = multiply(mat1, lab)
    x2 = [x**3 for x in x1]
    linearRgb = multiply(mat2, x2)
    return linearRgb

def toOklch(lab: Float3) -> Float3:
    """Oklab to Oklch"""
    l, a, b = lab
    c = hypot(a, b)
    h = atan2(b, a)
    return [l, c, h]

def fromOklch(lch: Float3) -> Float3:
    """Oklch to Oklab"""
    l, c, h = lch
    a = c * cos(h)
    b = c * sin(h)
    return [l, a, b]

def rgbToOklch(rgb: Float3) -> Float3:
    """sRGB to Oklch"""
    linear = toLinearRgb(rgb)
    lab = toOklab(linear)
    lch = toOklch(lab)
    return lch

def oklchToRgb(lch: Float3) -> Float3:
    """Oklch to sRGB"""
    lab = fromOklch(lch)
    linear = fromOklab(lab)
    rgb = fromLinearRgb(linear)
    return rgb

def linearRgbToOklch(linearRgb: Float3) -> Float3:
    """sRGB to Oklch"""
    lab = toOklab(linearRgb)
    lch = toOklch(lab)
    return lch

def oklchToLinearRgb(lch: Float3) -> Float3:
    """Oklch to linear RGB"""
    lab = fromOklch(lch)
    linear = fromOklab(lab)
    return linear

def interpolateOklch(lch1: Float3, lch2: Float3, t: float, k: float) -> Float3:
    # t: [0, 1], k: [-1, 1]
    l1, c1, h1 = lch1
    l2, c2, h2 = lch2
    l = interp(l1, l2, t)
    c = interp(c1, c2, t)

    if c1 == 0 or c2 == 0:
        return [l, c, h1 if c2 == 0 else h2]

    angle = abs(h2 - h1)
    smallAngle = min(angle, 2*pi - angle)
    rotationDirection = -1 if (angle <= pi) ^ (h1 <= h2) else 1
    h = (h1 + h2)/2 + (angle > pi)*pi

    p = smallAngle / 2
    cosp = cos(p)
    d1 = interp(-p, p, t)
    d2 = interp(2*pi - p, p, t)
    if k >= 2*cosp - 1:
        if cosp != 1:
            a = interp(2*cosp - cos(d1), cos(d1), (k + 1 - 2*cosp)/(2 - 2*cosp))
            b = sin(d1)
            c *= hypot(a, b)
            h += atan2(b, a) * rotationDirection
        else:
            h = h1
    else:
        if cosp != 0:
            a = interp(2*cosp - cos(d1), cos(d2), -(k + 1 - 2*cosp)/(2*cosp))
            b = interp(sin(d1), sin(d2), -(k + 1 - 2*cosp)/(2*cosp))
            c *= hypot(a, b)
            h += atan2(b, a) * rotationDirection
        else:
            c = interp(c1, -c2, t)
            if c < 0:
                c = -c
                h = h2
            else:
                h = h1

    return [l, c, h % (2*pi)]
