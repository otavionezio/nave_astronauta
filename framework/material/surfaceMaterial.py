from material.basicMaterial import BasicMaterial
from OpenGL.GL import *


class SurfaceMaterial(BasicMaterial):
    """Superfície (triângulos) sem iluminação: usada p/ elementos emissivos (motores, visor)."""

    def __init__(self, properties=None):
        super().__init__()
        self.settings["drawStyle"] = GL_TRIANGLES
        self.settings["doubleSide"] = False
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
