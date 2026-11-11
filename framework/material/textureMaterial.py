from core.openGLUtils import OpenGLUtils
from material.material import Material
from OpenGL.GL import *


class TextureMaterial(Material):
    """Textura sem iluminação (HUD). STEMKOSKI & PASCALE (2022), seção 5.3.
    fragmentFile permite trocar o fragment shader (ex.: depthview.frag p/ depuração)."""

    def __init__(self, texture, properties=None, fragmentFile="texture.frag"):
        super().__init__(OpenGLUtils.loadShader("texture.vert"), OpenGLUtils.loadShader(fragmentFile))
        self.addUniform("vec3", "baseColor", [1.0, 1.0, 1.0])
        self.addUniform("sampler2D", "baseTexture", [texture.textureRef, 1])
        self.addUniform("vec2", "repeatUV", [1.0, 1.0])
        self.addUniform("vec2", "offsetUV", [0.0, 0.0])
        self.locateUniforms()
        self.settings["doubleSide"] = True
        self.settings["wireframe"] = False
        self.settings["lineWidth"] = 1
        self.setProperties(properties or {})

    def updateRenderSettings(self):
        if self.settings["doubleSide"]:
            glDisable(GL_CULL_FACE)
        else:
            glEnable(GL_CULL_FACE)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
