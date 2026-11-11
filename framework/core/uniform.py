"""
Uniforms: valores enviados do Python (CPU) para o programa GLSL (GPU).
Base: STEMKOSKI & PASCALE (2022), seções 2.4.2, 3.4, 5.3, 6.4.1 e 6.9.2.

Tipos: int, bool, float, vec2, vec3, vec4, mat4, sampler2D, Light, Shadow.
  * mat4 usa GL_TRUE em glUniformMatrix4fv: o NumPy guarda por linhas e o GLSL
    espera colunas, então pedimos a transposição;
  * sampler2D guarda [texturaRef, unidadeDeTextura];
  * Light / Shadow são structs GLSL: um glUniform por campo.

Adaptações: Light usa posição/direção de MUNDO (uma luz filha da nave precisa
seguir a nave); o struct Shadow ganhou os campos slopeBias e pcf.
"""
from OpenGL.GL import *


class Uniform(object):

    LIGHT_FIELDS = ("lightType", "color", "direction", "position", "attenuation")
    SHADOW_FIELDS = ("lightDirection", "projectionMatrix", "viewMatrix", "depthTexture",
                     "strength", "bias", "slopeBias", "pcf")
    SHADOW_TEXTURE_UNIT = 15       # unidade reservada ao mapa de profundidade

    def __init__(self, dataType, data):
        self.dataType = dataType
        self.data = data
        self.variableRef = None

    def locateVariable(self, programRef, variableName):
        if self.dataType == "Light":
            self.variableRef = {f: glGetUniformLocation(programRef, variableName + "." + f)
                                for f in Uniform.LIGHT_FIELDS}
        elif self.dataType == "Shadow":
            self.variableRef = {f: glGetUniformLocation(programRef, variableName + "." + f)
                                for f in Uniform.SHADOW_FIELDS}
        else:
            self.variableRef = glGetUniformLocation(programRef, variableName)

    def uploadData(self):
        ref = self.variableRef
        if not isinstance(ref, dict) and ref == -1:
            return                       # variável ausente/otimizada no shader
        t = self.dataType
        d = self.data
        if t == "int" or t == "bool":
            glUniform1i(ref, int(d))
        elif t == "float":
            glUniform1f(ref, d)
        elif t == "vec2":
            glUniform2f(ref, d[0], d[1])
        elif t == "vec3":
            glUniform3f(ref, d[0], d[1], d[2])
        elif t == "vec4":
            glUniform4f(ref, d[0], d[1], d[2], d[3])
        elif t == "mat4":
            glUniformMatrix4fv(ref, 1, GL_TRUE, d)
        elif t == "sampler2D":
            textureObjectRef, textureUnitRef = d
            glActiveTexture(GL_TEXTURE0 + textureUnitRef)
            glBindTexture(GL_TEXTURE_2D, textureObjectRef)
            glUniform1i(ref, textureUnitRef)
        elif t == "Light":
            light = d
            glUniform1i(ref["lightType"], light.lightType)
            glUniform3f(ref["color"], light.color[0], light.color[1], light.color[2])
            direction = light.getWorldDirection()
            glUniform3f(ref["direction"], direction[0], direction[1], direction[2])
            position = light.getWorldPosition()
            glUniform3f(ref["position"], position[0], position[1], position[2])
            glUniform3f(ref["attenuation"], light.attenuation[0], light.attenuation[1],
                        light.attenuation[2])
        elif t == "Shadow":
            sh = d
            direction = sh.lightSource.getWorldDirection()
            glUniform3f(ref["lightDirection"], direction[0], direction[1], direction[2])
            glUniformMatrix4fv(ref["projectionMatrix"], 1, GL_TRUE, sh.camera.projectionMatrix)
            glUniformMatrix4fv(ref["viewMatrix"], 1, GL_TRUE, sh.camera.viewMatrix)
            unit = Uniform.SHADOW_TEXTURE_UNIT
            glActiveTexture(GL_TEXTURE0 + unit)
            glBindTexture(GL_TEXTURE_2D, sh.renderTarget.texture.textureRef)
            glUniform1i(ref["depthTexture"], unit)
            glUniform1f(ref["strength"], sh.strength)
            glUniform1f(ref["bias"], sh.bias)
            glUniform1f(ref["slopeBias"], sh.slopeBias)
            glUniform1i(ref["pcf"], int(sh.pcf))
        else:
            raise Exception("Uniform com tipo desconhecido: " + str(t))
