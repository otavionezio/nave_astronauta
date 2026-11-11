"""
Astronauta de armadura pesada (inspirado nas referências: armadura preta/grafite com
detalhes dourados e vermelhos, ombreiras enormes, peitoral com águia/caveira, bolsas,
cinto com corrente, braço esquerdo prateado, joelheiras com caveira dourada/faixa vermelha).

HIERARQUIA DE JUNTAS (cada nó é um Group; a matriz local é recomposta a cada quadro):

  root  (posição no mundo + yaw)
   └ body (escala uniforme 0.9)
      ├ hipL ── kneeL        ├ hipR ── kneeR
      └ torso
         ├ neck (cabeça)
         ├ shoulderL ── elbowL (braço esquerdo, prateado)   ├ shoulderR ── elbowR
         └ pauldronL / pauldronR  (ombreiras: seguem só PARTE do movimento do braço)

Transformação final de uma peça no mundo:
     W = T_root @ Ry(yaw) @ S @ T_junta... @ (T·R·S da peça)
isto é, cada filho herda a transformação do pai (multiplicação de matrizes em cadeia).

Convenção: a "frente" do astronauta é -z, a direita é +x, o alto é +y.
"""
import math
from core.group import Group
from core.matrix import Matrix
from modeling import PartBuilder, joint, poseTransform

PI = math.pi
BODY_SCALE = 0.9


class Astronaut(object):

    def __init__(self, M):
        self.root = Group()
        self.body = joint(self.root)
        self.body.transform = Matrix.makeScale(BODY_SCALE)       # ESCALA do conjunto

        # ---------------- articulações ----------------
        self.hip = {}
        self.knee = {}
        self.shoulder = {}
        self.elbow = {}
        self.pauldron = {}
        self.torso = joint(self.body, (0, 1.30, 0))
        self.neck = joint(self.torso, (0, 1.02, 0))
        for side, s in (("L", -1), ("R", 1)):
            self.hip[side] = joint(self.body, (s * 0.27, 1.22, 0))
            self.knee[side] = joint(self.hip[side], (0, -0.50, 0))
            self.shoulder[side] = joint(self.torso, (s * 0.64, 0.80, 0))
            self.elbow[side] = joint(self.shoulder[side], (0, -0.54, 0))
            self.pauldron[side] = joint(self.torso, (s * 0.64, 0.80, 0))

        self.partCount = 0
        for side, s in (("L", -1), ("R", 1)):
            self._buildLeg(M, side, s)
            self._buildArm(M, side, s)
            self._buildPauldron(M, side, s)
        self._buildTorso(M)
        self._buildHead(M)

    # ------------------------------------------------------------------
    def _make(self, parent):
        b = PartBuilder()
        return b, lambda kind, mat, pos, size, rot=(0, 0, 0): b.add(kind, mat, pos, size, rot)

    def _finish(self, builder, parent):
        builder.build(parent)
        self.partCount += builder.partCount

    def _buildLeg(self, M, side, s):
        # ---- coxa (junta do quadril) ----
        b, add = self._make(self.hip[side])
        add("sphere", M.graphite, (0, 0, 0), (0.30, 0.30, 0.30))                    # articulação
        add("box", M.armorBlack, (0, -0.24, 0), (0.44, 0.54, 0.46))                 # coxa
        add("box", M.graphite, (0, -0.22, -0.25), (0.36, 0.42, 0.06))               # placa frontal
        for dx in (-0.10, 0.10):                                                    # parafusos
            add("cylinder", M.silver, (dx, -0.12, -0.29), (0.06, 0.03, 0.06), (PI / 2, 0, 0))
        self._finish(b, self.hip[side])

        # ---- joelho, canela e bota (junta do joelho) ----
        b, add = self._make(self.knee[side])
        add("sphere", M.armorBlack, (0, 0.0, -0.20), (0.42, 0.34, 0.30))            # joelheira
        if s < 0:                                                                   # caveira dourada
            add("sphere", M.gold, (0, 0.0, -0.34), (0.14, 0.17, 0.10))
            add("box", M.gold, (0, -0.10, -0.33), (0.09, 0.05, 0.06))
            for dx in (-0.035, 0.035):
                add("box", M.armorBlack, (dx, 0.02, -0.39), (0.035, 0.035, 0.02))
        else:                                                                       # faixa vermelha
            add("box", M.redArmor, (0, 0.0, -0.335), (0.12, 0.32, 0.05))
        add("box", M.armorBlack, (0, -0.26, 0), (0.40, 0.50, 0.44))                 # canela
        add("box", M.graphite, (0, -0.26, -0.25), (0.32, 0.46, 0.07))               # grevas
        add("box", M.graphite, (0, -0.22, 0.24), (0.34, 0.34, 0.08))                # panturrilha
        add("cylinder", M.graphite, (0, -0.51, 0), (0.30, 0.10, 0.30))              # tornozelo
        add("box", M.armorBlack, (0, -0.57, -0.06), (0.44, 0.30, 0.64))             # bota
        add("box", M.graphite, (0, -0.62, -0.38), (0.40, 0.20, 0.20))               # biqueira
        self._finish(b, self.knee[side])

    def _buildArm(self, M, side, s):
        silver = (s < 0)
        plate = M.silver if silver else M.armorBlack
        # ---- braço (junta do ombro) ----
        b, add = self._make(self.shoulder[side])
        add("sphere", M.graphite, (0, 0, 0), (0.28, 0.28, 0.28))
        add("box", plate, (0, -0.27, 0), (0.30, 0.54, 0.32))
        if not silver:
            add("sphere", M.gold, (0.17, -0.28, 0.0), (0.10, 0.14, 0.12))           # caveira dourada
        self._finish(b, self.shoulder[side])

        # ---- antebraço e mão (junta do cotovelo) ----
        b, add = self._make(self.elbow[side])
        add("cylinder", M.graphite, (0, 0, 0), (0.20, 0.30, 0.20), (0, 0, PI / 2))  # cotovelo nervurado
        add("box", plate, (0, -0.26, 0), (0.34, 0.50, 0.36))                        # antebraço
        add("box", plate, (0, -0.18, 0), (0.40, 0.30, 0.42))                        # braçadeira
        add("cylinder", M.graphite, (0, -0.52, 0), (0.26, 0.06, 0.26))              # punho
        add("box", M.graphite, (0, -0.68, 0), (0.26, 0.26, 0.22))                   # mão (punho fechado)
        add("box", M.graphite, (-s * 0.10, -0.66, -0.13), (0.07, 0.15, 0.08))       # polegar
        add("box", M.silver, (0, -0.60, -0.10), (0.24, 0.05, 0.06))                 # placa de nós dos dedos
        self._finish(b, self.elbow[side])

    def _buildPauldron(self, M, side, s):
        b, add = self._make(self.pauldron[side])
        if s > 0:                                  # direita: cúpula negra com borda dourada e pano
            add("sphere", M.armorBlack, (0.06, 0.10, 0), (0.72, 0.54, 0.68))
            add("sphere", M.gold, (0.06, -0.13, 0), (0.76, 0.07, 0.72))
            add("cylinder", M.gold, (0.43, 0.10, 0), (0.20, 0.04, 0.20), (0, 0, PI / 2))
            add("sphere", M.bone, (0.46, 0.10, 0), (0.12, 0.13, 0.08))
            add("box", M.clothGrey, (0.42, -0.22, 0.02), (0.04, 0.50, 0.46), (0, 0, -0.12))
        else:                                      # esquerda: placa retangular com inscrições
            add("box", M.armorBlack, (-0.13, 0.05, 0), (0.46, 0.64, 0.74), (0, 0, 0.10))
            add("box", M.silver, (-0.11, 0.38, 0), (0.48, 0.05, 0.78), (0, 0, 0.10))
            add("box", M.silver, (-0.15, -0.27, 0), (0.48, 0.05, 0.78), (0, 0, 0.10))
            for k in range(4):                     # linhas de texto em relevo (douradas)
                y = 0.26 - k * 0.14
                add("box", M.gold, (-0.365 - 0.10 * y, y, 0), (0.025, 0.06, 0.50), (0, 0, 0.10))
            add("box", M.armorBlack, (-0.05, 0.43, 0), (0.22, 0.10, 0.22))
            add("sphere", M.bone, (-0.05, 0.51, 0), (0.17, 0.18, 0.15))             # caveira
        self._finish(b, self.pauldron[side])

    def _buildTorso(self, M):
        b, add = self._make(self.torso)
        # abdômen nervurado
        add("cylinder", M.graphite, (0, 0.14, 0), (0.52, 0.34, 0.40))
        for y in (0.06, 0.16, 0.26):
            add("cylinder", M.armorBlack, (0, y, 0), (0.60, 0.05, 0.48))
        # cinto, fivela, corrente
        add("box", M.armorBlack, (0, -0.02, 0), (0.66, 0.14, 0.46))
        add("box", M.graphite, (0, -0.02, -0.25), (0.22, 0.18, 0.06))
        add("sphere", M.gold, (0, -0.02, -0.29), (0.10, 0.10, 0.06))
        add("torus", M.silver, (0, -0.07, 0), (1.0, 1.0, 0.82))
        add("torus", M.silver, (0, -0.13, 0), (0.95, 1.0, 0.78))
        # tabardo e troféus
        add("box", M.clothRed, (0, -0.34, -0.26), (0.30, 0.56, 0.03), (0.05, 0, 0))
        add("box", M.gold, (0, -0.62, -0.265), (0.30, 0.03, 0.04))
        add("sphere", M.bone, (-0.08, -0.38, -0.31), (0.14, 0.16, 0.14))
        add("sphere", M.bone, (-0.02, -0.54, -0.31), (0.12, 0.14, 0.12))
        add("cylinder", M.bone, (-0.16, -0.32, -0.30), (0.04, 0.30, 0.04), (0, 0, 0.45))
        add("box", M.redArmor, (-0.10, -0.22, -0.30), (0.03, 0.08, 0.03))
        add("box", M.leather, (0.36, -0.24, -0.08), (0.14, 0.32, 0.12))             # bolsa do quadril
        # peitoral
        add("box", M.armorBlack, (0, 0.62, 0), (0.88, 0.58, 0.54))
        add("box", M.armorBlack, (0, 0.88, 0), (1.00, 0.20, 0.52))
        for sx in (-1, 1):
            add("box", M.graphite, (sx * 0.20, 0.64, -0.30), (0.40, 0.36, 0.10), (0, -sx * 0.18, 0))
        # águia dourada com caveira
        for sx in (-1, 1):
            add("box", M.gold, (sx * 0.20, 0.71, -0.375), (0.28, 0.05, 0.04), (0, 0, sx * 0.22))
            add("box", M.gold, (sx * 0.17, 0.62, -0.375), (0.22, 0.04, 0.04), (0, 0, sx * 0.55))
        add("sphere", M.gold, (0, 0.65, -0.385), (0.15, 0.17, 0.10))
        add("box", M.gold, (0, 0.555, -0.375), (0.09, 0.05, 0.07))
        for dx in (-0.035, 0.035):
            add("box", M.armorBlack, (dx, 0.67, -0.435), (0.03, 0.03, 0.02))
        # bolsas do peito (4) com abas
        for sx in (-1, 1):
            for y in (0.72, 0.50):
                add("box", M.leather, (sx * 0.36, y, -0.31), (0.20, 0.17, 0.11))
                add("box", M.graphite, (sx * 0.36, y + 0.075, -0.315), (0.21, 0.04, 0.12))
        # gola e mochila de energia
        add("box", M.armorBlack, (0, 0.97, 0), (0.62, 0.14, 0.52))
        add("box", M.armorBlack, (0, 1.06, 0.22), (0.50, 0.22, 0.12))
        add("box", M.graphite, (0, 0.58, 0.42), (0.62, 0.62, 0.30))
        add("box", M.armorBlack, (0, 0.94, 0.45), (0.40, 0.12, 0.12))
        for dx in (-0.18, 0.18):
            add("cylinder", M.silver, (dx, 0.18, 0.55), (0.14, 0.22, 0.14))
        # coroa gótica atrás da cabeça (3 arcos com pináculos)
        for dx in (-0.20, 0.0, 0.20):
            h = 0.34 if dx == 0 else 0.28
            add("box", M.bronze, (dx, 1.12 + h / 2 - 0.1, 0.40), (0.15, h, 0.06))
            add("pyramid", M.gold, (dx, 1.12 + h - 0.02 + 0.07, 0.40), (0.15, 0.16, 0.06))
        self._finish(b, self.torso)

    def _buildHead(self, M):
        b, add = self._make(self.neck)
        add("cylinder", M.graphite, (0, -0.02, 0), (0.20, 0.12, 0.20))              # pescoço
        add("sphere", M.armorBlack, (0, 0.14, 0), (0.34, 0.38, 0.40))               # capacete
        add("box", M.armorBlack, (0, 0.34, 0), (0.05, 0.06, 0.30))                  # crista
        for sx in (-1, 1):                                                          # sobrancelhas
            add("box", M.armorBlack, (sx * 0.08, 0.215, -0.18), (0.14, 0.05, 0.07), (0, 0, -sx * 0.3))
        add("box", M.graphite, (0, 0.04, -0.19), (0.16, 0.10, 0.06))                # grade/máscara
        for dx in (-0.04, 0.0, 0.04):
            add("box", M.silver, (dx, 0.04, -0.225), (0.012, 0.08, 0.02))
        for sx in (-1, 1):                                                          # ventilações laterais
            add("cylinder", M.silver, (sx * 0.18, 0.08, 0.0), (0.07, 0.05, 0.07), (0, 0, PI / 2))
        add("sphere", M.gold, (0, 0.29, -0.155), (0.06, 0.06, 0.04))                # caveira na testa
        # visor vermelho (emissivo: não depende da luz)
        visor = PartBuilder()
        visor.add("box", M.visor, (0, 0.17, -0.195), (0.25, 0.05, 0.04))
        for sx in (-1, 1):
            visor.add("box", M.visor, (sx * 0.09, 0.15, -0.20), (0.07, 0.06, 0.03), (0, 0, -sx * 0.25))
        self._finish(b, self.neck)
        self._finish(visor, self.neck)

    # ------------------------------------------------------------------
    @staticmethod
    def _armTransform(position, pitch, roll):
        # Rx primeiro (balança para frente), depois Rz (afasta lateralmente)
        return (Matrix.makeTranslation(*position) @ Matrix.makeRotationZ(roll)
                @ Matrix.makeRotationX(pitch))

    def applyPose(self, p):
        """Recompõe TODAS as matrizes locais a partir dos parâmetros da pose."""
        self.root.transform = Matrix.makeTranslation(p.x, p.bob, p.z) @ Matrix.makeRotationY(p.yaw)

        self.hip["L"].transform = poseTransform((-0.27, 1.22, 0), rx=p.lHip)
        self.hip["R"].transform = poseTransform((0.27, 1.22, 0), rx=p.rHip)
        self.knee["L"].transform = poseTransform((0, -0.50, 0), rx=-p.lKnee)       # canela vai para trás
        self.knee["R"].transform = poseTransform((0, -0.50, 0), rx=-p.rKnee)

        self.torso.transform = poseTransform((0, 1.30, 0), ry=p.torsoYaw)
        self.neck.transform = poseTransform((0, 1.02, 0), rx=p.headPitch, ry=p.headYaw)

        # braço esquerdo (x < 0): "para fora" = rotação negativa em z; direito: positiva
        self.shoulder["L"].transform = self._armTransform((-0.64, 0.80, 0), p.lShoulderPitch, -p.lShoulderRoll)
        self.shoulder["R"].transform = self._armTransform((0.64, 0.80, 0), p.rShoulderPitch, p.rShoulderRoll)
        self.elbow["L"].transform = (Matrix.makeTranslation(0, -0.54, 0) @ Matrix.makeRotationX(p.lElbow)
                                     @ Matrix.makeRotationZ(p.lWave))
        self.elbow["R"].transform = Matrix.makeTranslation(0, -0.54, 0) @ Matrix.makeRotationX(p.rElbow)

        # ombreiras acompanham ~35% do movimento do braço (hierarquia em dois níveis)
        self.pauldron["L"].transform = self._armTransform(
            (-0.64, 0.80, 0), 0.35 * p.lShoulderPitch, -0.35 * (p.lShoulderRoll - 0.07))
        self.pauldron["R"].transform = self._armTransform(
            (0.64, 0.80, 0), 0.35 * p.rShoulderPitch, 0.35 * (p.rShoulderRoll - 0.07))

    # ponto de interesse para a câmera / testes
    def worldPosition(self):
        return self.root.getWorldPosition()
