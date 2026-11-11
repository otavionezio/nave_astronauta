from material.basicMaterial import BasicMaterial
from OpenGL.GL import *


class PointMaterial(BasicMaterial):
    """Vértices como pontos quadrados (estrelas do fundo)."""

    def __init__(self, properties=None):
        super().__init__()
        self.settings["drawStyle"] = GL_POINTS
        self.settings["pointSize"] = 2
        self.setProperties(properties or {})

    def updateRenderSettings(self):
        glPointSize(self.settings["pointSize"])
