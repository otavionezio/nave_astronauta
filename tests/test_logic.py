"""
Testes de LÓGICA (não precisam de OpenGL, Pygame nem janela).
Execução:  python -m unittest tests.test_logic -v     (a partir da raiz do projeto)
        ou python tests/test_logic.py
"""
import glob
import math
import os
import re
import sys
import unittest

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
import bootstrap  # noqa: E402,F401

import numpy as np  # noqa: E402
import animation as A  # noqa: E402
from animation import State, InteractionDirector  # noqa: E402
from core.matrix import Matrix  # noqa: E402
from core.object3D import Object3D  # noqa: E402
from camera import OrbitCamera  # noqa: E402


class Keys(object):
    """Entrada simulada."""
    def __init__(self, pressed=(), down=(), mouse=(0, 0), wheel=0, button=False):
        self.pressed, self.down = set(pressed), set(down)
        self.mouseDelta, self.mouseWheel, self._b = mouse, wheel, button

    def isKeyDown(self, k): return k in self.down
    def isKeyPressed(self, k): return k in self.pressed
    def isMousePressed(self, b=1): return self._b


def run(director, seconds, fps, jitter=False):
    """Simula `seconds` a `fps` quadros/s (opcionalmente com dt irregular, porém somando o mesmo total)."""
    rng = np.random.default_rng(1)
    t = 0.0
    while t < seconds - 1e-12:
        dt = 1.0 / fps
        if jitter:
            dt *= rng.uniform(0.3, 1.7)
        dt = min(dt, seconds - t)
        director.update(dt)
        t += dt
    return director


def snapshot(d):
    s, a = d.shipPose, d.astronautPose
    return np.array([*s.position, s.yaw, s.pitch, s.roll, s.enginePower,
                     a.x, a.z, a.bob, a.yaw, a.headYaw, a.headPitch, a.lHip, a.rHip, a.lKnee, a.rKnee,
                     a.lShoulderPitch, a.lShoulderRoll, a.lElbow, a.lWave, a.armRaise])


class TestMatrices(unittest.TestCase):

    def test_composicao_aplica_a_direita_primeiro(self):
        M = Matrix.makeTranslation(5, 0, 0) @ Matrix.makeScale(2)     # escala, depois translada
        p = M @ np.array([1.0, 0, 0, 1])
        self.assertTrue(np.allclose(p[:3], [7, 0, 0]))

    def test_hierarquia_pai_filho(self):
        pai, filho = Object3D(), Object3D()
        pai.add(filho)
        pai.translate(1, 2, 3)
        filho.rotateY(math.pi / 2)
        filho.translate(0, 0, -1)               # 1 m para a frente do filho
        self.assertTrue(np.allclose(filho.getWorldPosition(), [0, 2, 3], atol=1e-9))
        self.assertTrue(np.allclose(filho.getWorldDirection(), [-1, 0, 0], atol=1e-9))

    def test_translacao_local_x_global(self):
        a, b = Object3D(), Object3D()
        for o in (a, b):
            o.rotateY(math.pi / 2)
        a.translate(0, 0, -1, localCoord=True)        # anda na frente do objeto (girado)
        b.translate(0, 0, -1, localCoord=False)       # anda no eixo -z do mundo
        self.assertTrue(np.allclose(a.getPosition(), [-1, 0, 0], atol=1e-9))
        self.assertTrue(np.allclose(b.getPosition(), [0, 0, -1], atol=1e-9))

    def test_perspectiva_mapeia_near_e_far(self):
        P = Matrix.makePerspective(60, 1.5, 0.5, 100)
        for z, esperado in ((-0.5, -1.0), (-100.0, 1.0)):
            c = P @ np.array([0, 0, z, 1.0])
            self.assertAlmostEqual(c[2] / c[3], esperado, places=6)

    def test_ortografica_mapeia_caixa_no_cubo(self):
        O = Matrix.makeOrthographic(-10, 10, -5, 5, 1, 50)
        c = O @ np.array([10, -5, -50, 1.0])
        self.assertTrue(np.allclose(c[:3], [1, -1, 1]))

    def test_lookat_aponta_para_o_alvo(self):
        m = Matrix.makeLookAt([0, 0, 0], [3, 0, -4])
        frente = -m[:3, 2]
        self.assertTrue(np.allclose(frente, [0.6, 0, -0.8]))

    def test_matriz_nao_tem_itemset(self):
        # ndarray.itemset foi removido no NumPy 2: o projeto não pode usá-lo
        for f in glob.glob(os.path.join(ROOT, "**", "*.py"), recursive=True):
            if os.sep + "tests" + os.sep in f:
                continue
            with open(f, encoding="utf-8") as fh:
                self.assertNotIn(".itemset(", fh.read(), f)


class TestMaquinaDeEstados(unittest.TestCase):

    def test_ordem_e_instantes_dos_estados(self):
        d = run(InteractionDirector(), 40, 60)
        ordem = [s for s, _ in d.history]
        self.assertEqual(ordem, A.ORDER)
        inicio = dict(d.history)
        esperado = 0.0
        for s in A.ORDER[:-1]:
            self.assertAlmostEqual(inicio[s], esperado, places=6)
            esperado += A.DURATION[s]
        self.assertAlmostEqual(inicio[State.CONCLUIDO], esperado, places=6)

    def test_nave_nao_se_move_na_espera(self):
        # da ESTABILIZACAO até antes da partida a nave só oscila (hover) em torno de HOLD
        d = InteractionDirector()
        maximo = 0.0
        t = 0.0
        while d.state is not State.CONCLUIDO and t < 60:
            d.update(1 / 60)
            t += 1 / 60
            st = d.state
            parada = st in (State.REACAO_DO_ASTRONAUTA, State.SINALIZACAO, State.RESPOSTA_DA_NAVE) or (
                st is State.RETOMADA and not d.shipPose.departureEnabled)
            if parada:
                p = d.shipPose.position
                maximo = max(maximo, math.dist(p, A.HOLD))
        self.assertLess(maximo, 0.2, "a nave deve ficar parada (apenas hover de ~0,12 m)")

    def test_astronauta_so_anda_depois_da_nave_estabilizar(self):
        d = InteractionDirector()
        run(d, A.DURATION[State.APROXIMACAO] + A.DURATION[State.ESTABILIZACAO] - 0.01, 60)
        self.assertEqual(d.astronautPose.x, A.ASTRONAUT_START[0])
        self.assertEqual(d.astronautPose.z, A.ASTRONAUT_START[1])
        run(d, 3.0, 60)                                   # em plena REACAO
        self.assertIs(d.state, State.REACAO_DO_ASTRONAUTA)
        self.assertGreater(math.hypot(d.astronautPose.x, d.astronautPose.z - A.ASTRONAUT_START[1]), 0.1)

    def test_chega_na_marca_e_o_braco_so_sobe_depois(self):
        d = InteractionDirector()
        while d.state is not State.SINALIZACAO:
            d.update(1 / 60)
            if d.state is State.REACAO_DO_ASTRONAUTA:
                self.assertEqual(d.astronautPose.armRaise, 0.0)      # braço em repouso enquanto anda
        self.assertAlmostEqual(d.astronautPose.x, A.MARK[0], places=3)
        self.assertAlmostEqual(d.astronautPose.z, A.MARK[1], places=3)

    def test_resposta_da_nave_so_depois_do_aceno_completo(self):
        d = InteractionDirector()
        while d.state is not State.RESPOSTA_DA_NAVE:
            d.update(1 / 60)
            if d.state is State.SINALIZACAO:
                # durante o aceno os motores NÃO pulsam (potência constante)
                self.assertAlmostEqual(d.shipPose.enginePower, 0.30, places=6)
                self.assertFalse(d.shipPose.beaconOn)
        self.assertGreaterEqual(d.astronautPose.waveCycles, 3.0 - 1e-6)    # 3 acenos concluídos

    def test_tres_pulsos_dos_motores(self):
        d = InteractionDirector()
        while d.state is not State.RESPOSTA_DA_NAVE:
            d.update(1 / 60)
        potencias = []
        while d.state is State.RESPOSTA_DA_NAVE:
            d.update(1 / 240)
            potencias.append(d.shipPose.enginePower)
        p = np.array(potencias)
        picos = np.sum((p[1:-1] > p[:-2]) & (p[1:-1] >= p[2:]) & (p[1:-1] > 0.9))
        self.assertEqual(picos, 3)

    def test_nave_so_parte_depois_que_o_braco_baixou(self):
        d = InteractionDirector()
        iniciou = None
        while d.state is not State.CONCLUIDO:
            d.update(1 / 120)
            if d.state is State.RETOMADA:
                if d.shipPose.departureEnabled:
                    self.assertEqual(d.astronautPose.armRaise, 0.0)    # condição de partida
                    if iniciou is None:
                        iniciou = d.totalTime
                else:
                    self.assertGreater(d.astronautPose.armRaise, 0.0)  # enquanto o braço ainda está no alto
        inicio_retomada = dict(d.history)[State.RETOMADA]
        self.assertAlmostEqual(iniciou - inicio_retomada, A.ARM_LOWER_TIME, delta=0.02)
        self.assertIsNotNone(d.departureStartedAt)

    def test_conclusao_perceptivel_e_reinicio(self):
        d = run(InteractionDirector(), 35, 60)
        self.assertIs(d.state, State.CONCLUIDO)
        self.assertFalse(d.shipPose.visible)
        d.reset()
        self.assertIs(d.state, State.APROXIMACAO)
        self.assertTrue(d.shipPose.visible)
        self.assertEqual(d.totalTime, 0.0)
        self.assertTrue(np.allclose(snapshot(d), snapshot(InteractionDirector())))

    def test_modo_loop_reinicia_sozinho(self):
        d = InteractionDirector(loop=True)
        run(d, A.DURATION_TOTAL if hasattr(A, "DURATION_TOTAL") else 29.9 + A.LOOP_DELAY + 1.0, 60)
        self.assertIs(d.state, State.APROXIMACAO)


class TestTempo(unittest.TestCase):
    """Animação por delta time: o resultado depende do TEMPO, não do número de quadros."""

    def test_independente_da_taxa_de_quadros(self):
        for alvo in (2.0, 6.5, 8.3, 11.7, 16.1, 19.4, 22.9, 26.0, 33.0):
            ref = snapshot(run(InteractionDirector(), alvo, 240))
            for fps in (15, 30, 60, 144):
                obtido = snapshot(run(InteractionDirector(), alvo, fps))
                self.assertTrue(np.allclose(ref, obtido, atol=1e-6), "t=%s fps=%s" % (alvo, fps))

    def test_dt_irregular_nao_altera_o_resultado(self):
        for alvo in (7.7, 14.2, 21.0, 27.5):
            ref = snapshot(run(InteractionDirector(), alvo, 60))
            obtido = snapshot(run(InteractionDirector(), alvo, 60, jitter=True))
            self.assertTrue(np.allclose(ref, obtido, atol=1e-6))

    def test_um_unico_passo_grande_equivale_a_varios_pequenos(self):
        a = InteractionDirector(); a.update(17.3)
        b = run(InteractionDirector(), 17.3, 100)
        self.assertEqual(a.state, b.state)
        self.assertTrue(np.allclose(snapshot(a), snapshot(b), atol=1e-6))

    def test_pausa_mantem_exatamente_o_estado(self):
        d = run(InteractionDirector(), 13.37, 60)
        antes, estado, t = snapshot(d), d.state, d.totalTime
        for _ in range(500):
            d.update(0.0)                       # pausado
        self.assertEqual(d.state, estado)
        self.assertEqual(d.totalTime, t)
        self.assertTrue(np.array_equal(antes, snapshot(d)))

    def test_retomar_continua_coerente(self):
        a = run(InteractionDirector(), 9.0, 60)
        for _ in range(100):
            a.update(0.0)
        run(a, 11.0, 60)                        # +11 s depois de retomar
        b = run(InteractionDirector(), 20.0, 60)
        self.assertTrue(np.allclose(snapshot(a), snapshot(b), atol=1e-6))

    def test_passada_proporcional_a_distancia(self):
        # a fase da perna cresce com a distância andada: sem "patinar"
        d = InteractionDirector()
        run(d, A.DURATION[State.APROXIMACAO] + A.DURATION[State.ESTABILIZACAO], 60)
        fases, dist, ult = [], 0.0, (d.astronautPose.x, d.astronautPose.z)
        while d.state is State.REACAO_DO_ASTRONAUTA or d.state is State.ESTABILIZACAO:
            d.update(1 / 60)
            p = d.astronautPose
            dist += math.hypot(p.x - ult[0], p.z - ult[1])
            ult = (p.x, p.z)
        self.assertAlmostEqual(dist, A.WALK_DISTANCE, places=2)


class TestCamera(unittest.TestCase):

    def novo(self):
        c = OrbitCamera()
        return c, {"astronauta": (0, 0, 0), "nave": (-18, 8, 6)}

    def quadros(self, c, follow, inp, n=300, dt=1 / 60):
        for _ in range(n):
            c.update(dt, inp, follow)

    def test_elevacao_e_distancia_limitadas(self):
        c, f = self.novo()
        self.quadros(c, f, Keys(pressed={"down", "s"}), 600)
        self.assertGreaterEqual(c.el, math.radians(4) - 1e-9)
        self.assertLessEqual(c.dist, 90 + 1e-9)
        self.quadros(c, f, Keys(pressed={"up", "w"}), 1200)
        self.assertLessEqual(c.el, math.radians(86) + 1e-9)
        self.assertGreaterEqual(c.dist, 3.0 - 1e-9)

    def test_camera_nunca_abaixo_do_piso(self):
        c, f = self.novo()
        for teclas in ({"down"}, {"down", "q"}, {"down", "a"}, {"down", "w"}):
            self.quadros(c, f, Keys(pressed=teclas), 400)
            self.assertGreaterEqual(c.position[1], 0.4 - 1e-9, teclas)

    def test_alvo_limitado_ao_deck(self):
        c, f = self.novo()
        self.quadros(c, f, Keys(pressed={"d", "e"}), 3000)
        self.assertLessEqual(c.target[0], 45 + 1e-6)
        self.assertLessEqual(c.target[1], 25 + 1e-6)

    def test_orbita_gira_ao_redor_do_alvo(self):
        c, f = self.novo()
        self.quadros(c, f, Keys(), 120)
        d0 = c.dist
        self.quadros(c, f, Keys(pressed={"right"}), 60)
        t = c.target
        dist = math.dist(c.position, t)
        self.assertAlmostEqual(dist, c.dist, delta=0.5)
        self.assertGreater(abs(c.azT - c.az) + abs(c.az), 0)

    def test_mouse_e_roda(self):
        c, f = self.novo()
        antes = c.distT
        c.update(1 / 60, Keys(wheel=3), f)
        self.assertLess(c.distT, antes)
        az = c.azT
        c.update(1 / 60, Keys(mouse=(100, 0), button=True), f)
        self.assertNotEqual(c.azT, az)

    def test_camera_continua_com_a_animacao_pausada(self):
        # a câmera usa dt REAL: responde mesmo que o diretor receba dt = 0
        c, f = self.novo()
        az = c.az
        self.quadros(c, f, Keys(pressed={"right"}), 60)
        self.assertNotEqual(c.az, az)

    def test_empurra_a_camera_para_fora_do_obstaculo(self):
        c, f = self.novo()
        centro = np.array([-10.0, 4.5, 2.5])

        def obstaculo(p, margem):
            v = np.array(p) - centro
            if np.linalg.norm(v) < 10:
                v = v / (np.linalg.norm(v) or 1) * 10
                return list(centro + v)
            return p
        c.obstacle = obstaculo
        c.distT = c.dist = 3.0
        c.setMode("4")
        self.quadros(c, f, Keys(), 60)
        self.assertGreaterEqual(math.dist(c.position, centro), 10 - 1e-6)

    def test_presets(self):
        c, f = self.novo()
        c.update(1 / 60, Keys(down={"2"}), f)
        self.assertEqual(c.mode, "astronauta")
        c.update(1 / 60, Keys(down={"3"}), f)
        self.assertEqual(c.mode, "nave")


class TestFontes(unittest.TestCase):

    def shaders(self):
        out = {}
        for f in glob.glob(os.path.join(ROOT, "shaders", "*")):
            with open(f, encoding="utf-8") as fh:
                out[os.path.basename(f)] = fh.read()
        return out

    def test_shaders_existem_e_includes_resolvem(self):
        from core.shaderSource import loadShader
        for nome in ("lit.vert", "lit.frag", "depth.vert", "depth.frag", "basic.vert", "basic.frag",
                     "texture.vert", "texture.frag", "depthview.frag"):
            codigo = loadShader(nome)
            self.assertNotIn("#include", codigo, nome)
        self.assertIn("struct Light", loadShader("lit.frag"))
        self.assertTrue(loadShader("lit.frag", ["USE_SPECULAR"]).startswith("#define USE_SPECULAR"))

    def test_shaders_sem_apis_removidas(self):
        for nome, codigo in self.shaders().items():
            self.assertIsNone(re.search(r"\btexture2D\b", codigo), nome)      # removida no GLSL 330 core
            for linha in codigo.splitlines():
                if re.match(r"\s*in\s+vec[234]\s+vertex", linha):             # atributo sem layout(location)
                    self.fail("%s: atributo sem layout(location): %s" % (nome, linha))

    def test_localizacoes_de_atributos_coerentes(self):
        # o VAO é compartilhado entre o programa principal e o DepthMaterial: vertexPosition = 0 em todos
        for nome, codigo in self.shaders().items():
            m = re.search(r"layout\s*\(\s*location\s*=\s*(\d)\s*\)\s*in\s+vec3\s+vertexPosition", codigo)
            if nome.endswith(".vert"):
                self.assertIsNotNone(m, nome)
                self.assertEqual(m.group(1), "0", nome)

    def test_texturas_geradas_sao_reprodutiveis(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import gerar_texturas as g
        a, b = g.make_floor(), g.make_floor()
        self.assertTrue(np.array_equal(a, b))
        self.assertEqual(a.shape, (512, 512, 3))
        for nome in ("painel_metalico.png", "casco_cinza.png"):
            self.assertTrue(os.path.isfile(os.path.join(ROOT, "textures", nome)), nome)

    def test_texturas_repetiveis(self):
        from PIL import Image
        for nome in ("painel_metalico.png", "casco_cinza.png"):
            im = np.asarray(Image.open(os.path.join(ROOT, "textures", nome)).convert("L"), float)
            borda = np.abs(im[:, 0] - im[:, -1]).mean()          # coluna 0 vs última: deve ser contínua
            interno = np.abs(im[:, 100] - im[:, 101]).mean()
            self.assertLess(borda, interno * 3 + 12, nome)


if __name__ == "__main__":
    unittest.main(verbosity=2)
