from material.litMaterial import LitMaterial


class LambertMaterial(LitMaterial):
    """Iluminação ambiente + difusa."""
    def __init__(self, texture=None, properties=None, useShadow=False):
        super().__init__(texture, properties, useShadow, specular=False)
