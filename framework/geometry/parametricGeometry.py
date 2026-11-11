"""
Superfície paramétrica S(u,v) = (x(u,v), y(u,v), z(u,v)).
Base: STEMKOSKI & PASCALE (2022), seções 4.3.4, 5.2.4 e 6.3.4.

Normal em um ponto = produto vetorial das derivadas parciais (aproximadas por
diferenças finitas de passo h):  n = (S(u+h,v) - S(u,v)) x (S(u,v+h) - S(u,v)).

Adaptação: nos polos de uma esfera e no ápice de um cone as derivadas se anulam
(vetor nulo -> divisão por zero -> NaN). Aqui a normal é recalculada um pouco
"para dentro" da superfície e há um valor de reserva para triângulos degenerados.
"""
import numpy
from geometry.geometry import Geometry


def _unitNormal(P0, P1, P2):
    n = numpy.cross(numpy.array(P1) - numpy.array(P0), numpy.array(P2) - numpy.array(P0))
    length = numpy.linalg.norm(n)
    if length < 1e-12:
        return None
    return n / length


class ParametricGeometry(Geometry):

    def __init__(self, uStart, uEnd, uResolution, vStart, vEnd, vResolution, surfaceFunction):
        super().__init__()
        deltaU = (uEnd - uStart) / uResolution
        deltaV = (vEnd - vStart) / vResolution
        h = 0.0001

        positions, uvs, vertexNormals = [], [], []
        for uIndex in range(uResolution + 1):
            posRow, uvRow, nRow = [], [], []
            for vIndex in range(vResolution + 1):
                u = uStart + uIndex * deltaU
                v = vStart + vIndex * deltaV
                posRow.append(surfaceFunction(u, v))
                uvRow.append([uIndex / uResolution, vIndex / vResolution])

                n = _unitNormal(surfaceFunction(u, v), surfaceFunction(u + h, v), surfaceFunction(u, v + h))
                if n is None:
                    # ponto singular: reavalia ligeiramente para dentro do domínio
                    v2 = v - 2 * h if vIndex == vResolution else v + 2 * h
                    n = _unitNormal(surfaceFunction(u, v2), surfaceFunction(u + h, v2),
                                    surfaceFunction(u, v2 + h))
                if n is None:
                    n = numpy.array([0.0, 1.0, 0.0])
                nRow.append(n)
            positions.append(posRow)
            uvs.append(uvRow)
            vertexNormals.append(nRow)

        positionData, colorData, uvData = [], [], []
        vertexNormalData, faceNormalData = [], []
        C1, C2, C3 = [1, 0, 0], [0, 1, 0], [0, 0, 1]
        C4, C5, C6 = [0, 1, 1], [1, 0, 1], [1, 1, 0]

        for xIndex in range(uResolution):
            for yIndex in range(vResolution):
                pA = positions[xIndex + 0][yIndex + 0]
                pB = positions[xIndex + 1][yIndex + 0]
                pD = positions[xIndex + 0][yIndex + 1]
                pC = positions[xIndex + 1][yIndex + 1]
                positionData += [pA, pB, pC, pA, pC, pD]
                colorData += [C1, C2, C3, C4, C5, C6]

                uvA = uvs[xIndex + 0][yIndex + 0]
                uvB = uvs[xIndex + 1][yIndex + 0]
                uvD = uvs[xIndex + 0][yIndex + 1]
                uvC = uvs[xIndex + 1][yIndex + 1]
                uvData += [uvA, uvB, uvC, uvA, uvC, uvD]

                nA = vertexNormals[xIndex + 0][yIndex + 0]
                nB = vertexNormals[xIndex + 1][yIndex + 0]
                nD = vertexNormals[xIndex + 0][yIndex + 1]
                nC = vertexNormals[xIndex + 1][yIndex + 1]
                vertexNormalData += [nA, nB, nC, nA, nC, nD]

                fn0 = _unitNormal(pA, pB, pC)
                fn1 = _unitNormal(pA, pC, pD)
                if fn0 is None:
                    fn0 = (nA + nB + nC) / numpy.linalg.norm(nA + nB + nC)
                if fn1 is None:
                    fn1 = (nA + nC + nD) / numpy.linalg.norm(nA + nC + nD)
                faceNormalData += [fn0, fn0, fn0, fn1, fn1, fn1]

        self.addAttribute("vec3", "vertexPosition", positionData)
        self.addAttribute("vec3", "vertexColor", colorData)
        self.addAttribute("vec2", "vertexUV", uvData)
        self.addAttribute("vec3", "vertexNormal", vertexNormalData)
        self.addAttribute("vec3", "faceNormal", faceNormalData)
        self.countVertices()
