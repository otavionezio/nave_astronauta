"""
Nave de guerra gótica (inspirada nas referências: casco cinza longo com alcovas em arco,
proa em cunha clara com friso dourado, torre escalonada à ré, antenas, dois propulsores).

HIERARQUIA
  root   : posição no mundo + orientação (yaw = guinada, pitch = arfagem, roll = rolagem)
   └ body: escala uniforme 0.75
      ├ malhas do casco (peças fundidas por material: ver modeling.PartBuilder)
      ├ engineL / engineR : nós nos bicos dos motores
      │    ├ chama externa (cone laranja)  ┐ escala em z proporcional à potência
      │    ├ chama interna (cone claro)    ┘
      │    └ disco de brilho (cilindro emissivo)
      ├ balizas (esferas emissivas que piscam)
      └ luz pontual dos motores (cor proporcional à potência)

Convenção: a "frente" (proa) é -z; a ré (motores) fica em +z.

Matriz da nave:  W = T(pos) @ Ry(yaw) @ Rx(pitch) @ Rz(roll) @ S(0.75)
"""
import math
import numpy
from core.group import Group
from core.mesh import Mesh
from core.matrix import Matrix
from geometry.coneGeometry import ConeGeometry
from geometry.cylinderGeometry import CylinderGeometry
from geometry.sphereGeometry import SphereGeometry
from material.surfaceMaterial import SurfaceMaterial
from modeling import PartBuilder, joint

PI = math.pi
SHIP_SCALE = 0.9
ENGINE_X = 1.15
ENGINE_Y = -0.10
ENGINE_Z = 11.45


class Spaceship(object):

    def __init__(self, M):
        self.root = Group()
        self.body = joint(self.root)
        self.body.transform = Matrix.makeScale(SHIP_SCALE)
        self.meshes = []
        self.visible = True

        b = PartBuilder()
        add = lambda kind, mat, pos, size, rot=(0, 0, 0), tile=None: b.add(kind, mat, pos, size, rot, tile)
        self._buildHull(M, add)
        self._buildTower(M, add)
        self._buildEngineBlocks(M, add)
        self.meshes += b.build(self.body)
        self.partCount = b.partCount

        self._buildEmissives()

    # ------------------------------------------------------------------
    def _buildHull(self, M, add):
        add("box", M.hull, (0, 0, -0.2), (4.2, 2.2, 10.5), tile=3.0)               # casco principal
        add("box", M.hull, (0, 0, 6.6), (3.8, 2.4, 4.6), tile=3.0)                  # bloco traseiro
        add("box", M.hullDark, (0, -1.5, 0.3), (2.8, 0.9, 9.5))                     # quilha
        add("box", M.hullDark, (0, -2.1, 4.0), (0.15, 1.4, 3.0))

        # proa em cunha: prisma triangular achatado, ápice voltado para -z
        add("prism3", M.hullWhite, (0, 0.0, -6.2), (4.2, 1.6, 6.8), (0, PI, 0))
        for sx in (-1, 1):                                                           # friso dourado
            add("box", M.gold, (sx * 0.91, 0.85, -7.05), (0.14, 0.10, 5.415), (0, sx * 0.343, 0))
        add("box", M.gold, (0, 0.86, -6.4), (0.22, 0.10, 1.4))                       # cruz dourada
        add("box", M.gold, (0, 0.86, -6.6), (0.90, 0.10, 0.22))

        for s in (-1, 1):
            add("box", M.hull, (s * 2.35, 0.1, -0.8), (0.55, 1.7, 6.8), tile=3.0)   # blindagem lateral
            add("box", M.hullDark, (s * 2.3, 1.05, -0.8), (0.9, 0.25, 7.2))
            add("box", M.hull, (s * 2.5, -0.1, 3.4), (1.0, 1.6, 3.0), tile=3.0)
            for i in range(5):                                                       # alcovas em arco
                z = -3.9 + i * 1.55
                add("box", M.windowGlass, (s * 2.66, 0.15, z), (0.12, 1.1, 0.9))
                add("cylinder", M.windowGlass, (s * 2.66, 0.70, z), (0.9, 0.12, 0.9), (0, 0, PI / 2))
                for dz in (-0.50, 0.50):
                    add("box", M.bronze, (s * 2.70, 0.35, z + dz), (0.10, 1.5, 0.08))
                add("box", M.bronze, (s * 2.70, 1.20, z), (0.10, 0.08, 1.08))

        add("box", M.hullDark, (0, 1.35, -0.5), (1.4, 0.5, 7.5))                    # espinha dorsal
        add("box", M.bronze, (0, 1.72, -0.5), (0.5, 0.25, 6.0))
        for s in (-1, 1):
            for z in (-3.2, 0.2):                                                    # torres de artilharia
                add("cylinder", M.hullDark, (s * 1.0, 1.62, z), (1.1, 0.40, 1.1))
                add("sphere", M.graphite, (s * 1.0, 1.87, z), (0.9, 0.55, 0.9))
                for dx in (-0.18, 0.18):
                    add("cylinder", M.graphite, (s * 1.0 + dx, 1.95, z - 1.2), (0.16, 2.2, 0.16), (PI / 2, 0, 0))
        for z in (-3.5, -0.5, 2.5):                                                  # faixas douradas
            add("box", M.gold, (0, 1.13, z), (4.3, 0.10, 0.35))

    def _buildTower(self, M, add):
        add("box", M.hull, (0, 2.0, 6.8), (3.4, 1.6, 3.4), tile=3.0)
        add("box", M.hull, (0, 3.55, 7.0), (2.5, 1.5, 2.4), tile=3.0)
        add("box", M.hull, (0, 4.95, 7.1), (1.5, 1.4, 1.5), tile=3.0)
        for dx in (-0.9, 0.0, 0.9):                                                  # janelas góticas
            add("box", M.windowGlass, (dx, 2.05, 5.08), (0.45, 1.0, 0.06))
            add("cylinder", M.windowGlass, (dx, 2.55, 5.08), (0.45, 0.06, 0.45), (PI / 2, 0, 0))
        for dx in (-0.6, 0.6):
            add("box", M.windowGlass, (dx, 3.55, 5.78), (0.40, 0.8, 0.06))
            add("cylinder", M.windowGlass, (dx, 3.95, 5.78), (0.40, 0.06, 0.40), (PI / 2, 0, 0))
        add("pyramid", M.bronze, (0, 6.10, 7.1), (1.5, 0.9, 1.5))
        add("cylinder", M.bronze, (0, 7.9, 7.1), (0.16, 2.9, 0.16))
        for sx in (-1, 1):
            for sz in (-1, 1):
                add("pyramid", M.bronze, (sx * 1.5, 3.35, 6.8 + sz * 1.5), (0.4, 1.1, 0.4))
            add("cylinder", M.silver, (sx * 1.0, 5.3, 7.4), (0.06, 2.8, 0.06), (0, 0, -sx * 0.18))
            add("box", M.hullDark, (sx * 1.55, 3.5, 7.0), (0.7, 0.5, 2.0))
        add("sphere", M.silver, (0.9, 4.0, 5.9), (1.1, 0.25, 1.1))
        add("box", M.gold, (0, 2.82, 6.8), (3.5, 0.10, 3.5))
        add("box", M.gold, (0, 4.32, 7.0), (2.6, 0.08, 2.5))

    def _buildEngineBlocks(self, M, add):
        for s in (-1, 1):
            x = s * ENGINE_X
            add("cylinder", M.hullDark, (x, ENGINE_Y, 9.9), (2.0, 2.8, 2.0), (PI / 2, 0, 0))
            add("cylinder", M.graphite, (x, ENGINE_Y, 11.2), (2.25, 0.45, 2.25), (PI / 2, 0, 0))
            add("cylinder", M.gold, (x, ENGINE_Y, 8.8), (2.1, 0.15, 2.1), (PI / 2, 0, 0))
            add("box", M.hullDark, (x, 1.2, 9.5), (0.4, 0.8, 2.0))

    def _buildEmissives(self):
        # materiais próprios (suas cores mudam a cada quadro)
        self.flameOuter = SurfaceMaterial({"baseColor": [1.0, 0.35, 0.08]})
        self.flameInner = SurfaceMaterial({"baseColor": [1.0, 0.85, 0.55]})
        self.glowMat = SurfaceMaterial({"baseColor": [0.3, 0.06, 0.03]})
        self.beaconRed = SurfaceMaterial({"baseColor": [1.0, 0.1, 0.1]})
        self.beaconGreen = SurfaceMaterial({"baseColor": [0.1, 1.0, 0.2]})

        coneGeo = ConeGeometry(0.5, 1.0, 16, 1)
        glowGeo = CylinderGeometry(0.5, 1.0, 20, 1)
        self.flames = []
        for s in (-1, 1):
            engine = joint(self.body, (s * ENGINE_X, ENGINE_Y, ENGINE_Z))
            outer = Mesh(coneGeo, self.flameOuter)
            inner = Mesh(coneGeo, self.flameInner)
            glow = Mesh(glowGeo, self.glowMat)
            glow.transform = Matrix.makeRotationX(PI / 2) @ Matrix.makeScale(1.75, 0.08, 1.75)
            for m in (outer, inner, glow):
                m.castShadow = False                  # brilho não projeta sombra
                engine.add(m)
                self.meshes.append(m)
            self.flames.append((outer, inner))

        ballGeo = SphereGeometry(0.2, 12, 8)
        self.beacons = []
        for mat, x in ((self.beaconRed, -2.78), (self.beaconGreen, 2.78)):
            ball = Mesh(ballGeo, mat)
            ball.castShadow = False
            ball.setPosition((x, 1.25, 3.0))
            self.body.add(ball)
            self.meshes.append(ball)
            self.beacons.append(ball)

        self.engineLight = None

    def attachEngineLight(self, light):
        """A luz pontual vira filha da nave: segue sua posição e orientação."""
        self.engineLight = light
        light.setPosition((0, ENGINE_Y, ENGINE_Z + 1.8))
        self.body.add(light)

    # ------------------------------------------------------------------
    def applyPose(self, p):
        self.root.transform = (Matrix.makeTranslation(*p.position) @ Matrix.makeRotationY(p.yaw)
                               @ Matrix.makeRotationX(p.pitch) @ Matrix.makeRotationZ(p.roll))
        if p.visible != self.visible:
            self.visible = p.visible
            for m in self.meshes:
                m.visible = p.visible

        power = max(0.0, min(1.0, p.enginePower))
        length = 0.6 + 4.0 * power
        for outer, inner in self.flames:
            # cone com ápice em +y; Rx(90°) leva +y para +z (para trás) e a base fica no bico
            outer.transform = (Matrix.makeTranslation(0, 0, length / 2) @ Matrix.makeRotationX(PI / 2)
                               @ Matrix.makeScale(1.5, length, 1.5))
            inner.transform = (Matrix.makeTranslation(0, 0, 0.35 * length) @ Matrix.makeRotationX(PI / 2)
                               @ Matrix.makeScale(0.8, 0.7 * length, 0.8))
        self.flameOuter.uniforms["baseColor"].data = [1.0, 0.30 + 0.25 * power, 0.06]
        self.glowMat.uniforms["baseColor"].data = [0.25 + 0.75 * power, 0.05 + 0.50 * power, 0.03 + 0.17 * power]

        on = p.beaconOn
        self.beaconRed.uniforms["baseColor"].data = [1.0, 0.1, 0.1] if on else [0.20, 0.02, 0.02]
        self.beaconGreen.uniforms["baseColor"].data = [0.1, 1.0, 0.2] if on else [0.02, 0.16, 0.04]

        if self.engineLight is not None:
            k = 1.5 * power if p.visible else 0.0
            self.engineLight.color = [1.0 * k, 0.45 * k, 0.15 * k]

    # ------------------------------------------------------------------
    # Caixa orientada (OBB) usada para a câmera não ficar dentro do casco
    OBB_CENTER = numpy.array([0.0, 1.5, 0.8])
    OBB_HALF = numpy.array([3.3, 4.6, 12.0])

    def pushOut(self, point, margin=1.0):
        """Se `point` (mundo) estiver dentro da caixa da nave, devolve o ponto empurrado
        para fora pelo eixo de menor penetração; senão devolve o mesmo ponto."""
        if not self.visible:
            return point
        world = self.body.getWorldMatrix()
        local = numpy.linalg.inv(world) @ numpy.array([point[0], point[1], point[2], 1.0])
        local = local[0:3] - self.OBB_CENTER
        half = self.OBB_HALF + margin / SHIP_SCALE
        if numpy.all(numpy.abs(local) < half):
            depth = half - numpy.abs(local)
            axis = int(numpy.argmin(depth))
            local[axis] = math.copysign(half[axis], local[axis] if local[axis] != 0 else 1.0)
            moved = world @ numpy.append(local + self.OBB_CENTER, 1.0)
            return [moved[0], moved[1], moved[2]]
        return point
