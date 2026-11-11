"""
Atributo de vértice (dados por vértice guardados num VBO).
Base: STEMKOSKI & PASCALE (2022), seção 2.3.2.

associateVariable(): liga o buffer à variável `in` do shader. A associação fica
armazenada no VAO que estiver ativo (ver core/mesh.py).
"""
from OpenGL.GL import *
import numpy


class Attribute(object):

    def __init__(self, dataType, data):
        self.dataType = dataType      # int | float | vec2 | vec3 | vec4
        self.data = data              # lista ou ndarray (N x componentes)
        self.bufferRef = glGenBuffers(1)
        self.uploadData()

    def uploadData(self):
        data = numpy.ascontiguousarray(numpy.array(self.data), dtype=numpy.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.bufferRef)
        glBufferData(GL_ARRAY_BUFFER, data.ravel(), GL_STATIC_DRAW)

    def associateVariable(self, programRef, variableName):
        variableRef = glGetAttribLocation(programRef, variableName)
        if variableRef == -1:           # o programa não usa esta variável
            return
        glBindBuffer(GL_ARRAY_BUFFER, self.bufferRef)
        if self.dataType == "int":
            glVertexAttribPointer(variableRef, 1, GL_INT, False, 0, None)
        elif self.dataType == "float":
            glVertexAttribPointer(variableRef, 1, GL_FLOAT, False, 0, None)
        elif self.dataType == "vec2":
            glVertexAttribPointer(variableRef, 2, GL_FLOAT, False, 0, None)
        elif self.dataType == "vec3":
            glVertexAttribPointer(variableRef, 3, GL_FLOAT, False, 0, None)
        elif self.dataType == "vec4":
            glVertexAttribPointer(variableRef, 4, GL_FLOAT, False, 0, None)
        else:
            raise Exception("Attribute " + variableName + " has unknown type " + str(self.dataType))
        glEnableVertexAttribArray(variableRef)
