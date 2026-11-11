from light.light import Light


class AmbientLight(Light):
    """Luz ambiente: contribuição constante (aproxima a luz indireta)."""
    def __init__(self, color=(1, 1, 1)):
        super().__init__(Light.AMBIENT)
        self.color = list(color)
