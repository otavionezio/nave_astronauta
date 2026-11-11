"""Carrega libEGL (Mesa) e resolve funções OpenGL por eglGetProcAddress."""
import ctypes
import os

os.environ.setdefault("EGL_PLATFORM", "surfaceless")
egl = ctypes.CDLL("libEGL.so.1")
egl.eglGetProcAddress.restype = ctypes.c_void_p
egl.eglGetProcAddress.argtypes = [ctypes.c_char_p]

_cache = {}


def proc(name, restype, argtypes):
    key = name
    if key not in _cache:
        addr = egl.eglGetProcAddress(name.encode())
        if not addr:
            raise RuntimeError("Função OpenGL indisponível: " + name)
        _cache[key] = ctypes.CFUNCTYPE(restype, *argtypes)(addr)
    return _cache[key]
