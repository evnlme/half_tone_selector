from typing import List

Float3 = List[float]
Mat3x3 = List[Float3]

def dot(a: Float3, b: Float3) -> float:
    return sum(ai * bi for ai, bi in zip(a, b))

def multiply(m: Mat3x3, x: Float3) -> Float3:
    return [dot(row, x) for row in m]

def scale3(x: Float3, s: float) -> Float3:
    return [s*xi for xi in x]

def interp(a: float, b: float, t: float) -> float:
    return a*(1-t) + b*t

def interp3(a: Float3, b: Float3, t: float) -> Float3:
    return [interp(ai, bi, t) for ai, bi in zip(a, b)]

def clamp(xmin: float, xmax: float, x: float) -> float:
    return max(min(x, xmax), xmin)
