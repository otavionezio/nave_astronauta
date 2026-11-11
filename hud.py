"""
HUD: textos 2D desenhados com Pygame (fonte) -> Texture -> retângulo numa cena própria
renderizada com câmera ORTOGRÁFICA em coordenadas de pixel (técnica da seção 5.7.3 do livro).
O texto só é redesenhado (e reenviado à GPU) quando muda.
"""
import pygame
from OpenGL.GL import GL_LINEAR, GL_CLAMP_TO_EDGE
from core.scene import Scene
from core.camera import Camera
from core.mesh import Mesh
from core.texture import Texture
from geometry.rectangleGeometry import RectangleGeometry
from material.textureMaterial import TextureMaterial

HELP_LINES = [
    "CONTROLES",
    "Setas / mouse (arrastar)  orbitar",
    "W,S / + - / roda          aproximar, afastar",
    "A,D  Q,E                  deslocar alvo / altura",
    "1 geral  2 astronauta  3 nave  4 livre",
    "ESPACO  pausar/retomar    R  reiniciar",
    ", .  velocidade 0.25x..4x",
    "G  mapa de sombras   H  ajuda   ESC  sair",
]


LONGEST_STATUS = [
    "2/6  ESTABILIZACAO - a nave freia e gira para encarar o astronauta",
    "executando | 60 FPS | sombras: shadow mapping  [mapa visivel] | H = ajuda",
    "tempo simulado  999.9 s   velocidade 0.25x   camera: astronauta   ",
]


class _Panel(object):
    def __init__(self, hud, width, height):
        self.width, self.height = width, height
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.texture = Texture(None, {"magFilter": GL_LINEAR, "minFilter": GL_LINEAR, "wrap": GL_CLAMP_TO_EDGE})
        self.texture.surface = self.surface
        self.mesh = Mesh(RectangleGeometry(width, height), TextureMaterial(self.texture))
        hud.scene.add(self.mesh)
        self.key = None

    def place(self, left, top, windowHeight):
        self.mesh.setPosition([left + self.width / 2, windowHeight - top - self.height / 2, 0])

    def redraw(self, lines, fonts, key, bar=None):
        if key == self.key:
            return
        self.key = key
        self.surface.fill((6, 8, 14, 175))
        y = 8
        for text, size in lines:
            img = fonts[size].render(text, True, (235, 215, 160) if size == 24 else (205, 210, 225))
            self.surface.blit(img, (10, y))
            y += fonts[size].get_linesize() + 2
        if bar is not None:
            pygame.draw.rect(self.surface, (70, 70, 85), (10, self.height - 18, self.width - 20, 8))
            pygame.draw.rect(self.surface, (225, 170, 40), (10, self.height - 18, int((self.width - 20) * bar), 8))
        self.texture.uploadData()


class Hud(object):

    def __init__(self, windowSize):
        self.width, self.height = windowSize
        self.scene = Scene()
        self.camera = Camera()
        self.camera.setOrthographic(0, self.width, 0, self.height, -1, 1)
        pygame.font.init()
        self.fonts = {24: pygame.font.Font(None, 24), 20: pygame.font.Font(None, 20)}

        # tamanhos medidos com a fonte real (a largura dos caracteres varia entre sistemas)
        helpWidth = max(self.fonts[24 if i == 0 else 20].size(t)[0] for i, t in enumerate(HELP_LINES)) + 24
        helpHeight = sum(self.fonts[24 if i == 0 else 20].get_linesize() + 2 for i in range(len(HELP_LINES))) + 16
        statusWidth = max(self.fonts[24].size(l)[0] for l in LONGEST_STATUS) + 24
        statusHeight = (self.fonts[24].get_linesize() + 2 * (self.fonts[20].get_linesize() + 2) + 2 + 36)
        self.status = _Panel(self, statusWidth, statusHeight)
        self.help = _Panel(self, helpWidth, helpHeight)
        self.status.place(12, 12, self.height)
        self.help.place(12, self.height - self.help.height - 12, self.height)
        self.showHelp = False            # H mostra/oculta a ajuda
        self.visible = True
        self.shadowMesh = None

    def attachShadowMap(self, texture, size=300):
        """Retângulo que mostra o mapa de profundidade (depuração, tecla G)."""
        self.shadowMesh = Mesh(RectangleGeometry(size, size),
                               TextureMaterial(texture, fragmentFile="depthview.frag"))
        self.shadowMesh.setPosition([self.width - size / 2 - 12, self.height - size / 2 - 12, 0])
        self.shadowMesh.visible = False
        self.scene.add(self.shadowMesh)

    def toggleShadowMap(self):
        if self.shadowMesh is not None:
            self.shadowMesh.visible = not self.shadowMesh.visible
        return self.shadowMesh is not None and self.shadowMesh.visible

    def update(self, label, progress, totalTime, fps, paused, speed, cameraMode, shadowMapOn):
        bar = round(progress * 80) / 80.0
        lines = [(label, 24),
                 ("tempo simulado %6.1f s   velocidade %.2fx   camera: %s" % (totalTime, speed, cameraMode), 20),
                 ("%s | %d FPS | sombras: shadow mapping%s | H = ajuda" % (
                     "PAUSADO" if paused else "executando", fps, "  [mapa visivel]" if shadowMapOn else ""), 20)]
        key = (label, bar, int(totalTime * 5), int(fps / 2), paused, speed, cameraMode, shadowMapOn)
        self.status.redraw(lines, self.fonts, key, bar=bar)
        self.help.redraw([(HELP_LINES[0], 24)] + [(t, 20) for t in HELP_LINES[1:]], self.fonts, "help")
        self.help.mesh.visible = self.showHelp

    def render(self, renderer):
        if self.visible:
            renderer.render(self.scene, self.camera, clearColor=False, clearDepth=True, useShadows=False)
