from geometry.parametricGeometry import ParametricGeometry
from math import sin, cos, pi


class TorusGeometry(ParametricGeometry):
    """
    Toro (extensão deste projeto, no mesmo estilo das superfícies do livro).
    Eixo = y; raio maior R (centro do tubo), raio do tubo r:
        S(u,v) = ((R + r cos v) sin u,  r sin v,  (R + r cos v) cos u)
    Usado para correntes, anéis e a marca de inspeção no chão.
    """
    def __init__(self, majorRadius=1, minorRadius=0.25, majorSegments=32, minorSegments=8):
        def S(u, v):
            ring = majorRadius + minorRadius * cos(v)
            return [ring * sin(u), minorRadius * sin(v), ring * cos(u)]
        super().__init__(0, 2 * pi, majorSegments, 0, 2 * pi, minorSegments, S)
