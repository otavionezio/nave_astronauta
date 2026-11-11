"""
Compilação/ligação de shaders.
Base: STEMKOSKI & PASCALE (2022), seção 2.2.2.

Adaptações:
  * loadShader(): lê o GLSL de arquivos em shaders/ (#include e defines: core/shaderSource.py);
  * os erros de compilação citam o nome do arquivo.
"""
from OpenGL.GL import *
from core.shaderSource import loadShader as loadShaderSource


class OpenGLUtils(object):

    @staticmethod
    def loadShader(fileName, defines=()):
        """Código GLSL de shaders/<fileName> com #include expandido (ver core/shaderSource.py)."""
        return loadShaderSource(fileName, defines)

    @staticmethod
    def initializeShader(shaderCode, shaderType, sourceName="<inline>"):
        # versão exigida de OpenGL/GLSL
        shaderCode = '#version 330\n' + shaderCode
        shaderRef = glCreateShader(shaderType)
        glShaderSource(shaderRef, shaderCode)
        glCompileShader(shaderRef)

        compileSuccess = glGetShaderiv(shaderRef, GL_COMPILE_STATUS)
        if not compileSuccess:
            errorMessage = glGetShaderInfoLog(shaderRef)
            glDeleteShader(shaderRef)
            if isinstance(errorMessage, bytes):
                errorMessage = errorMessage.decode('utf-8', errors='replace')
            raise Exception('\nErro de compilação do shader (' + sourceName + '):\n' + errorMessage)
        return shaderRef

    @staticmethod
    def initializeProgram(vertexShaderCode, fragmentShaderCode):
        vertexShaderRef = OpenGLUtils.initializeShader(vertexShaderCode, GL_VERTEX_SHADER, "vertex")
        fragmentShaderRef = OpenGLUtils.initializeShader(fragmentShaderCode, GL_FRAGMENT_SHADER, "fragment")

        programRef = glCreateProgram()
        glAttachShader(programRef, vertexShaderRef)
        glAttachShader(programRef, fragmentShaderRef)
        glLinkProgram(programRef)

        linkSuccess = glGetProgramiv(programRef, GL_LINK_STATUS)
        if not linkSuccess:
            errorMessage = glGetProgramInfoLog(programRef)
            glDeleteProgram(programRef)
            if isinstance(errorMessage, bytes):
                errorMessage = errorMessage.decode('utf-8', errors='replace')
            raise Exception('\nErro ao ligar o programa:\n' + errorMessage)

        # os objetos shader já estão embutidos no programa
        glDeleteShader(vertexShaderRef)
        glDeleteShader(fragmentShaderRef)
        return programRef

    @staticmethod
    def printSystemInfo():
        def s(name):
            v = glGetString(name)
            return v.decode('utf-8') if isinstance(v, bytes) else str(v)
        print(" Vendor: " + s(GL_VENDOR))
        print("Renderer: " + s(GL_RENDERER))
        print("OpenGL version supported: " + s(GL_VERSION))
        print(" GLSL version supported: " + s(GL_SHADING_LANGUAGE_VERSION))
