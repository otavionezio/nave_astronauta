"""
Modelagem por composição de primitivas do framework.

Cada peça de um modelo (placa de armadura, cano, torre...) é uma primitiva unitária
(caixa 1x1x1, esfera de diâmetro 1, cilindro de diâmetro 1 e altura 1, cone, prisma,
pirâmide, toro) à qual aplicamos ESCALA, ROTAÇÃO e TRANSLAÇÃO:

        M = T(pos) @ Ry(ry) @ Rx(rx) @ Rz(rz) @ S(sx, sy, sz)

(a escala age primeiro, a translação por último). As normais usam a inversa transposta
da parte linear de M, de modo que a iluminação continua correta com escala não uniforme.

O PartBuilder agrupa as peças de uma mesma ARTICULAÇÃO pelo material e as funde numa
única malha (Geometry.merge do framework): poucas chamadas de desenho por quadro,
mas a hierarquia de animação continua nas articulações (Groups).
"""
import numpy
from core.matrix import Matrix
from core.group import Group
from core.mesh import Mesh
from geometry.geometry import Geometry
from geometry.boxGeometry import BoxGeometry
from geometry.sphereGeometry import SphereGeometry
from geometry.cylinderGeometry import CylinderGeometry
from geometry.coneGeometry import ConeGeometry
from geometry.prismGeometry import PrismGeometry
from geometry.pyramidGeometry import PyramidGeometry
from geometry.torusGeometry import TorusGeometry
from math import pi, sqrt


def _arrays(geometry):
    g = geometry.attributes
    return {k: numpy.asarray(g[n].data, dtype=float)
            for k, n in (("pos", "vertexPosition"), ("nrm", "vertexNormal"),
                         ("fnrm", "faceNormal"), ("uv", "vertexUV"))}


class PrimitiveLibrary(object):
    """Primitivas unitárias, geradas uma única vez (os dados são copiados para cada peça)."""
    _cache = {}

    @classmethod
    def get(cls, kind):
        if kind not in cls._cache:
            if kind == "box":
                g = BoxGeometry(1, 1, 1)
            elif kind == "sphere":
                g = SphereGeometry(0.5, 16, 10)
            elif kind == "cylinder":
                g = CylinderGeometry(0.5, 1.0, 16, 1)
            elif kind == "cone":
                g = ConeGeometry(0.5, 1.0, 16, 1)
            elif kind == "prism3":          # prisma triangular; vértice em +z
                g = PrismGeometry(0.5, 1.0, 3, 1)
            elif kind == "pyramid":         # base quadrada de lado 1, alinhada aos eixos
                g = PyramidGeometry(sqrt(0.5), 1.0, 4, 1)
                g.applyMatrix(Matrix.makeRotationY(pi / 4))
            elif kind == "torus":           # raio maior 0.4, tubo 0.03
                g = TorusGeometry(0.4, 0.03, 24, 6)
            else:
                raise Exception("primitiva desconhecida: " + kind)
            cls._cache[kind] = _arrays(g)
        return cls._cache[kind]


class PartBuilder(object):

    def __init__(self):
        self.batches = {}          # id(material) -> (material, [peças])
        self.partCount = 0

    def add(self, kind, material, pos=(0, 0, 0), size=(1, 1, 1), rot=(0, 0, 0), uvTile=None):
        """rot = (rx, ry, rz) em radianos; aplicadas na ordem Rz, depois Rx, depois Ry."""
        prim = PrimitiveLibrary.get(kind)
        M = (Matrix.makeTranslation(*pos) @ Matrix.makeRotationY(rot[1]) @ Matrix.makeRotationX(rot[0])
             @ Matrix.makeRotationZ(rot[2]) @ Matrix.makeScale(*size))
        linear = M[0:3, 0:3]
        normalMatrix = numpy.linalg.inv(linear).T

        def norm(a):
            n = a @ normalMatrix.T
            l = numpy.linalg.norm(n, axis=1, keepdims=True)
            l[l == 0] = 1.0
            return n / l

        uv = prim["uv"].copy()
        if uvTile is not None and kind == "box":
            sx, sy, sz = size           # x±:(z,y)  y±:(x,z)  z±:(x,y)
            faceSizes = [(sz, sy)] * 2 + [(sx, sz)] * 2 + [(sx, sy)] * 2
            for f, (fu, fv) in enumerate(faceSizes):
                uv[f * 6:(f + 1) * 6, 0] *= fu / uvTile
                uv[f * 6:(f + 1) * 6, 1] *= fv / uvTile

        part = {"pos": prim["pos"] @ linear.T + M[0:3, 3], "nrm": norm(prim["nrm"]),
                "fnrm": norm(prim["fnrm"]), "uv": uv}
        self.batches.setdefault(id(material), (material, []))[1].append(part)
        self.partCount += 1

    def build(self, parent):
        """Funde as peças por material e cria uma Mesh por material sob `parent`."""
        meshes = []
        for material, parts in self.batches.values():
            cat = lambda key: numpy.concatenate([p[key] for p in parts])
            geometry = Geometry()
            positions = cat("pos")
            geometry.addAttribute("vec3", "vertexPosition", positions)
            geometry.addAttribute("vec3", "vertexColor", numpy.ones_like(positions))
            geometry.addAttribute("vec2", "vertexUV", cat("uv"))
            geometry.addAttribute("vec3", "vertexNormal", cat("nrm"))
            geometry.addAttribute("vec3", "faceNormal", cat("fnrm"))
            geometry.countVertices()
            mesh = Mesh(geometry, material)
            parent.add(mesh)
            meshes.append(mesh)
        return meshes


def joint(parent, position=(0, 0, 0)):
    """Cria uma articulação (Group) em `position`, filha de `parent`."""
    g = Group()
    g.setPosition(position)
    parent.add(g)
    g.restPosition = tuple(position)
    return g


def poseTransform(position, rx=0.0, ry=0.0, rz=0.0):
    """Transformação local de uma articulação: T(pos) @ Ry @ Rx @ Rz  (recalculada a cada
    quadro a partir dos parâmetros; nada é acumulado, então não há deriva numérica)."""
    return (Matrix.makeTranslation(*position) @ Matrix.makeRotationY(ry)
            @ Matrix.makeRotationX(rx) @ Matrix.makeRotationZ(rz))
