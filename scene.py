"""
Ambiente: plataforma de inspeção militar flutuando no espaço.

  * deck (caixa 40x40) com textura de imagem repetida (UV proporcional ao tamanho) — recebe
    as sombras da nave e do astronauta;
  * pad circular elevado com anéis emissivos e as marcas de partida/inspeção;
  * quatro pilares góticos nos cantos, contêineres e barris (compõem sem competir com os modelos);
  * planeta distante (esfera iluminada pelo sol) e campo de estrelas (pontos) que acompanha a câmera.
"""
import math
import random
from core.group import Group
from core.mesh import Mesh
from core.matrix import Matrix
from geometry.geometry import Geometry
from geometry.sphereGeometry import SphereGeometry
from material.pointMaterial import PointMaterial
from material.lambertMaterial import LambertMaterial
from modeling import PartBuilder
from animation import MARK, ASTRONAUT_START

PI = math.pi


class Environment(object):

    def __init__(self, M):
        self.root = Group()
        b = PartBuilder()
        add = lambda kind, mat, pos, size, rot=(0, 0, 0), tile=None: b.add(kind, mat, pos, size, rot, tile)

        # --- deck 36x36: a textura se repete a cada 4 m (uvTile) ---
        add("box", M.deck, (0, -0.30, 0), (36, 0.60, 36), tile=4.0)
        for sx, sz, w, d in ((0, -18.15, 36.6, 0.3), (0, 18.15, 36.6, 0.3), (-18.15, 0, 0.3, 36), (18.15, 0, 0.3, 36)):
            add("box", M.hullDark, (sx, 0.1, sz), (w, 0.30, d))                       # meio-fio
            add("box", M.gold, (sx, 0.27, sz), (w * (1 if d < 1 else 0.02), 0.04, d * (1 if w < 1 else 0.02)))

        # --- pad de inspeção ---
        padCenter = (-0.8, 1.2)
        add("cylinder", M.graphite, (padCenter[0], 0.06, padCenter[1]), (8.4, 0.12, 8.4))
        add("cylinder", M.hullDark, (padCenter[0], 0.13, padCenter[1]), (7.0, 0.03, 7.0))

        # --- pilares góticos ---
        for sx in (-15, 15):
            for sz in (-15, 15):
                add("box", M.graphite, (sx, 0.25, sz), (1.9, 0.5, 1.9))
                add("cylinder", M.hullDark, (sx, 3.9, sz), (1.1, 6.8, 1.1))
                for y in (1.2, 3.9, 6.5):
                    add("cylinder", M.bronze, (sx, y, sz), (1.35, 0.18, 1.35))
                add("box", M.graphite, (sx, 7.5, sz), (1.6, 0.4, 1.6))
                add("pyramid", M.bronze, (sx, 8.5, sz), (1.4, 1.6, 1.4))
                add("sphere", M.gold, (sx, 9.5, sz), (0.35, 0.35, 0.35))

        # --- contêineres e barris ---
        add("box", M.hull, (11.0, 0.95, -7.0), (3.4, 1.9, 1.6), (0, 0.25, 0), tile=3.0)
        add("box", M.hull, (11.3, 2.85, -7.1), (3.2, 1.9, 1.6), (0, 0.32, 0), tile=3.0)
        add("box", M.hullDark, (8.3, 0.7, -11.0), (1.6, 1.4, 1.6), (0, -0.2, 0), tile=3.0)
        add("box", M.hull, (-11.0, 0.8, -9.0), (2.6, 1.6, 1.4), (0, -0.4, 0), tile=3.0)
        for i, (x, z) in enumerate(((13.0, -3.0), (13.9, -2.3), (12.4, -2.1))):
            add("cylinder", M.bronze, (x, 0.65, z), (0.9, 1.3, 0.9))
            add("cylinder", M.graphite, (x, 1.32, z), (0.95, 0.06, 0.95))
        b.build(self.root)

        # --- peças emissivas (sem iluminação) ---
        e = PartBuilder()
        # anel externo do pad, anel da marca de inspeção, anel de partida e mira
        e.add("torus", M.emissiveGold, (padCenter[0], 0.16, padCenter[1]), (8.6, 1.0, 8.6))
        e.add("torus", M.visor, (MARK[0], 0.16, MARK[1]), (1.8, 1.0, 1.8))
        e.add("box", M.visor, (MARK[0], 0.15, MARK[1]), (1.1, 0.02, 0.07))
        e.add("box", M.visor, (MARK[0], 0.15, MARK[1]), (0.07, 0.02, 1.1))
        e.add("torus", M.emissiveGold, (ASTRONAUT_START[0], 0.16, ASTRONAUT_START[1]), (1.3, 1.0, 1.3))
        for sx in (-15, 15):
            for sz in (-15, 15):
                e.add("sphere", M.visor, (sx, 6.5, sz), (0.28, 0.28, 0.28))
        for mesh in e.build(self.root):
            mesh.castShadow = False

        # --- planeta distante (não recebe nem projeta sombra) ---
        planetMat = LambertMaterial(useShadow=False, properties={"baseColor": [0.62, 0.24, 0.12]})
        self.planet = Mesh(SphereGeometry(55, 48, 24), planetMat)
        self.planet.setPosition((-190, 75, -270))
        self.planet.castShadow = False
        self.root.add(self.planet)

        # --- estrelas: pontos numa esfera grande, acompanham a câmera (skybox) ---
        rng = random.Random(40000)
        positions, colors = [], []
        for _ in range(1600):
            z = rng.uniform(-1, 1)
            a = rng.uniform(0, 2 * PI)
            r = math.sqrt(1 - z * z)
            positions.append([450 * r * math.cos(a), 450 * z, 450 * r * math.sin(a)])
            tint = rng.choice(([1, 1, 1], [0.8, 0.88, 1.0], [1.0, 0.92, 0.75]))
            k = rng.uniform(0.35, 1.0)
            colors.append([tint[0] * k, tint[1] * k, tint[2] * k])
        geometry = Geometry()
        geometry.addAttribute("vec3", "vertexPosition", positions)
        geometry.addAttribute("vec3", "vertexColor", colors)
        geometry.countVertices()
        self.stars = Mesh(geometry, PointMaterial({"useVertexColors": True, "pointSize": 2}))
        self.stars.castShadow = False
        self.root.add(self.stars)

    def update(self, cameraPosition):
        self.stars.setPosition(cameraPosition)
