"""
Aplicação: monta a cena, avança a simulação e desenha cada quadro.
É independente da janela (main.py fornece Pygame; os testes fornecem entrada simulada).

Ordem de cada quadro (update):
  1. controles (pausa, reiniciar, velocidade, mapa de sombras, ajuda);
  2. diretor da interação avança por dt_simulado  (0 se pausado)  -> poses de nave e astronauta;
  3. poses são aplicadas às juntas (matrizes locais recompostas);
  4. câmera orbital avança por dt REAL (continua respondendo durante a pausa);
render():
  passe de sombra (cena vista da luz) -> passe principal -> HUD.
"""
import math
import bootstrap  # noqa: F401  (ajusta sys.path)
import os
from dataclasses import dataclass
from core.renderer import Renderer
from core.scene import Scene
from core.texture import Texture
from animation import InteractionDirector, State
from astronaut import Astronaut
from spaceship import Spaceship
from scene import Environment
from camera import OrbitCamera
from hud import Hud
import lighting

ROOT = os.path.dirname(os.path.abspath(__file__))
SPEEDS = [0.25, 0.5, 1.0, 2.0, 4.0]


@dataclass
class Options:
    loop: bool = False
    hud: bool = True
    shadows: bool = True
    shadowResolution: int = 2048
    pcf: int = 1


class Application(object):

    def __init__(self, windowSize, options=None):
        self.options = options or Options()
        W, H = windowSize
        self.renderer = Renderer(clearColor=[0.0, 0.0, 0.015], windowSize=windowSize)
        self.scene = Scene()

        floorTexture = Texture(os.path.join(ROOT, "textures", "painel_metalico.png"))
        hullTexture = Texture(os.path.join(ROOT, "textures", "casco_cinza.png"))
        self.materials = lighting.Materials(floorTexture, hullTexture, useShadow=True)

        self.environment = Environment(self.materials)
        self.scene.add(self.environment.root)

        self.sun, engineLight, padLight = lighting.createLights(self.scene)
        self.astronaut = Astronaut(self.materials)
        self.scene.add(self.astronaut.root)
        self.ship = Spaceship(self.materials)
        self.scene.add(self.ship.root)
        self.ship.attachEngineLight(engineLight)

        if self.options.shadows:
            res = (self.options.shadowResolution,) * 2
            lighting.enableSun(self.renderer, self.sun, resolution=res, pcf=self.options.pcf)

        self.director = InteractionDirector(loop=self.options.loop)
        self.orbit = OrbitCamera(aspectRatio=W / H)
        self.orbit.obstacle = self.ship.pushOut
        self.hud = Hud(windowSize)
        self.hud.visible = self.options.hud
        if self.options.shadows:
            self.hud.attachShadowMap(self.renderer.shadowObject.renderTarget.texture)

        self.paused = False
        self.speedIndex = 2
        self.fps = 60.0
        self._applyPoses()
        self.orbit.update(0.0, _NoInput(), self._followPoints())
        self.orbit.update(10.0, _NoInput(), self._followPoints())      # posição inicial imediata

    # ------------------------------------------------------------------
    @property
    def timeScale(self):
        return SPEEDS[self.speedIndex]

    def _applyPoses(self):
        self.astronaut.applyPose(self.director.astronautPose)
        self.ship.applyPose(self.director.shipPose)

    def _followPoints(self):
        a = self.director.astronautPose
        return {"astronauta": (a.x, 0.0, a.z), "nave": tuple(self.director.shipPose.position)}

    def update(self, realDt, inp):
        # ---- controles ----
        if inp.isKeyDown("space"):
            self.paused = not self.paused
        if inp.isKeyDown("r"):
            self.director.reset()
        if inp.isKeyDown("h"):
            self.hud.showHelp = not self.hud.showHelp
        if inp.isKeyDown("g"):
            self.shadowMapOn = self.hud.toggleShadowMap()
        if inp.isKeyDown("."):
            self.speedIndex = min(self.speedIndex + 1, len(SPEEDS) - 1)
        if inp.isKeyDown(","):
            self.speedIndex = max(self.speedIndex - 1, 0)

        # ---- simulação: dt simulado = dt real x velocidade (0 quando pausado) ----
        simDt = 0.0 if self.paused else realDt * self.timeScale
        self.director.update(simDt)
        self._applyPoses()

        # ---- câmera e ambiente: dt real ----
        self.orbit.update(realDt, inp, self._followPoints())
        self.environment.update(self.orbit.position)

        if realDt > 0:
            self.fps += (1.0 / realDt - self.fps) * 0.05
        self.hud.update(self.director.label(), self.director.progress, self.director.totalTime, self.fps,
                        self.paused, self.timeScale, self.orbit.mode,
                        getattr(self, "shadowMapOn", False))

    shadowMapOn = False

    def render(self):
        self.renderer.render(self.scene, self.orbit.camera)
        self.mainDrawCalls = self.renderer.drawCalls          # sombra + principal
        self.hud.render(self.renderer)

    def caption(self):
        return "Warhammer 40K - Nave x Astronauta | %s | %s" % (
            self.director.state.name, "PAUSADO" if self.paused else "%.0f FPS" % self.fps)


class _NoInput(object):
    mouseDelta = (0, 0)
    mouseWheel = 0

    def isKeyDown(self, k): return False
    def isKeyPressed(self, k): return False
    def isMousePressed(self, b=1): return False
