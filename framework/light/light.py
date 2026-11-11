"""Luzes (STEMKOSKI & PASCALE, 2022, seção 6.2). Posição/direção vêm da matriz de transformação."""
from core.object3D import Object3D


class Light(Object3D):
    AMBIENT = 1
    DIRECTIONAL = 2
    POINT = 3

    def __init__(self, lightType=0):
        super().__init__()
        self.lightType = lightType
        self.color = [1, 1, 1]
        self.attenuation = [1, 0, 0]
