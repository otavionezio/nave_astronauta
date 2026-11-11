from core.openGLUtils import OpenGLUtils
from material.material import Material


class DepthMaterial(Material):
    """Material do passe de sombra: grava gl_FragCoord.z (profundidade vista da luz).
    Shaders: depth.vert / depth.frag. (STEMKOSKI & PASCALE, 2022, seção 6.9.2)"""
    def __init__(self):
        super().__init__(OpenGLUtils.loadShader("depth.vert"), OpenGLUtils.loadShader("depth.frag"))
        self.locateUniforms()
