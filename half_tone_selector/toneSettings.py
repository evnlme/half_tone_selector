import math
from ctypes import c_uint
from PyQt5.QtCore import Qt, QTimer # type: ignore
from PyQt5.QtGui import ( # type: ignore
    QOpenGLFramebufferObject,
    QColor,
)
from PyQt5.QtWidgets import ( # type: ignore
    QOpenGLWidget,
    QWidget,
    QVBoxLayout,
    QLabel,
    QSlider,
    QSizePolicy,
)
from .gl import (
    loadGLFuncs,
    loadShader,
    shadersDir,
    createProgram,
)
from .color import (
    toOklch,
    fromOklch,
    getColorError,
)
from .app import (
    HalfToneSelectorApp,
)

class ChromaHueSelector(QOpenGLWidget):
    def __init__(self, app: HalfToneSelectorApp) -> None:
        super().__init__()
        self._app = app
        self._width = 800
        self._height = 600
        self._isMousePressed = False
        self._activeColor = 1
        self._changeCallback = lambda: True

        def updateColor1():
            self._color1 = fromOklch(app.s.light)
            self._activeColor = 1
            self.colorError = getColorError(self._color1)
            self._changeCallback()

        def updateColor2():
            self._color2 = fromOklch(app.s.dark)
            self._activeColor = 2
            self.colorError = getColorError(self._color2)
            self._changeCallback()

        app.registerCallback(['dark'], updateColor2)
        app.registerCallback(['light'], updateColor1)
        updateColor2()
        updateColor1()

    def setChangeCallback(self, func):
        self._changeCallback = func

    def initializeGL(self):
        self.setMouseTracking(True)
        # self.setAttribute(Qt.WA_AlwaysStackOnTop)
        loadGLFuncs(self, self.context())

        vert1 = loadShader(self.context(), shadersDir / 'lab1.vert')
        frag1 = loadShader(self.context(), shadersDir / 'lab1.frag')
        frag2 = loadShader(self.context(), shadersDir / 'lab2.frag')
        self._prog_1 = createProgram(vert1, frag1)
        self._prog_2 = createProgram(vert1, frag2)
        self._init_fbo()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(int(1000.0 / 60.0)) # 60 FPS

    def _init_fbo(self):
        w, h = self._width, self._height
        fbo = QOpenGLFramebufferObject(w, h, self.COLOR_ATTACHMENT0, self.TEXTURE_2D)
        fbo.addColorAttachment(w, h)
        fbo.bind()
        self.glDrawBuffers(2, (c_uint * 2)(self.COLOR_ATTACHMENT0, self.COLOR_ATTACHMENT1))
        # self.glReadBuffer(self.COLOR_ATTACHMENT1)
        fbo.release()
        self._fbo = fbo

    def _draw_1(self):
        w, h = self._width, self._height
        self._prog_1.bind()
        self._prog_1.setUniformValue('u_resolution', w, h)
        if self._activeColor == 1:
            self._prog_1.setUniformValue('u_lightness', self._color1[0])
        else: # self._activeColor == 2
            self._prog_1.setUniformValue('u_lightness', self._color2[0])

        self._fbo.bind()
        self.glClearColor(0.0, 0.0, 0.0, 0.0)
        self.glClear(self.COLOR_BUFFER_BIT | self.DEPTH_BUFFER_BIT)
        self.glDrawArrays(self.GL_TRIANGLE_STRIP, 0, 4)
        self._fbo.release()

    def _draw_2(self):
        self._prog_2.bind()
        self._prog_2.setUniformValue('u_resolution', self._width, self._height)
        if self._activeColor == 1:
            self._prog_2.setUniformValue('lab_1', *self._color1)
            self._prog_2.setUniformValue('lab_2', *self._color2)
        else: # self._activeColor == 2
            self._prog_2.setUniformValue('lab_2', *self._color1)
            self._prog_2.setUniformValue('lab_1', *self._color2)
        self._prog_2.setUniformValue('pattern', 0)
        self._prog_2.setUniformValue('e', 1)

        textures = self._fbo.textures()
        self.glActiveTexture(self.TEXTURE0)
        self.glBindTexture(self.TEXTURE_2D, textures[0])
        self.glActiveTexture(self.TEXTURE1)
        self.glBindTexture(self.TEXTURE_2D, textures[1])

        QOpenGLFramebufferObject.bindDefault()
        self.glClearColor(0.0, 0.0, 0.0, 0.0)
        self.glClear(self.COLOR_BUFFER_BIT | self.DEPTH_BUFFER_BIT)
        self.glDrawArrays(self.GL_TRIANGLE_STRIP, 0, 4)

    def paintGL(self):
        self._draw_1()
        self._draw_2()

    def resizeGL(self, width, height):
        self._width = width
        self._height = height
        self.glViewport(0, 0, width, height)
        self._init_fbo()

    def handleColorChange(self, coord):
        if self._activeColor == 1:
            lightness = self._color1[0]
        else: # self._activeColor == 2
            lightness = self._color2[0]
        color = [lightness, coord[0], coord[1]]
        lch = toOklch(color)
        if self._activeColor == 1:
            self._app.setState(light=lch)
        else: # self._activeColor == 2
            self._app.setState(dark=lch)

    def getCoord(self, x, y):
        """Coord from pixel xy."""
        w2, h2 = self._width / 2, self._height / 2
        s = min(w2, h2)
        coord = (0.4*(x-w2)/s, 0.4*(h2-y)/s)
        length = math.hypot(*coord)
        if length > 0.333:
            coord = (coord[0] / length * 0.333, coord[1] / length * 0.333)
        return coord

    def mouseMoveEvent(self, event):
        p = event.pos()
        coord = self.getCoord(p.x(), p.y())
        if self._isMousePressed:
            self.handleColorChange(coord)

    def mousePressEvent(self, event):
        self._isMousePressed = True
        p = event.pos()
        coord = self.getCoord(p.x(), p.y())
        d1 = math.dist(coord, self._color1[1:3])
        d2 = math.dist(coord, self._color2[1:3])
        if d1 < 0.1 or d2 < 0.1:
            self._activeColor = 1 if d1 < d2 else 2
        self.handleColorChange(coord)

    def mouseReleaseEvent(self, event):
        self._isMousePressed = False

    def leaveEvent(self, event):
        self._isMousePressed = False

class LightnessSelector(QOpenGLWidget):
    def __init__(self, app: HalfToneSelectorApp):
        super().__init__()
        self._app = app
        self._width = 800
        self._height = 600
        self._activeColor = 1
        self._isMousePressed = False

        def updateColor1():
            self._color1 = fromOklch(app.s.light)
            self._activeColor = 1

        def updateColor2():
            self._color2 = fromOklch(app.s.dark)
            self._activeColor = 2

        app.registerCallback(['dark'], updateColor2)
        app.registerCallback(['light'], updateColor1)
        updateColor2()
        updateColor1()

    def initializeGL(self):
        loadGLFuncs(self, self.context())

        vert = loadShader(self.context(), shadersDir / 'lab1.vert')
        frag = loadShader(self.context(), shadersDir / 'lab3.frag')
        self._prog = createProgram(vert, frag)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(int(1000.0 / 60.0)) # 60 FPS

    def paintGL(self):
        self._prog.bind()
        self._prog.setUniformValue('u_resolution', self._width, self._height)
        if self._activeColor == 1:
            self._prog.setUniformValue('lab_1', *self._color1)
            self._prog.setUniformValue('lab_2', *self._color2)
        else: # self._activeColor == 2
            self._prog.setUniformValue('lab_1', *self._color2)
            self._prog.setUniformValue('lab_2', *self._color1)

        self.glClearColor(0.0, 0.0, 0.0, 0.0)
        self.glClear(self.COLOR_BUFFER_BIT | self.DEPTH_BUFFER_BIT)
        self.glDrawArrays(self.GL_TRIANGLE_STRIP, 0, 4)

    def resizeGL(self, width, height):
        self._width = width
        self._height = height
        self.glViewport(0, 0, width, height)

    def handleColorChange(self, coord):
        if self._activeColor == 1:
            ab = self._color1[1:]
        else: # self._activeColor == 2
            ab = self._color2[1:]
        color = [coord, *ab]
        lch = toOklch(color)
        if self._activeColor == 1:
            self._app.setState(light=lch)
        else: # self._activeColor == 2
            self._app.setState(dark=lch)

    def mouseMoveEvent(self, event):
        p = event.pos()
        coord = p.x() / self._width
        if self._isMousePressed:
            self.handleColorChange(coord)

    def mousePressEvent(self, event):
        self._isMousePressed = True
        p = event.pos()
        coord = p.x() / self._width
        d1 = abs(coord - self._color1[0])
        d2 = abs(coord - self._color2[0])
        if d1 < 0.1 or d2 < 0.1:
            self._activeColor = 1 if d1 < d2 else 2
        self.handleColorChange(coord)

    def mouseReleaseEvent(self, event):
        self._isMousePressed = False

    def leaveEvent(self, event):
        self._isMousePressed = False

def toneSettings(app: HalfToneSelectorApp):
    widget = QWidget()
    layout = QVBoxLayout()
    # layout.setAlignment(Qt.AlignTop)
    widget.setLayout(layout)

    chs = ChromaHueSelector(app)
    layout.addWidget(chs, 11)

    ls = LightnessSelector(app)
    layout.addWidget(ls, 1)

    label = QLabel(f'\u0394E={chs.colorError:.3f}')
    chs.setChangeCallback(lambda: label.setText(f'\u0394E={chs.colorError:.3f}'))
    layout.addWidget(label, alignment=Qt.AlignTop)
    return widget
