from geometry.parametricGeometry import ParametricGeometry
from geometry.polygonGeometry import PolygonGeometry
from core.matrix import Matrix
from math import sin, cos, pi


class CylindricalGeometry(ParametricGeometry):
    """
    Base de cilindro, prisma, cone e pirâmide (STEMKOSKI & PASCALE, 2022, 4.3.6).
    Eixo = y, altura centrada na origem; o raio varia linearmente de radiusBottom
    (y = -h/2) até radiusTop (y = +h/2). As tampas vêm de PolygonGeometry
    transformados e fundidos com merge().
    """

    def __init__(self, radiusTop=1, radiusBottom=1, height=1,
                 radialSegments=32, heightSegments=4, closedTop=True, closedBottom=True):
        def S(u, v):
            r = v * radiusTop + (1 - v) * radiusBottom
            return [r * sin(u), height * (v - 0.5), r * cos(u)]

        super().__init__(0, 2 * pi, radialSegments, 0, 1, heightSegments, S)

        if closedTop:
            top = PolygonGeometry(radialSegments, radiusTop)
            top.applyMatrix(Matrix.makeTranslation(0, height / 2, 0)
                            @ Matrix.makeRotationY(-pi / 2) @ Matrix.makeRotationX(-pi / 2))
            self.merge(top)
        if closedBottom:
            bottom = PolygonGeometry(radialSegments, radiusBottom)
            bottom.applyMatrix(Matrix.makeTranslation(0, -height / 2, 0)
                               @ Matrix.makeRotationY(-pi / 2) @ Matrix.makeRotationX(pi / 2))
            self.merge(bottom)
