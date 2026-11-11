"""
Iluminação, materiais e sombras da cena.

LUZES (limite do framework: 4)
  1. AmbientLight     : cor fria e fraca (luz indireta do espaço);
  2. DirectionalLight : "sol" — única luz que projeta sombra (shadow mapping);
  3. PointLight       : brilho dos motores da nave (filha da nave, segue o movimento);
  4. PointLight       : luminária vermelha da marca de inspeção.

MATERIAIS (PhongMaterial/LambertMaterial: ambiente + difusa [+ especular])
  baseColor multiplica a textura e a iluminação; specularStrength/shininess controlam o
  brilho (metal = forte e concentrado; tecido/couro = fosco).

SOMBRAS: parâmetros do shadow mapping (resolução, viés, PCF) ficam em SHADOW.
"""
import math
from light.ambientLight import AmbientLight
from light.directionalLight import DirectionalLight
from light.pointLight import PointLight
from material.phongMaterial import PhongMaterial
from material.lambertMaterial import LambertMaterial
from material.surfaceMaterial import SurfaceMaterial

# direção dos raios do sol: vem de cima, do lado da câmera e da esquerda; as sombras caem para +x e -z
SUN_DIRECTION = (0.32, -0.80, -0.45)
SUN_COLOR = (1.0, 0.96, 0.90)
AMBIENT_COLOR = (0.30, 0.32, 0.42)

# região do mundo coberta pelo mapa de sombras (câmera ortográfica da luz)
SHADOW = {
    "resolution": (2048, 2048),
    "target": (-3.0, 1.5, -1.0),          # centro da região
    "halfSize": 23.0,                      # metade do lado do volume ortográfico (m)
    "distance": 45.0,                      # distância da luz ao alvo
    "strength": 0.72,
    "bias": 0.0004,
    "slopeBias": 0.0025,
    "pcf": 1,
}


def _norm(v):
    l = math.sqrt(sum(c * c for c in v))
    return [c / l for c in v]


def createLights(scene):
    """Adiciona as luzes à cena e devolve (sol, luzMotor, luzMarca)."""
    scene.add(AmbientLight(color=AMBIENT_COLOR))

    d = _norm(SUN_DIRECTION)
    sun = DirectionalLight(color=SUN_COLOR, direction=d)       # 1º a direção...
    t = SHADOW["target"]
    k = SHADOW["distance"]
    sun.setPosition([t[0] - d[0] * k, t[1] - d[1] * k, t[2] - d[2] * k])   # ...depois a posição
    scene.add(sun)

    engineLight = PointLight(color=(0, 0, 0), position=(0, 0, 0), attenuation=(1.0, 0.03, 0.012))
    padLight = PointLight(color=(0.38, 0.05, 0.03), position=(1.6, 0.9, 3.4), attenuation=(1.0, 0.28, 0.20))
    scene.add(padLight)
    return sun, engineLight, padLight


def enableSun(renderer, sun, resolution=None, pcf=None):
    s = SHADOW
    h = s["halfSize"]
    res = tuple(resolution) if resolution else s["resolution"]
    renderer.enableShadows(sun, strength=s["strength"], resolution=res,
                           cameraBounds=(-h, h, -h, h, 1.0, 2 * s["distance"]),
                           bias=s["bias"], slopeBias=s["slopeBias"],
                           pcf=s["pcf"] if pcf is None else pcf)


class Materials(object):
    """Biblioteca de materiais compartilhados pelos modelos (uma instância por cor/brilho)."""

    def __init__(self, floorTexture, hullTexture, useShadow=True):
        P = lambda color, spec, shin, tex=None, rep=None: self._phong(color, spec, shin, tex, rep, useShadow)
        L = lambda color: self._lambert(color, useShadow)

        # --- armadura ---
        self.armorBlack = P((0.13, 0.13, 0.15), 1.0, 56)
        self.graphite = P((0.30, 0.31, 0.35), 0.8, 40)
        self.silver = P((0.78, 0.80, 0.85), 1.5, 90)
        self.gold = P((1.0, 0.76, 0.22), 1.6, 70)
        self.redArmor = P((0.42, 0.02, 0.02), 0.7, 40)
        self.bone = L((0.80, 0.76, 0.66))
        self.leather = L((0.34, 0.22, 0.13))
        self.clothGrey = L((0.62, 0.60, 0.55))
        self.clothRed = L((0.26, 0.02, 0.03))
        self.bronze = P((0.58, 0.38, 0.17), 1.0, 48)

        # --- nave / ambiente ---
        self.hull = P((0.86, 0.88, 0.95), 0.55, 28, hullTexture)
        self.hullDark = P((0.26, 0.27, 0.31), 0.7, 34)
        self.hullWhite = P((0.90, 0.90, 0.86), 0.8, 50)
        self.windowGlass = P((0.02, 0.02, 0.03), 2.0, 120)
        self.deck = P((1.0, 1.0, 1.0), 0.35, 20, floorTexture)

        # --- emissivos (sem iluminação): cada um com seu próprio material ---
        self.visor = SurfaceMaterial({"baseColor": [1.0, 0.06, 0.04]})
        self.emissiveGold = SurfaceMaterial({"baseColor": [1.0, 0.70, 0.15]})

    @staticmethod
    def _phong(color, spec, shin, tex, rep, useShadow):
        m = PhongMaterial(texture=tex, useShadow=useShadow,
                          properties={"baseColor": list(color), "specularStrength": spec,
                                      "shininess": float(shin)})
        if rep:
            m.uniforms["repeatUV"].data = list(rep)
        return m

    @staticmethod
    def _lambert(color, useShadow):
        return LambertMaterial(useShadow=useShadow, properties={"baseColor": list(color)})
