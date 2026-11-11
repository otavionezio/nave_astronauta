"""
Shadow: tudo que o shadow mapping precisa (STEMKOSKI & PASCALE, 2022, seção 6.9.2).

  * lightSource : luz direcional que projeta a sombra;
  * camera      : "câmera da luz" (ortográfica), filha da luz -> usa a posição e a
                  direção da luz; define a região do mundo que gera/recebe sombra;
  * renderTarget: framebuffer cuja textura (mapa de profundidade) recebe o passe de sombra;
  * material    : DepthMaterial (grava a profundidade);
  * strength    : quanto a luz direta é reduzida dentro da sombra (0..1);
  * bias        : deslocamento mínimo na comparação de profundidades (evita "acne");
  * slopeBias   : viés extra proporcional à inclinação da superfície em relação à luz;
  * pcf         : raio do filtro de vizinhança (0 = sombra dura; 1 = 3x3; 2 = 5x5).

Adaptação: o mapa usa textura R32F e filtro NEAREST (a comparação deve ser feita com
valores exatos; a suavização das bordas é feita por PCF no shader).
"""
from OpenGL.GL import *
from core.camera import Camera
from core.renderTarget import RenderTarget
from material.depthMaterial import DepthMaterial


class Shadow(object):

    def __init__(self, lightSource, strength=0.5, resolution=(512, 512),
                 cameraBounds=(-5, 5, -5, 5, 0, 20), bias=0.01, slopeBias=0.0, pcf=0):
        self.lightSource = lightSource
        self.camera = Camera()
        left, right, bottom, top, near, far = cameraBounds
        self.camera.setOrthographic(left, right, bottom, top, near, far)
        self.lightSource.add(self.camera)

        self.renderTarget = RenderTarget(
            resolution,
            properties={"wrap": GL_CLAMP_TO_BORDER, "magFilter": GL_NEAREST, "minFilter": GL_NEAREST},
            floatColor=True)
        self.material = DepthMaterial()
        self.strength = strength
        self.bias = bias
        self.slopeBias = slopeBias
        self.pcf = pcf

    def updateInternal(self):
        self.camera.updateViewMatrix()
        self.material.uniforms["viewMatrix"].data = self.camera.viewMatrix
        self.material.uniforms["projectionMatrix"].data = self.camera.projectionMatrix
