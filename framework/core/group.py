from core.object3D import Object3D


class Group(Object3D):
    """Nó interior: serve para agrupar e transformar vários objetos como uma unidade
    (usado como 'junta' articulada nos modelos)."""
    def __init__(self):
        super().__init__()
