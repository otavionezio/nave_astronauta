"""
Alvo de renderização fora da tela (framebuffer + textura de cor + buffer de profundidade).
Base: STEMKOSKI & PASCALE (2022), seção 5.8.

floatColor=True cria a textura de cor em R32F; é o formato do mapa de sombras.
"""
import pygame
from OpenGL.GL import *
from core.texture import Texture


class RenderTarget(object):

    def __init__(self, resolution=(512, 512), texture=None, properties=None, floatColor=False):
        self.width, self.height = resolution

        if texture is not None:
            self.texture = texture
        else:
            self.texture = Texture(None, {"magFilter": GL_LINEAR, "minFilter": GL_LINEAR,
                                          "wrap": GL_CLAMP_TO_EDGE})
            self.texture.setProperties(properties or {})
            if floatColor:
                self.texture.allocateFloat(self.width, self.height)
            else:
                self.texture.surface = pygame.Surface((self.width, self.height))
                self.texture.uploadData()

        self.framebufferRef = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.framebufferRef)
        glFramebufferTexture(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self.texture.textureRef, 0)

        # profundidade necessária para o teste de profundidade durante o passe
        depthBufferRef = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, depthBufferRef)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, self.width, self.height)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, depthBufferRef)

        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        if status != GL_FRAMEBUFFER_COMPLETE:
            raise Exception("Framebuffer status error: " + str(status))
