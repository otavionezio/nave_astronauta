from core.object3D import Object3D
from OpenGL.GL import *


class Mesh(Object3D):
    """Objeto renderizável = Geometry (vértices) + Material (shaders/uniforms).
    Cada Mesh guarda um VAO que associa os buffers da geometria às variáveis `in`
    do shader do material."""

    def __init__(self, geometry, material):
        super().__init__()
        self.geometry = geometry
        self.material = material
        self.visible = True
        self.castShadow = True      # participa do passe de sombra? (extensão)

        self.vaoRef = glGenVertexArrays(1)
        glBindVertexArray(self.vaoRef)
        for variableName, attributeObject in geometry.attributes.items():
            attributeObject.associateVariable(material.programRef, variableName)
        glBindVertexArray(0)
