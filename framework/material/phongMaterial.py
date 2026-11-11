from material.litMaterial import LitMaterial


class PhongMaterial(LitMaterial):
    """Iluminação ambiente + difusa + especular."""
    def __init__(self, texture=None, properties=None, useShadow=False):
        super().__init__(texture, properties, useShadow, specular=True)
