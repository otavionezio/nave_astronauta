from core.openGLUtils import OpenGLUtils
from material.material import Material


class BasicMaterial(Material):
    """Sem iluminação: baseColor (e, opcionalmente, cores de vértice). Shaders: basic.vert/.frag."""
    def __init__(self):
        super().__init__(OpenGLUtils.loadShader("basic.vert"), OpenGLUtils.loadShader("basic.frag"))
        self.addUniform("vec3", "baseColor", [1.0, 1.0, 1.0])
        self.addUniform("bool", "useVertexColors", False)
        self.locateUniforms()
