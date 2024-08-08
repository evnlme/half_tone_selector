"""
https://github.com/evnlme/fun/blob/master/permutation.py
https://github.com/evnlme/fun/blob/master/matrix.py
https://github.com/evnlme/fun/blob/master/gausselim.py
"""
from copy import deepcopy
from typing import (
    List,
    Tuple,
    Callable,
    Any,
)

Perm = List[int]
Vec = List[float]
Mat = List[Vec]

def invertPerm(p: Perm) -> None:
    n = len(p)
    for i in range(n):
        if p[i] < 0:
            continue
        prev = i
        curr = p[prev]
        next = p[curr]
        while True:
            p[curr] = prev-n
            if curr == i:
                break
            prev, curr, next = curr, next, p[next]
    for i in range(n):
        p[i] += n

def permute(p: Perm, **kwargs) -> None:
    n = len(p)
    i: int = kwargs['start'] if 'start' in kwargs else 0
    j: int = kwargs['stop'] if 'stop' in kwargs else n
    read: Callable[[int], Any]
    write: Callable[[int, Any], None]
    if 'read' in kwargs and 'write' in kwargs:
        read = kwargs['read']
        write = kwargs['write']
    elif 'arr' in kwargs:
        arr: List[Any] = kwargs['arr']
        read = arr.__getitem__
        write = arr.__setitem__
    else:
        raise ValueError('Expected "read" and "write" in kwargs.')

    for k in range(i, j):
        if p[k] < 0:
            continue
        prev = k
        curr = p[prev]
        prevValue = read(prev)
        while p[curr] >= 0:
            temp = read(curr)
            write(curr, prevValue)
            prevValue = temp
            prev, curr = curr, p[curr]
            p[prev] -= n
        write(curr, prevValue)
    for k in range(i, j):
        p[k] += n

def permuteMatCols(p: Perm, mat: Mat) -> None:
    n = len(p)
    def read(key):
        return [mat[rowId][key] for rowId in range(n)]
    def write(key, value):
        for rowId in range(n):
            mat[rowId][key] = value[rowId]
    permute(p, read=read, write=write)

def multMat(m1: Mat, m2: Mat) -> Mat:
    m = len(m1)
    n = len(m2[0])
    p = len(m1[0]) # == len(m2)
    return [[
        sum(m1[i][k]*m2[k][j] for k in range(p))
        for j in range(n)]
        for i in range(m)]

def dot(v1: Vec, v2: Vec) -> float:
    return sum(v1i * v2i for v1i, v2i in zip(v1, v2))

def multMatVec(mat: Mat, vec: Vec) -> Vec:
    return [dot(row, vec) for row in mat]

def scaleVec(vec: Vec, s: float) -> Vec:
    return [s*vi for vi in vec]

def _findPivot(mat: Mat, k: int, n: int) -> int:
    value = abs(mat[k][k])
    valueId = k
    for rowId in range(k, n):
        row = mat[rowId]
        if abs(row[k]) > value:
            value = abs(row[k])
            valueId = rowId
    return valueId

def _elim(l: Mat, u: Mat, k: int, n: int) -> None:
    for rowId in range(k+1, n):
        c = u[rowId][k] / u[k][k]
        l[rowId][k] = c
        u[rowId][k] = 0
        for colId in range(k+1, n):
            u[rowId][colId] -= c*u[k][colId]

def _permute(p: Perm, l: Mat, k: int, n: int) -> None:
    def read(key):
        return l[key][k]
    def write(key, value):
        l[key][k] = value
    permute(p, i=k+1, j=n, read=read, write=write)

def _plu(p: Perm, l: Mat, u: Mat, k: int, n: int) -> None:
    if k == n:
        return
    pivotRowId = _findPivot(u, k, n)
    u[k], u[pivotRowId] = u[pivotRowId], u[k]
    _elim(l, u, k, n)
    _plu(p, l, u, k+1, n)
    _permute(p, l, k, n)
    p[k], p[pivotRowId] = p[pivotRowId], p[k]

def plu(mat: Mat) -> Tuple[Perm, Mat, Mat]:
    n = len(mat)
    p = list(range(n))
    l = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    u = deepcopy(mat)
    _plu(p, l, u, 0, n)
    invertPerm(p)
    return p, l, u

def invertUpper(u: Mat) -> Mat:
    n = len(u)
    mat = [[0.0]*n for _ in range(n)]
    for k in range(n):
        mat[k][k] = 1 / u[k][k]
        i = k - 1
        while i >= 0:
            mat[i][k] = -sum(u[i][j]*mat[j][k] for j in range(k, i, -1)) / u[i][i]
            i -= 1
    return mat

def invertLower(l: Mat) -> Mat:
    n = len(l)
    mat = [[0.0]*n for _ in range(n)]
    for k in range(n):
        mat[k][k] = 1 / l[k][k]
        i = k + 1
        while i < n:
            mat[i][k] = -sum(l[i][j]*mat[j][k] for j in range(0, i)) / l[i][i]
            i += 1
    return mat

def invertMat(mat: Mat) -> Mat:
    p, l, u = plu(mat)
    lInv = invertLower(l)
    uInv = invertUpper(u)
    matInv = multMat(uInv, lInv)
    permuteMatCols(p, matInv)
    return matInv

def transposeMat(mat: Mat) -> Mat:
    m = len(mat)
    n = len(mat[0])
    return [[mat[j][i] for j in range(m)] for i in range(n)]

def clamp(x: float, xmin: float, xmax: float) -> float:
    return max(min(x, xmax), xmin)
