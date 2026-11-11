"""
Matrizes de transformação 4x4 (coordenadas homogêneas).

Base: STEMKOSKI & PASCALE (2022), cap. 3 (seção 3.3), cap. 5 (look-at, 5.7.2.1)
e ortográfica (5.7.3).
Adaptações deste projeto:
  * makeScale aceita escala uniforme (como no livro) OU por eixo (sx, sy, sz);
  * todas as matrizes são sempre float (evita dtype inteiro por engano).

Convenção: vetores-coluna; a transformação de um ponto é  p' = M @ p.
Logo, em  A @ B  a matriz B é aplicada ANTES de A.
"""
import numpy
from math import sin, cos, tan, pi
from numpy import subtract, divide, cross
from numpy.linalg import norm


class Matrix(object):

    @staticmethod
    def makeIdentity():
        return numpy.identity(4, dtype=float)

    @staticmethod
    def makeTranslation(x, y, z):
        m = numpy.identity(4, dtype=float)
        m[0, 3], m[1, 3], m[2, 3] = x, y, z
        return m

    @staticmethod
    def makeRotationX(angle):
        c, s = cos(angle), sin(angle)
        return numpy.array([[1, 0, 0, 0],
                            [0, c, -s, 0],
                            [0, s, c, 0],
                            [0, 0, 0, 1]], dtype=float)

    @staticmethod
    def makeRotationY(angle):
        c, s = cos(angle), sin(angle)
        return numpy.array([[c, 0, s, 0],
                            [0, 1, 0, 0],
                            [-s, 0, c, 0],
                            [0, 0, 0, 1]], dtype=float)

    @staticmethod
    def makeRotationZ(angle):
        c, s = cos(angle), sin(angle)
        return numpy.array([[c, -s, 0, 0],
                            [s, c, 0, 0],
                            [0, 0, 1, 0],
                            [0, 0, 0, 1]], dtype=float)

    @staticmethod
    def makeScale(sx, sy=None, sz=None):
        # makeScale(s) -> escala uniforme (livro);  makeScale(sx,sy,sz) -> por eixo
        if sy is None:
            sy = sz = sx
        return numpy.array([[sx, 0, 0, 0],
                            [0, sy, 0, 0],
                            [0, 0, sz, 0],
                            [0, 0, 0, 1]], dtype=float)

    @staticmethod
    def makePerspective(angleOfView=60, aspectRatio=1, near=0.1, far=1000):
        # Projeção em perspectiva (frustum -> cubo de clip space [-1,1]^3).
        a = angleOfView * pi / 180.0
        d = 1.0 / tan(a / 2)
        r = aspectRatio
        b = (far + near) / (near - far)
        c = 2 * far * near / (near - far)
        return numpy.array([[d / r, 0, 0, 0],
                            [0, d, 0, 0],
                            [0, 0, b, c],
                            [0, 0, -1, 0]], dtype=float)

    @staticmethod
    def makeOrthographic(left=-1, right=1, bottom=-1, top=1, near=-1, far=1):
        # Projeção ortográfica: caixa -> cubo [-1,1]^3 (usada pela "câmera da luz").
        return numpy.array([[2 / (right - left), 0, 0, -(right + left) / (right - left)],
                            [0, 2 / (top - bottom), 0, -(top + bottom) / (top - bottom)],
                            [0, 0, -2 / (far - near), -(far + near) / (far - near)],
                            [0, 0, 0, 1]], dtype=float)

    @staticmethod
    def makeLookAt(position, target):
        # Matriz de OBJETO (não de view): colunas = right, up, -forward, posição.
        worldUp = numpy.array([0.0, 1.0, 0.0])
        forward = subtract(target, position)
        right = cross(forward, worldUp)
        # forward paralelo a worldUp -> right nulo; perturba worldUp um pouco
        if norm(right) < 0.001:
            right = cross(forward, worldUp + numpy.array([0.001, 0, 0]))
        up = cross(right, forward)
        forward = divide(forward, norm(forward))
        right = divide(right, norm(right))
        up = divide(up, norm(up))
        return numpy.array([[right[0], up[0], -forward[0], position[0]],
                            [right[1], up[1], -forward[1], position[1]],
                            [right[2], up[2], -forward[2], position[2]],
                            [0, 0, 0, 1]], dtype=float)
