from math import atan2, sqrt, cos, sin, pi, hypot, dist
from .matrix import (
    Vec,
    Mat,
    clamp,
    invertMat,
    transposeMat,
    multMat,
    multMatVec,
    scaleVec,
)
from .autocomp import createComps

def fromHexRgb(rgb: str) -> Vec:
    # #RRGGBB
    # 0123456
    return [int(rgb[2*x+1:2*x+3], 16) / 255 for x in range(3)]

# For transfer function: https://bottosson.github.io/posts/colorwrong/
def fromLinearRgb(linearRgb: Vec) -> Vec:
    """Linear RGB to sRGB"""
    def fromLinear(x: float) -> float:
        # [0, 1] -> [0, 1]
        if x >= 0.0031308:
            return (1.055) * x**(1.0/2.4) - 0.055
        else:
            return 12.92 * x
    return [fromLinear(clamp(x, 0, 1)) for x in linearRgb]

def toLinearRgb(rgb: Vec) -> Vec:
    """sRGB to Linear RGB"""
    def toLinear(x: float) -> float:
        # [0, 1] -> [0, 1]
        if x >= 0.04045:
            return ((x + 0.055)/(1 + 0.055))**2.4
        else:
            return x / 12.92
    return [toLinear(x) for x in rgb]

def deriveRgbToXyzMat() -> Mat:
    """
    Primaries: https://github.com/colour-science/colour/blob/develop/colour/models/rgb/datasets/srgb.py
    Whitepoint: https://github.com/colour-science/colour/blob/develop/colour/colorimetry/datasets/illuminants/chromaticity_coordinates.py
    """
    primaries = [
        [0.64, 0.33],
        [0.30, 0.60],
        [0.15, 0.06],
    ]
    for p in primaries:
        p.append(1.0-sum(p))
    primaries = transposeMat(primaries)
    whitepoint = [0.3127, 0.3290]
    whitepoint.append(1.0-sum(whitepoint))
    whitepoint = [w/whitepoint[1] for w in whitepoint]
    coeff = multMatVec(invertMat(primaries), whitepoint)
    return [[xi*c for xi, c in zip(row, coeff)] for row in primaries]

_rgbToXyzMat = deriveRgbToXyzMat()
_xyzToRgbMat = invertMat(_rgbToXyzMat)

def convertLinearRgbToXyz(linearRgb: Vec) -> Vec:
    return multMatVec(_rgbToXyzMat, linearRgb)

def convertXyzToLinearRgb(xyz: Vec) -> Vec:
    return multMatVec(_xyzToRgbMat, xyz)

# https://colour.readthedocs.io/en/latest/_modules/colour/models/oklab.html
_xyzToLmsMat = [
    [0.8189330101, 0.3618667424,-0.1288597137],
    [0.0329845436, 0.9293118715, 0.0361456387],
    [0.0482003018, 0.2643662691, 0.6338517070],
]
_lmsToOklabMat = [
    [0.2104542553, 0.7936177850,-0.0040720468],
    [1.9779984951,-2.4285922050, 0.4505937099],
    [0.0259040371, 0.7827717662,-0.8086757660],
]
_lmsToXyzMat = invertMat(_xyzToLmsMat)
_oklabToLmsMat = invertMat(_lmsToOklabMat)

def toOklab(xyz: Vec) -> Vec:
    """XYZ to Oklab"""
    lms1 = multMatVec(_xyzToLmsMat, xyz)
    lms2 = [x**(1/3) for x in lms1]
    lab = multMatVec(_lmsToOklabMat, lms2)
    return lab

def fromOklab(lab: Vec) -> Vec:
    """Oklab to XYZ"""
    lms2 = multMatVec(_oklabToLmsMat, lab)
    lms1 = [x**3 for x in lms2]
    xyz = multMatVec(_lmsToXyzMat, lms1)
    return xyz

def toOklch(lab: Vec) -> Vec:
    """Oklab to Oklch"""
    l, a, b = lab
    c = hypot(a, b)
    h = atan2(b, a)
    return [l, c, h]

def fromOklch(lch: Vec) -> Vec:
    """Oklch to Oklab"""
    l, c, h = lch
    a = c * cos(h)
    b = c * sin(h)
    return [l, a, b]

convertColorSpace = createComps([
    (fromHexRgb, 'StringRGB', 'sRGB'),
    (fromLinearRgb, 'LinearRGB', 'sRGB'),
    (toLinearRgb, 'sRGB', 'LinearRGB'),
    (convertLinearRgbToXyz, 'LinearRGB', 'XYZ'),
    (convertXyzToLinearRgb, 'XYZ', 'LinearRGB'),
    (toOklab, 'XYZ', 'Oklab'),
    (fromOklab, 'Oklab', 'XYZ'),
    (toOklch, 'Oklab', 'Oklch'),
    (fromOklch, 'Oklch', 'Oklab'),
])

def getColorError(lab: Vec) -> float:
    linear = convertColorSpace(lab, 'Oklab', 'LinearRGB')
    clampedLinear = [clamp(x, 0, 1) for x in linear]
    clampedLab = convertColorSpace(clampedLinear, 'LinearRGB', 'Oklab')
    return dist(lab, clampedLab)

def interp(a: float, b: float, t: float) -> float:
    return a*(1-t) + b*t

def interpolateOklch(lch1: Vec, lch2: Vec, t: float, k: float) -> Vec:
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
