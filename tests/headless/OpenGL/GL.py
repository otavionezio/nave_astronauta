"""Subconjunto de OpenGL.GL (PyOpenGL) implementado com ctypes. Ver ../README.md."""
import ctypes
from ctypes import (c_int, c_uint, c_float, c_void_p, c_char_p, c_ubyte, c_ssize_t,
                    POINTER, byref)
import numpy as np
from OpenGL._egl import proc

# ----------------------------- constantes -----------------------------
GL_NO_ERROR = 0
GL_FALSE, GL_TRUE = 0, 1
GL_VERTEX_SHADER, GL_FRAGMENT_SHADER = 0x8B31, 0x8B30
GL_COMPILE_STATUS, GL_LINK_STATUS, GL_INFO_LOG_LENGTH = 0x8B81, 0x8B82, 0x8B84
GL_VENDOR, GL_RENDERER, GL_VERSION, GL_SHADING_LANGUAGE_VERSION = 0x1F00, 0x1F01, 0x1F02, 0x8B8C
GL_ARRAY_BUFFER, GL_STATIC_DRAW = 0x8892, 0x88E4
GL_FLOAT, GL_INT, GL_UNSIGNED_BYTE = 0x1406, 0x1404, 0x1401
GL_POINTS, GL_LINES, GL_LINE_LOOP, GL_LINE_STRIP, GL_TRIANGLES = 0, 1, 2, 3, 4
GL_DEPTH_TEST, GL_MULTISAMPLE, GL_BLEND, GL_CULL_FACE = 0x0B71, 0x809D, 0x0BE2, 0x0B44
GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA = 0x0302, 0x0303
GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT = 0x4000, 0x0100
GL_FRONT_AND_BACK, GL_LINE, GL_FILL = 0x0408, 0x1B01, 0x1B02
GL_TEXTURE_2D, GL_TEXTURE0 = 0x0DE1, 0x84C0
GL_RGBA, GL_RED, GL_R32F = 0x1908, 0x1903, 0x822E
GL_TEXTURE_MAG_FILTER, GL_TEXTURE_MIN_FILTER = 0x2800, 0x2801
GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T, GL_TEXTURE_BORDER_COLOR = 0x2802, 0x2803, 0x1004
GL_NEAREST, GL_LINEAR = 0x2600, 0x2601
GL_NEAREST_MIPMAP_NEAREST, GL_LINEAR_MIPMAP_NEAREST = 0x2700, 0x2701
GL_NEAREST_MIPMAP_LINEAR, GL_LINEAR_MIPMAP_LINEAR = 0x2702, 0x2703
GL_REPEAT, GL_CLAMP_TO_EDGE, GL_CLAMP_TO_BORDER = 0x2901, 0x812F, 0x812D
GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_DEPTH_ATTACHMENT = 0x8D40, 0x8CE0, 0x8D00
GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, GL_FRAMEBUFFER_COMPLETE = 0x8D41, 0x81A6, 0x8CD5
GL_UNPACK_ALIGNMENT, GL_PACK_ALIGNMENT = 0x0CF5, 0x0D05

_U, _I, _F, _V, _S = c_uint, c_int, c_float, c_void_p, c_char_p


def _simple(name, restype, *argtypes):
    def call(*args):
        return proc(name, restype, argtypes)(*args)
    call.__name__ = name
    return call


glEnable = _simple("glEnable", None, _U)
glDisable = _simple("glDisable", None, _U)
glBlendFunc = _simple("glBlendFunc", None, _U, _U)
glClearColor = _simple("glClearColor", None, _F, _F, _F, _F)
glClear = _simple("glClear", None, _U)
glViewport = _simple("glViewport", None, _I, _I, _I, _I)
glPolygonMode = _simple("glPolygonMode", None, _U, _U)
glLineWidth = _simple("glLineWidth", None, _F)
glPointSize = _simple("glPointSize", None, _F)
glDrawArrays = _simple("glDrawArrays", None, _U, _I, _I)
glUseProgram = _simple("glUseProgram", None, _U)
glBindVertexArray = _simple("glBindVertexArray", None, _U)
glBindBuffer = _simple("glBindBuffer", None, _U, _U)
glEnableVertexAttribArray = _simple("glEnableVertexAttribArray", None, _U)
glCreateShader = _simple("glCreateShader", _U, _U)
glCompileShader = _simple("glCompileShader", None, _U)
glDeleteShader = _simple("glDeleteShader", None, _U)
glCreateProgram = _simple("glCreateProgram", _U)
glAttachShader = _simple("glAttachShader", None, _U, _U)
glLinkProgram = _simple("glLinkProgram", None, _U)
glDeleteProgram = _simple("glDeleteProgram", None, _U)
glActiveTexture = _simple("glActiveTexture", None, _U)
glBindTexture = _simple("glBindTexture", None, _U, _U)
glGenerateMipmap = _simple("glGenerateMipmap", None, _U)
glTexParameteri = _simple("glTexParameteri", None, _U, _U, _I)
glPixelStorei = _simple("glPixelStorei", None, _U, _I)
glBindFramebuffer = _simple("glBindFramebuffer", None, _U, _U)
glBindRenderbuffer = _simple("glBindRenderbuffer", None, _U, _U)
glRenderbufferStorage = _simple("glRenderbufferStorage", None, _U, _U, _I, _I)
glFramebufferRenderbuffer = _simple("glFramebufferRenderbuffer", None, _U, _U, _U, _U)
glFramebufferTexture = _simple("glFramebufferTexture", None, _U, _U, _U, _I)
glCheckFramebufferStatus = _simple("glCheckFramebufferStatus", _U, _U)
glGetError = _simple("glGetError", _U)
glFinish = _simple("glFinish", None)
glUniform1i = _simple("glUniform1i", None, _I, _I)
glUniform1f = _simple("glUniform1f", None, _I, _F)
glUniform2f = _simple("glUniform2f", None, _I, _F, _F)
glUniform3f = _simple("glUniform3f", None, _I, _F, _F, _F)
glUniform4f = _simple("glUniform4f", None, _I, _F, _F, _F, _F)


def _gen(name):
    fn = _simple(name, None, _I, POINTER(_U))

    def gen(n):
        ids = (_U * n)()
        fn(n, ids)
        return ids[0] if n == 1 else list(ids)
    return gen


glGenBuffers = _gen("glGenBuffers")
glGenTextures = _gen("glGenTextures")
glGenVertexArrays = _gen("glGenVertexArrays")
glGenFramebuffers = _gen("glGenFramebuffers")
glGenRenderbuffers = _gen("glGenRenderbuffers")


def glGetString(name):
    return proc("glGetString", c_char_p, (_U,))(name)


def glShaderSource(shader, source):
    arr = (c_char_p * 1)(source.encode("utf-8"))
    proc("glShaderSource", None, (_U, _I, POINTER(c_char_p), POINTER(_I)))(shader, 1, arr, None)


def glGetShaderiv(shader, pname):
    v = _I()
    proc("glGetShaderiv", None, (_U, _U, POINTER(_I)))(shader, pname, byref(v))
    return v.value


def glGetProgramiv(program, pname):
    v = _I()
    proc("glGetProgramiv", None, (_U, _U, POINTER(_I)))(program, pname, byref(v))
    return v.value


def glGetShaderInfoLog(shader):
    n = glGetShaderiv(shader, GL_INFO_LOG_LENGTH)
    buf = ctypes.create_string_buffer(max(n, 1))
    proc("glGetShaderInfoLog", None, (_U, _I, POINTER(_I), c_char_p))(shader, n, None, buf)
    return buf.value


def glGetProgramInfoLog(program):
    n = glGetProgramiv(program, GL_INFO_LOG_LENGTH)
    buf = ctypes.create_string_buffer(max(n, 1))
    proc("glGetProgramInfoLog", None, (_U, _I, POINTER(_I), c_char_p))(program, n, None, buf)
    return buf.value


def glGetAttribLocation(program, name):
    return proc("glGetAttribLocation", _I, (_U, c_char_p))(program, name.encode())


def glGetUniformLocation(program, name):
    return proc("glGetUniformLocation", _I, (_U, c_char_p))(program, name.encode())


def glBufferData(target, data, usage):
    data = np.ascontiguousarray(data)
    proc("glBufferData", None, (_U, c_ssize_t, c_void_p, _U))(target, data.nbytes, data.ctypes.data, usage)


def glVertexAttribPointer(index, size, type_, normalized, stride, pointer):
    proc("glVertexAttribPointer", None, (_U, _I, _U, ctypes.c_ubyte, _I, c_void_p))(
        index, size, type_, 1 if normalized else 0, stride, pointer)


def glUniformMatrix4fv(location, count, transpose, value):
    arr = np.ascontiguousarray(value, dtype=np.float32)
    proc("glUniformMatrix4fv", None, (_I, _I, ctypes.c_ubyte, POINTER(_F)))(
        location, count, 1 if transpose else 0, arr.ctypes.data_as(POINTER(_F)))


def glTexImage2D(target, level, internalformat, width, height, border, format_, type_, pixels):
    if pixels is None:
        ptr = None
    elif isinstance(pixels, (bytes, bytearray)):
        ptr = ctypes.c_char_p(bytes(pixels))
    else:
        pixels = np.ascontiguousarray(pixels)
        ptr = c_void_p(pixels.ctypes.data)
    proc("glTexImage2D", None, (_U, _I, _I, _I, _I, _I, _U, _U, c_void_p))(
        target, level, internalformat, width, height, border, format_, type_,
        ctypes.cast(ptr, c_void_p) if ptr is not None else None)


def glTexParameterfv(target, pname, params):
    arr = (_F * len(params))(*params)
    proc("glTexParameterfv", None, (_U, _U, POINTER(_F)))(target, pname, arr)


def glReadPixels(x, y, width, height, format_, type_):
    buf = ctypes.create_string_buffer(width * height * 4)
    proc("glReadPixels", None, (_I, _I, _I, _I, _U, _U, c_void_p))(
        x, y, width, height, format_, type_, ctypes.cast(buf, c_void_p))
    return buf.raw
