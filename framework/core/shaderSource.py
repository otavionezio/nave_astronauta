"""
Leitura de código GLSL de arquivos (shaders/*.vert, *.frag, *.glsl) — sem depender do OpenGL.

  * `#include "arquivo"` é substituído pelo conteúdo do arquivo (reuso: struct Light, struct Shadow);
  * `defines=[...]` vira linhas `#define X` no topo (ex.: USE_SPECULAR liga o termo especular).
O '#version 330' é acrescentado depois, por OpenGLUtils.initializeShader.
"""
import os

SHADER_DIRECTORY = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "shaders"))


def loadShader(fileName, defines=(), directory=None):
    directory = directory or SHADER_DIRECTORY

    def read(name, depth=0):
        if depth > 8:
            raise Exception("#include recursivo demais em " + name)
        path = os.path.join(directory, name)
        if not os.path.isfile(path):
            raise Exception("Arquivo de shader não encontrado: " + path)
        out = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("#include"):
                    out.append(read(stripped.split('"')[1], depth + 1))
                else:
                    out.append(line)
        return "".join(out)

    return "".join("#define " + d + "\n" for d in defines) + read(fileName)
