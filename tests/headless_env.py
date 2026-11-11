"""
Prepara o ambiente de testes gráficos.

  * Se `pygame` e `OpenGL` (PyOpenGL) reais estiverem instalados E a variável FORCE_HEADLESS_SHIM
    não estiver definida, usa-os (é preciso haver janela/contexto: ver tests/PLANO_DE_TESTES).
  * Caso contrário, usa a camada de teste de tests/headless (ctypes + Mesa/EGL, Linux).
Devolve True se está usando as bibliotecas reais.
"""
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
HEADLESS_DIR = os.path.join(ROOT, "tests", "headless")


def setup(width=1280, height=720):
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    import bootstrap  # noqa: F401

    real = False
    if not os.environ.get("FORCE_HEADLESS_SHIM"):
        try:
            import pygame  # noqa: F401
            import OpenGL.GL  # noqa: F401
            real = True
        except ImportError:
            real = False
    if not real:
        already = getattr(sys.modules.get("OpenGL"), "__file__", "") or ""
        if not already.startswith(HEADLESS_DIR):          # só descarta módulos que não são a camada de teste
            for m in [m for m in sys.modules if m == "pygame" or m == "OpenGL" or m.startswith("OpenGL.")]:
                del sys.modules[m]
        if HEADLESS_DIR not in sys.path:
            sys.path.insert(0, HEADLESS_DIR)
        import glcontext
        glcontext.create(width, height)
    else:
        import pygame
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.set_mode((width, height), pygame.DOUBLEBUF | pygame.OPENGL)
    return real


class FakeInput(object):
    """Entrada simulada: keys = teclas 'pressionadas'; down = teclas 'recém-pressionadas'."""
    def __init__(self, pressed=(), down=()):
        self.pressed, self.down = set(pressed), set(down)
        self.mouseDelta, self.mouseWheel = (0, 0), 0

    def isKeyDown(self, k): return k in self.down
    def isKeyPressed(self, k): return k in self.pressed
    def isMousePressed(self, b=1): return False


def readFramebuffer(width, height):
    """Lê o framebuffer padrão e devolve uma imagem PIL (RGB, origem no topo)."""
    from OpenGL.GL import glReadPixels, glFinish, GL_RGBA, GL_UNSIGNED_BYTE, glBindFramebuffer, GL_FRAMEBUFFER
    from PIL import Image
    glBindFramebuffer(GL_FRAMEBUFFER, 0)
    glFinish()
    data = glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE)
    if not isinstance(data, (bytes, bytearray)):
        data = bytes(data)
    return Image.frombytes("RGBA", (width, height), data).transpose(Image.FLIP_TOP_BOTTOM).convert("RGB")
