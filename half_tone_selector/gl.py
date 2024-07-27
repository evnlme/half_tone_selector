from ctypes import CFUNCTYPE, c_int, c_uint, c_float, c_void_p, POINTER
from pathlib import Path
from PyQt5.QtGui import ( # type: ignore
    QOpenGLShader,
    QOpenGLShaderProgram,
    QOpenGLContext,
)

shadersDir = Path(__file__).resolve().parent / 'shaders'

_funcTypes = {
    'glClear': CFUNCTYPE(None, c_uint),
    'glClearColor': CFUNCTYPE(None, c_float, c_float, c_float, c_float),
    'glDrawArrays': CFUNCTYPE(None, c_int, c_int, c_int),
    'glViewport': CFUNCTYPE(None, c_int, c_int, c_int, c_int),
    'glGenTextures': CFUNCTYPE(None, c_uint, POINTER(c_uint)),
    'glBindTexture': CFUNCTYPE(None, c_uint, c_uint),
    'glActiveTexture': CFUNCTYPE(None, c_uint),
    'glTexImage2D': CFUNCTYPE(None, c_uint, c_int, c_int, c_uint, c_uint, c_int, c_uint, c_uint, c_void_p),
    'glGenFramebuffers': CFUNCTYPE(None, c_uint, POINTER(c_uint)),
    'glBindFramebuffer': CFUNCTYPE(None, c_uint, c_uint),
    'glFramebufferTexture2D': CFUNCTYPE(None, c_uint, c_uint, c_uint, c_uint, c_int),
    'glDrawBuffers': CFUNCTYPE(None, c_uint, POINTER(c_uint)),
    'glReadBuffer': CFUNCTYPE(None, c_uint),
    'glReadPixels': CFUNCTYPE(None, c_int, c_int, c_uint, c_uint, c_uint, c_uint, POINTER(c_uint)),
    'glPixelStorei': CFUNCTYPE(None, c_uint, c_int),
}

def getGLFunc(context, name):
    sipPointer = context.getProcAddress(name.encode())
    funcType = _funcTypes.get(name)
    return funcType(int(sipPointer))

def loadGLFuncs(obj, context):
    for name in _funcTypes.keys():
        setattr(obj, name, getGLFunc(context, name))
    obj.GL_TRIANGLE_STRIP = 0x0005
    obj.FRAMEBUFFER = 0x8D40
    obj.COLOR_ATTACHMENT0 = 0x8CE0
    obj.COLOR_ATTACHMENT1 = 0x8CE1
    obj.TEXTURE_2D = 0x0DE1
    obj.TEXTURE0 = 0x84C0
    obj.TEXTURE1 = 0x84C1
    obj.R8 = 0x8229
    obj.RGB8 = 0x8051
    obj.RGBA8 = 0x8058
    obj.RED = 0x1903
    obj.RGB = 0x1907
    obj.RGBA = 0x1908
    obj.UNSIGNED_BYTE = 0x1401
    obj.UNPACK_ALIGNMENT = 0x0CF5
    obj.DEPTH_BUFFER_BIT = 0x0100
    obj.COLOR_BUFFER_BIT = 0x4000

def getVersionHeader(context: QOpenGLContext) -> str:
    version = context.format().version()
    if context.isOpenGLES():
        profile = 'es'
        precision = 'precision highp float;\n'
    else:
        profile = 'core'
        precision = ''
    versionHeader = f'#version {version[0]}{version[1]}0 {profile}\n{precision}'
    return versionHeader

def createShader(shaderType: int, code: str) -> QOpenGLShader:
    shader = QOpenGLShader(shaderType)
    shader.compileSourceCode(code)
    if not shader.isCompiled():
        raise Exception(shader.log())
    return shader

def loadShader(context: QOpenGLContext, name: Path) -> QOpenGLShader:
    if name.suffix == '.vert':
        shaderType = QOpenGLShader.Vertex
    elif name.suffix == '.frag':
        shaderType = QOpenGLShader.Fragment
    else:
        raise Exception(f'Unknown suffix in {str(name)}')
    versionHeader = getVersionHeader(context)
    with name.open() as f:
        code = f.read()
    return createShader(shaderType, versionHeader + code)

def createProgram(vertexShader: QOpenGLShader, fragmentShader: QOpenGLShader) -> QOpenGLShaderProgram:
    prog = QOpenGLShaderProgram()
    prog.addShader(vertexShader)
    prog.addShader(fragmentShader)
    prog.link()
    if not prog.isLinked():
        raise Exception(prog.log())
    return prog
