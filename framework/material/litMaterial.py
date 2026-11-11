"""
Materiais sensíveis à luz (Lambert e Phong) com textura e sombra opcionais.
Base: STEMKOSKI & PASCALE (2022), seções 6.4.2 e 6.9.2.

  * Lambert : ambiente + difusa           (superfície fosca)
  * Phong   : ambiente + difusa + especular (brilho metálico; specularStrength, shininess)

Os shaders ficam em shaders/lit.vert e shaders/lit.frag; o Phong liga USE_SPECULAR.
Uniforms principais: baseColor, light0..3, useTexture/baseTexture, repeatUV,
useShadow/shadow0 e (Phong) viewPosition, specularStrength, shininess.
"""
from core.openGLUtils import OpenGLUtils
from material.material import Material
from OpenGL.GL import *


class LitMaterial(Material):

    def __init__(self, texture=None, properties=None, useShadow=False, specular=False):
        defines = ["USE_SPECULAR"] if specular else []
        super().__init__(OpenGLUtils.loadShader("lit.vert"),
                         OpenGLUtils.loadShader("lit.frag", defines))

        self.addUniform("vec3", "baseColor", [1.0, 1.0, 1.0])
        self.addUniform("Light", "light0", None)
        self.addUniform("Light", "light1", None)
        self.addUniform("Light", "light2", None)
        self.addUniform("Light", "light3", None)
        self.addUniform("vec2", "repeatUV", [1.0, 1.0])

        if texture is None:
            self.addUniform("bool", "useTexture", False)
        else:
            self.addUniform("bool", "useTexture", True)
            self.addUniform("sampler2D", "baseTexture", [texture.textureRef, 1])

        if not useShadow:
            self.addUniform("bool", "useShadow", False)
        else:
            self.addUniform("bool", "useShadow", True)
            self.addUniform("Shadow", "shadow0", None)

        if specular:
            self.addUniform("vec3", "viewPosition", [0, 0, 0])
            self.addUniform("float", "specularStrength", 1.0)
            self.addUniform("float", "shininess", 32.0)

        self.locateUniforms()

        self.settings["doubleSide"] = False     # sólidos fechados: descarta faces de trás
        self.settings["wireframe"] = False
        self.settings["lineWidth"] = 1
        self.setProperties(properties or {})

    def updateRenderSettings(self):
        if self.settings["doubleSide"]:
            glDisable(GL_CULL_FACE)
        else:
            glEnable(GL_CULL_FACE)
        if self.settings["wireframe"]:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glLineWidth(self.settings["lineWidth"])
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
