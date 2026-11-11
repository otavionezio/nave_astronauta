"""
Geometry: dicionário de Attributes (posição, cor, UV, normais...) + contagem de vértices.
Base: STEMKOSKI & PASCALE (2022), seção 4.3 (applyMatrix e merge: 4.3.6; normais: 6.3.4).

Adaptações:
  * applyMatrix vetorizado (NumPy) e as NORMAIS usam a inversa transposta da parte 3x3
    da matriz (correto também com escala não uniforme; o livro usa só a rotação);
  * merge() concatena arrays NumPy e envia os dados à GPU uma única vez.
"""
import numpy
from core.attribute import Attribute


class Geometry(object):

    def __init__(self):
        # Attributes indexados pelo nome da variável `in` do shader
        self.attributes = {}
        self.vertexCount = None

    def addAttribute(self, dataType, variableName, data):
        self.attributes[variableName] = Attribute(dataType, data)

    def countVertices(self):
        attrib = list(self.attributes.values())[0]
        self.vertexCount = len(attrib.data)

    # aplica uma matriz 4x4 aos vértices (posição: completa; normais: inversa transposta)
    def applyMatrix(self, matrix, variableName="vertexPosition"):
        matrix = numpy.asarray(matrix, dtype=float)
        linear = matrix[0:3, 0:3]
        normalMatrix = numpy.linalg.inv(linear).T

        positions = numpy.asarray(self.attributes[variableName].data, dtype=float)
        self.attributes[variableName].data = positions @ linear.T + matrix[0:3, 3]
        self.attributes[variableName].uploadData()

        for normalName in ("vertexNormal", "faceNormal"):
            if normalName in self.attributes:
                normals = numpy.asarray(self.attributes[normalName].data, dtype=float)
                normals = normals @ normalMatrix.T
                lengths = numpy.linalg.norm(normals, axis=1, keepdims=True)
                lengths[lengths == 0] = 1.0
                self.attributes[normalName].data = normals / lengths
                self.attributes[normalName].uploadData()

    # junta os dados de outra geometria (mesmos nomes de atributos)
    def merge(self, otherGeometry):
        for variableName, attributeObject in self.attributes.items():
            attributeObject.data = numpy.concatenate(
                [numpy.asarray(attributeObject.data, dtype=float),
                 numpy.asarray(otherGeometry.attributes[variableName].data, dtype=float)])
            attributeObject.uploadData()
        self.countVertices()
