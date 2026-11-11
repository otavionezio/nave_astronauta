"""
Material: programa GLSL + uniforms + configurações de renderização.
Base: STEMKOSKI & PASCALE (2022), seção 4.4.1.

Adaptação: programas com o mesmo código-fonte são compilados UMA vez e
compartilhados entre os materiais (cada Material continua com seus próprios uniforms).
"""
from core.openGLUtils import OpenGLUtils
from core.uniform import Uniform
from OpenGL.GL import *


class Material(object):

    _programCache = {}

    def __init__(self, vertexShaderCode, fragmentShaderCode):
        key = (vertexShaderCode, fragmentShaderCode)
        if key not in Material._programCache:
            Material._programCache[key] = OpenGLUtils.initializeProgram(
                vertexShaderCode, fragmentShaderCode)
        self.programRef = Material._programCache[key]

        # Uniform objects indexados pelo nome da variável no shader
        self.uniforms = {}
        # presentes na maioria dos shaders; valores definidos pelo Renderer
        self.uniforms["modelMatrix"] = Uniform("mat4", None)
        self.uniforms["viewMatrix"] = Uniform("mat4", None)
        self.uniforms["projectionMatrix"] = Uniform("mat4", None)

        # configurações do OpenGL (estado de renderização)
        self.settings = {}
        self.settings["drawStyle"] = GL_TRIANGLES

    def addUniform(self, dataType, variableName, data):
        self.uniforms[variableName] = Uniform(dataType, data)

    def locateUniforms(self):
        for variableName, uniformObject in self.uniforms.items():
            uniformObject.locateVariable(self.programRef, variableName)

    def updateRenderSettings(self):
        pass

    def setProperties(self, properties):
        for name, data in properties.items():
            if name in self.uniforms.keys():
                self.uniforms[name].data = data
            elif name in self.settings.keys():
                self.settings[name] = data
            else:
                raise Exception("Material has no property named: " + name)
