from light.light import Light


class DirectionalLight(Light):
    """Luz direcional: raios paralelos (direção = eixo -z local do objeto).
    Defina a direção ANTES de posicionar a luz (setDirection usa lookAt)."""
    def __init__(self, color=(1, 1, 1), direction=(0, -1, 0)):
        super().__init__(Light.DIRECTIONAL)
        self.color = list(color)
        self.setDirection(direction)
