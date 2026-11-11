"""
Testes GRÁFICOS: renderizam quadros de verdade e verificam pixels.

Precisam de um contexto OpenGL 3.3 core. Duas formas de executar:
  * máquina com janela, Pygame e PyOpenGL instalados:  python -m unittest tests.test_render_headless -v
  * sem janela (Linux + Mesa): defina FORCE_HEADLESS_SHIM=1 — usa tests/headless (ctypes + EGL).
Se nenhum contexto puder ser criado, os testes são PULADOS (e dizem isso).
"""
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import headless_env  # noqa: E402

import numpy as np  # noqa: E402

W, H = 960, 540
ON = OFF = HUDAPP = None
REAL = None


def setUpModule():
    global ON, OFF, HUDAPP, REAL
    try:
        REAL = headless_env.setup(W, H)
        from app import Application, Options
        ON = Application((W, H), Options(hud=False, shadows=True))
        OFF = Application((W, H), Options(hud=False, shadows=False))
        HUDAPP = Application((W, H), Options(hud=True, shadows=True))
    except Exception as e:                                    # sem contexto GL disponível
        raise unittest.SkipTest("sem contexto OpenGL: %r" % (e,))


def advance(app, t, dt=None):
    """Leva a simulação ao instante t (partindo do início).
    dt=None: um único passo grande (as poses são funções exatas do tempo; ver TestTempo em
    test_logic.py). Com dt numérico, avança em passos de dt (usado no teste de FPS)."""
    app.director.reset()
    if dt is None:
        app.update(t, headless_env.FakeInput())
    else:
        while app.director.totalTime + 1e-12 < t:
            app.update(min(dt, t - app.director.totalTime), headless_env.FakeInput())
    app.update(0.0, headless_env.FakeInput())


def shot(app):
    app.render()
    return np.asarray(headless_env.readFramebuffer(W, H), dtype=float)


def project(app, p):
    cam = app.orbit.camera
    clip = cam.projectionMatrix @ cam.viewMatrix @ np.array([p[0], p[1], p[2], 1.0])
    ndc = clip[:3] / clip[3]
    return (ndc[0] * 0.5 + 0.5) * W, (1.0 - (ndc[1] * 0.5 + 0.5)) * H


def unprojectToPlane(app, px, py, planeY):
    """Raio da câmera pelo pixel (px,py) interceptando o plano y = planeY (coordenadas de mundo)."""
    cam = app.orbit.camera
    inv = np.linalg.inv(cam.projectionMatrix @ cam.viewMatrix)
    ndc = np.array([px / W * 2 - 1, (1 - py / H) * 2 - 1])
    near = inv @ np.array([ndc[0], ndc[1], -1.0, 1.0])
    far = inv @ np.array([ndc[0], ndc[1], 1.0, 1.0])
    near, far = near[:3] / near[3], far[:3] / far[3]
    t = (planeY - near[1]) / (far[1] - near[1])
    return near + t * (far - near)


def window(img, center, r):
    x, y = int(round(center[0])), int(round(center[1]))
    return img[max(y - r, 0):y + r + 1, max(x - r, 0):x + r + 1]


def darker(on, off):
    """Máscara dos pixels que ficaram mais escuros por causa das sombras (sombras ligadas x desligadas)."""
    return (off.mean(axis=2) - on.mean(axis=2)) > 10


def sunShadowPoint(p, sun=(0.32, -0.80, -0.45)):
    """Onde o ponto p (mundo) projeta sua sombra no piso (y = 0), seguindo a direção dos raios."""
    s = p[1] / -sun[1]
    return (p[0] + sun[0] * s, 0.0, p[2] + sun[2] * s)


class TestBase(unittest.TestCase):

    def test_materiais_e_shaders_compilam(self):
        import lighting
        from material.phongMaterial import PhongMaterial
        from material.lambertMaterial import LambertMaterial
        from material.surfaceMaterial import SurfaceMaterial
        from material.pointMaterial import PointMaterial
        from material.depthMaterial import DepthMaterial
        for ctor in (lambda: PhongMaterial(useShadow=True), LambertMaterial, SurfaceMaterial,
                     PointMaterial, DepthMaterial):
            self.assertGreater(ctor().programRef, 0)

    def test_primitivas_sem_nan_normais_unitarias_e_faces_para_fora(self):
        from geometry.boxGeometry import BoxGeometry
        from geometry.sphereGeometry import SphereGeometry
        from geometry.cylinderGeometry import CylinderGeometry
        from geometry.coneGeometry import ConeGeometry
        from geometry.prismGeometry import PrismGeometry
        from geometry.pyramidGeometry import PyramidGeometry
        from geometry.torusGeometry import TorusGeometry
        casos = {"box": (BoxGeometry(1, 2, 3), 6.0), "sphere": (SphereGeometry(0.5, 16, 10), 0.5236),
                 "cylinder": (CylinderGeometry(0.5, 1, 16, 1), 0.7854), "cone": (ConeGeometry(0.5, 1, 16, 1), 0.2618),
                 "prism3": (PrismGeometry(1, 1, 3, 1), 1.299), "pyramid": (PyramidGeometry(1, 1, 4, 1), 0.667),
                 "torus": (TorusGeometry(1, 0.2, 24, 8), 0.789)}
        for nome, (g, volume) in casos.items():
            P = np.asarray(g.attributes["vertexPosition"].data, float)
            N = np.asarray(g.attributes["vertexNormal"].data, float)
            self.assertFalse(np.isnan(P).any() or np.isnan(N).any(), nome)
            self.assertTrue(np.allclose(np.linalg.norm(N, axis=1), 1.0), nome)
            tri = P.reshape(-1, 3, 3)
            vol = np.einsum("ij,ij->i", tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum() / 6
            self.assertGreater(vol, 0, nome + ": volume negativo = faces voltadas para dentro")
            self.assertAlmostEqual(vol / volume, 1.0, delta=0.15, msg=nome)

    def test_quadro_sem_erro_gl_e_nao_vazio(self):
        from OpenGL.GL import glGetError
        advance(ON, 0.5)
        img = shot(ON)
        self.assertEqual(glGetError(), 0)
        self.assertGreater(img.std(), 8.0)
        self.assertGreater(ON.mainDrawCalls, 20)                      # sombra + principal
        for node in ON.scene.getDescendantList():
            self.assertTrue(np.isfinite(node.worldCache).all())

    def test_modelos_tem_hierarquia_e_muitas_pecas(self):
        self.assertGreaterEqual(ON.astronaut.partCount, 100)
        self.assertGreaterEqual(ON.ship.partCount, 100)
        prof = 0
        n = ON.astronaut.elbow["L"]
        while n.parent is not None:
            prof += 1
            n = n.parent
        self.assertGreaterEqual(prof, 5)        # cena > root > body > torso > ombro > cotovelo


class TestTextura(unittest.TestCase):

    def test_textura_de_imagem_aplicada_ao_piso(self):
        advance(ON, 0.5)
        img = shot(ON)
        p = project(ON, (8.0, 0.0, 9.0))                           # piso livre de sombras
        patch = window(img, p, 22).mean(axis=2)
        detalhe = np.abs(np.diff(patch, axis=1)).mean()            # variação pixel a pixel (textura)
        self.assertGreater(detalhe, 1.2, "o piso deveria mostrar o padrão da textura")
        self.assertTrue(ON.materials.deck.uniforms["useTexture"].data)
        self.assertIn("baseTexture", ON.materials.deck.uniforms)

    def test_uv_proporcional_ao_tamanho(self):
        from geometry.boxGeometry import BoxGeometry
        g = BoxGeometry(36, 0.6, 36, uvTile=4.0)
        uv = np.asarray(g.attributes["vertexUV"].data)
        self.assertAlmostEqual(uv[:, 0].max(), 9.0)                # 36 m / 4 m = 9 repetições
        self.assertAlmostEqual(uv.min(), 0.0)


class TestSombras(unittest.TestCase):
    """Shadow mapping: sombras ligadas x desligadas, nas mesmas condições."""

    def pair(self, t):
        advance(ON, t)
        advance(OFF, t)
        return shot(ON), shot(OFF)

    def test_sombra_do_astronauta_aparece_no_chao(self):
        on, off = self.pair(17.0)                                   # acenando na marca
        a = ON.astronaut.root.getWorldPosition()
        alvo = sunShadowPoint((a[0], 1.2, a[2]))
        centro = project(ON, alvo)
        mascara = darker(window(on, centro, 5), window(off, centro, 5))
        self.assertGreater(mascara.mean(), 0.45, "deveria haver sombra do astronauta nessa região")
        # coerência com a direção do sol: o ponto simétrico (lado iluminado) NÃO escurece
        oposto = project(ON, (2 * a[0] - alvo[0], 0.0, 2 * a[2] - alvo[2]))
        self.assertLess(darker(window(on, oposto, 5), window(off, oposto, 5)).mean(), 0.1)

    def test_sombra_da_nave_aparece_no_chao(self):
        on, off = self.pair(12.0)
        alvo = sunShadowPoint(ON.ship.root.getWorldPosition())
        mascara = darker(window(on, project(ON, alvo), 8), window(off, project(ON, alvo), 8))
        self.assertGreater(mascara.mean(), 0.5)

    def test_sombra_some_quando_a_nave_sai_de_cena(self):
        on, off = self.pair(12.0)
        alvo = sunShadowPoint(ON.ship.root.getWorldPosition())
        c = project(ON, alvo)
        antes = darker(window(on, c, 8), window(off, c, 8)).mean()
        on2, off2 = self.pair(33.0)                                 # CONCLUIDO: nave invisível
        depois = darker(window(on2, c, 8), window(off2, c, 8)).mean()
        self.assertGreater(antes, 0.5)
        self.assertLess(depois, 0.05)

    def test_sombra_acompanha_o_movimento(self):
        # o astronauta caminha 2,9 m entre t=10,5 e t=13,5: o centroide da sombra se desloca
        def centroide(t):
            on, off = self.pair(t)
            a = ON.astronaut.root.getWorldPosition()
            c = project(ON, (a[0] + 0.5, 0.0, a[2] - 0.7))
            m = darker(window(on, c, 28), window(off, c, 28))
            ys, xs = np.nonzero(m)
            self.assertGreater(len(xs), 15)
            x0, y0 = int(round(c[0])) - 28, int(round(c[1])) - 28
            return np.array([xs.mean() + x0, ys.mean() + y0])
        deslocamento = np.linalg.norm(centroide(13.5) - centroide(10.5))
        self.assertGreater(deslocamento, 2.5)

    def test_sem_acne_em_piso_livre(self):
        on, off = self.pair(15.0)
        for ponto in ((8.0, 0.0, 9.0), (-6.0, 0.0, 12.0), (3.0, 0.0, 10.0)):
            c = project(ON, ponto)
            a, b = window(on, c, 12), window(off, c, 12)
            self.assertLess(np.abs(a - b).mean(), 0.8, "acne de sombra em " + str(ponto))
            self.assertLess(np.abs(a - b).max(), 12.0, "acne de sombra em " + str(ponto))

    def test_sombra_encosta_na_base_sem_flutuar(self):
        # Poste fino (0,4 x 3 x 0,4 m) em piso livre. A sombra dele deve começar junto da base:
        # com viés grande demais (ex.: o 0,01 do livro, ~0,9 m de profundidade) haveria um vazio
        # entre a base e o início da sombra ("peter-panning"). O lado oposto (iluminado) fica claro.
        from core.mesh import Mesh
        from geometry.boxGeometry import BoxGeometry
        base = (3.0, 8.0)
        geometria = BoxGeometry(0.4, 3.0, 0.4)
        postes = []
        for app in (ON, OFF):
            poste = Mesh(geometria, app.materials.armorBlack)
            poste.setPosition((base[0], 1.5, base[1]))
            app.scene.add(poste)
            postes.append((app, poste))
        try:
            on, off = self.pair(1.0)
            sun = np.array([0.32, -0.45])
            direcao = sun / np.linalg.norm(sun)                      # direção horizontal das sombras
            def escurecido(distancia):
                ponto = (base[0] + direcao[0] * distancia, 0.0, base[1] + direcao[1] * distancia)
                c = project(ON, ponto)
                return darker(window(on, c, 1), window(off, c, 1)).mean()
            self.assertGreater(escurecido(0.45), 0.6, "a sombra deveria começar junto da base")
            self.assertGreater(escurecido(0.80), 0.6)
            self.assertGreater(escurecido(1.50), 0.6)
            self.assertLess(escurecido(-0.60), 0.1, "o lado voltado para o sol deve ficar iluminado")
            self.assertLess(escurecido(-1.20), 0.1)
        finally:
            for app, poste in postes:
                app.scene.remove(poste)

    def test_mapa_de_profundidade_visivel_com_g(self):
        from headless_env import FakeInput
        advance(HUDAPP, 12.0)
        HUDAPP.update(0.0, FakeInput(down={"g"}))
        img = shot(HUDAPP)
        quadro = img[12:312, W - 312:W - 12]                        # miniatura do mapa (300x300)
        self.assertGreater(quadro.std(), 6.0)                       # há objetos gravados no mapa
        self.assertGreater(quadro.max(), 200)                       # e fundo (profundidade 1 = branco)
        HUDAPP.update(0.0, FakeInput(down={"g"}))                   # desliga

    def test_luz_dos_motores_segue_a_nave(self):
        advance(ON, 3.0)
        p1 = np.array(ON.ship.engineLight.getWorldPosition())
        n1 = np.array(ON.shipPose if False else ON.director.shipPose.position)
        advance(ON, 6.0)
        p2 = np.array(ON.ship.engineLight.getWorldPosition())
        n2 = np.array(ON.director.shipPose.position)
        self.assertGreater(np.linalg.norm(p2 - p1), 5.0)           # moveu junto com a nave
        self.assertAlmostEqual(np.linalg.norm(p1 - n1), np.linalg.norm(p2 - n2), delta=1e-6)

    def test_potencia_dos_motores_muda_a_cor_da_luz(self):
        advance(ON, 20.4)                                           # RESPOSTA: pulsos
        valores = []
        for t in np.linspace(18.8, 22.4, 40):
            advance(ON, t)
            valores.append(ON.ship.engineLight.color[0])
        self.assertGreater(max(valores) - min(valores), 0.5)


class TestTempoEControles(unittest.TestCase):

    def test_imagem_final_independe_da_taxa_de_quadros(self):
        advance(ON, 16.0, dt=1 / 30)
        a = shot(ON)
        advance(ON, 16.0, dt=1 / 144)
        b = shot(ON)
        self.assertLess(np.abs(a - b).mean(), 0.05)
        self.assertLess(np.abs(a - b).max(), 40)                    # tolerância p/ borda de 1 pixel

    def test_pausa_congela_a_cena_mas_nao_a_camera(self):
        from headless_env import FakeInput
        advance(HUDAPP, 14.0)
        HUDAPP.hud.visible = False
        a = shot(HUDAPP)
        HUDAPP.update(1 / 60, FakeInput(down={"space"}))
        self.assertTrue(HUDAPP.paused)
        for _ in range(120):
            HUDAPP.update(1 / 60, FakeInput())
        b = shot(HUDAPP)
        self.assertEqual(np.abs(a - b).max(), 0.0)                  # nada se moveu
        for _ in range(40):
            HUDAPP.update(1 / 60, FakeInput(pressed={"right"}))     # câmera responde mesmo pausado
        c = shot(HUDAPP)
        self.assertGreater(np.abs(a - c).mean(), 0.5)
        t_pausa = HUDAPP.director.totalTime
        HUDAPP.update(1 / 60, FakeInput(down={"space"}))            # retoma
        for _ in range(30):
            HUDAPP.update(1 / 60, FakeInput())
        self.assertGreater(HUDAPP.director.totalTime, t_pausa + 0.4)
        HUDAPP.hud.visible = True

    def test_camera_nao_entra_na_caixa_da_nave(self):
        # integração real: a câmera tenta ficar no centro da nave (modo "livre", zoom mínimo)
        from headless_env import FakeInput
        import math
        advance(HUDAPP, 12.0)                                       # nave pairando em HOLD
        orbit = HUDAPP.orbit
        orbit.setMode("4")
        centro = HUDAPP.ship.root.getWorldPosition()
        orbit.anchor = [centro[0], centro[1] + 1.0, centro[2]]
        orbit.target = list(orbit.anchor)
        orbit.azT = orbit.az = 0.7
        orbit.elT = orbit.el = 0.3
        orbit.distT = orbit.dist = 3.0                              # distância mínima
        for _ in range(20):
            orbit.update(1 / 60, FakeInput(), HUDAPP._followPoints())
        import numpy as np
        mundo = np.linalg.inv(HUDAPP.ship.body.getWorldMatrix()) @ np.array([*orbit.position, 1.0])
        local = mundo[:3] - HUDAPP.ship.OBB_CENTER
        dentro = np.all(np.abs(local) < HUDAPP.ship.OBB_HALF - 1e-6)
        self.assertFalse(dentro, "a câmera ficou dentro da nave")
        self.assertGreaterEqual(orbit.position[1], 0.4 - 1e-9)

    def test_reiniciar_volta_ao_estado_inicial(self):
        from headless_env import FakeInput
        advance(HUDAPP, 25.0)
        HUDAPP.update(0.0, FakeInput(down={"r"}))
        self.assertEqual(HUDAPP.director.state.name, "APROXIMACAO")
        self.assertEqual(HUDAPP.director.totalTime, 0.0)

    def test_hud_aparece_e_pode_ser_ocultado(self):
        from headless_env import FakeInput
        advance(HUDAPP, 5.0)
        HUDAPP.hud.visible = True
        com = shot(HUDAPP)
        HUDAPP.hud.visible = False
        sem = shot(HUDAPP)
        HUDAPP.hud.visible = True
        topo = (slice(12, 100), slice(12, 500))
        self.assertGreater(np.abs(com[topo] - sem[topo]).mean(), 5.0)

    def test_velocidade_da_simulacao(self):
        from headless_env import FakeInput
        HUDAPP.director.reset()
        HUDAPP.speedIndex = 2
        HUDAPP.update(0.0, FakeInput(down={"."}))
        self.assertEqual(HUDAPP.timeScale, 2.0)
        HUDAPP.update(1.0, FakeInput())
        self.assertAlmostEqual(HUDAPP.director.totalTime, 2.0, places=6)
        HUDAPP.speedIndex = 2


if __name__ == "__main__":
    unittest.main(verbosity=2)
