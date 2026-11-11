"""Cria um contexto OpenGL 3.3 core (Mesa/llvmpipe) com pbuffer via EGL."""
import ctypes
from ctypes import c_int, c_uint, c_void_p
from OpenGL._egl import egl, proc

_state = {}


def create(width=640, height=360):
    getPlat = ctypes.CFUNCTYPE(c_void_p, c_uint, c_void_p, c_void_p)(
        egl.eglGetProcAddress(b"eglGetPlatformDisplayEXT"))
    dpy = c_void_p(getPlat(0x31DD, None, None))          # EGL_PLATFORM_SURFACELESS_MESA
    egl.eglCreatePbufferSurface.restype = c_void_p
    egl.eglCreateContext.restype = c_void_p
    for n in ("eglInitialize", "eglChooseConfig", "eglCreatePbufferSurface", "eglBindAPI",
              "eglCreateContext", "eglMakeCurrent", "eglGetError"):
        getattr(egl, n).argtypes = None
    maj, mn = c_int(), c_int()
    if not egl.eglInitialize(dpy, ctypes.byref(maj), ctypes.byref(mn)):
        raise RuntimeError("eglInitialize falhou")
    cfg_attr = (c_int * 13)(0x3040, 0x0008, 0x3033, 0x0001, 0x3024, 8, 0x3023, 8, 0x3022, 8,
                            0x3025, 24, 0x3038)
    cfg, n = c_void_p(), c_int()
    egl.eglChooseConfig(dpy, cfg_attr, ctypes.byref(cfg), 1, ctypes.byref(n))
    surf = c_void_p(egl.eglCreatePbufferSurface(
        dpy, cfg, (c_int * 5)(0x3057, width, 0x3056, height, 0x3038)))
    egl.eglBindAPI(0x30A2)
    ctx_attr = (c_int * 9)(0x3098, 3, 0x30FB, 3, 0x30FD, 1, 0x3038, 0, 0)
    ctx = c_void_p(egl.eglCreateContext(dpy, cfg, None, ctx_attr))
    if not ctx.value or not egl.eglMakeCurrent(dpy, surf, surf, ctx):
        raise RuntimeError("não foi possível criar o contexto OpenGL (EGL erro %#x)" % egl.eglGetError())
    _state.update(dpy=dpy, surf=surf, ctx=ctx, size=(width, height))
    return (width, height)
