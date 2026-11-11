"""
Textura 2D (imagem carregada com Pygame e enviada à GPU).
Base: STEMKOSKI & PASCALE (2022), seção 5.1.

Adaptações:
  * pygame.image.tobytes (tostring está obsoleto em versões recentes do Pygame);
  * allocateFloat(): textura de 32 bits em ponto flutuante (canal R) usada como
    mapa de profundidade do shadow mapping (o livro grava a profundidade em RGBA8,
    ou seja, só 256 níveis; com float32 o viés pode ser bem menor).
"""
import pygame
from OpenGL.GL import *


class Texture(object):

    def __init__(self, fileName=None, properties=None):
        self.surface = None
        self.textureRef = glGenTextures(1)
        self.properties = {
            "magFilter": GL_LINEAR,
            "minFilter": GL_LINEAR_MIPMAP_LINEAR,
            "wrap": GL_REPEAT
        }
        self.setProperties(properties or {})
        if fileName is not None:
            self.loadImage(fileName)
            self.uploadData()

    def loadImage(self, fileName):
        self.surface = pygame.image.load(fileName)

    def setProperties(self, props):
        for name, data in props.items():
            if name in self.properties.keys():
                self.properties[name] = data
            else:
                raise Exception("Texture has no property with name: " + name)

    def _applyParameters(self):
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, self.properties["magFilter"])
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, self.properties["minFilter"])
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, self.properties["wrap"])
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, self.properties["wrap"])
        # cor de borda branca: importante para as sombras (fora do mapa = profundidade 1 = sem sombra)
        glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, [1.0, 1.0, 1.0, 1.0])

    def uploadData(self):
        width = self.surface.get_width()
        height = self.surface.get_height()
        toBytes = getattr(pygame.image, "tobytes", None) or pygame.image.tostring
        pixelData = toBytes(self.surface, "RGBA", True)       # True = inverte o eixo y

        glBindTexture(GL_TEXTURE_2D, self.textureRef)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA,
                     GL_UNSIGNED_BYTE, pixelData)
        glGenerateMipmap(GL_TEXTURE_2D)
        self._applyParameters()

    def allocateFloat(self, width, height):
        """Reserva uma textura R32F vazia (sem mipmaps; use filtros NEAREST/LINEAR)."""
        if self.properties["minFilter"] in (GL_NEAREST_MIPMAP_NEAREST, GL_NEAREST_MIPMAP_LINEAR,
                                            GL_LINEAR_MIPMAP_NEAREST, GL_LINEAR_MIPMAP_LINEAR):
            raise Exception("allocateFloat: minFilter não pode usar mipmap")
        glBindTexture(GL_TEXTURE_2D, self.textureRef)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_R32F, width, height, 0, GL_RED, GL_FLOAT, None)
        self._applyParameters()
