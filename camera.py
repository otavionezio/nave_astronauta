"""
Câmera em perspectiva com controle orbital pelo teclado/mouse.

A câmera fica sobre uma esfera de raio `distance` em torno de um ponto-alvo:

    posição = alvo + distance * (sen(az) cos(el),  sen(el),  cos(az) cos(el))
    orientação = look-at (core.matrix.Matrix.makeLookAt) da posição para o alvo

Controles ->  setas / arrastar o mouse: orbitar | W,S / - + / roda: aproximar, afastar
              A,D: deslocar o alvo lateralmente | Q,E: subir/descer o alvo
              1 geral, 2 segue o astronauta, 3 segue a nave, 4 livre

Limites: elevação 4°..86°, distância 3..90 m, alvo dentro do deck e acima do piso, e a
posição da câmera nunca fica abaixo do piso nem dentro da caixa da nave (pushOut).
Os movimentos usam o delta time REAL (a câmera continua respondendo com a animação pausada).
"""
import math
from core.camera import Camera
from core.matrix import Matrix

EL_MIN, EL_MAX = math.radians(4.0), math.radians(86.0)
DIST_MIN, DIST_MAX = 3.0, 90.0
FLOOR_MARGIN = 0.4

PRESETS = {
    "1": dict(mode="geral", az=24, el=17, dist=39, anchor=(-10.0, 4.5, 2.5)),
    "2": dict(mode="astronauta", az=35, el=12, dist=7.5, anchor=None),
    "3": dict(mode="nave", az=-50, el=14, dist=34, anchor=None),
    "4": dict(mode="livre", az=None, el=None, dist=None, anchor=None),
}


def _approach(current, desired, dt, rate=9.0):
    return current + (desired - current) * (1.0 - math.exp(-rate * dt))


class OrbitCamera(object):

    def __init__(self, aspectRatio=16 / 9):
        self.camera = Camera(angleOfView=50, aspectRatio=aspectRatio, near=0.1, far=1000)
        self.mode = "geral"
        p = PRESETS["1"]
        self.az, self.el, self.dist = math.radians(p["az"]), math.radians(p["el"]), p["dist"]
        self.azT, self.elT, self.distT = self.az, self.el, self.dist
        self.anchor = list(p["anchor"])
        self.pan = [0.0, 0.0, 0.0]
        self.target = list(self.anchor)
        self.obstacle = None                 # função (ponto, margem) -> ponto
        self.position = [0.0, 0.0, 0.0]
        self._rebuild()

    def setMode(self, key):
        p = PRESETS[key]
        self.mode = p["mode"]
        if p["az"] is not None:
            self.azT, self.elT, self.distT = math.radians(p["az"]), math.radians(p["el"]), p["dist"]
        if p["anchor"] is not None:
            self.anchor = list(p["anchor"])
        self.pan = [0.0, 0.0, 0.0]

    # --------------------------------------------------------------
    def update(self, dt, inp, follow):
        """follow: {"astronauta": (x,y,z), "nave": (x,y,z)} posições atuais (mundo)."""
        # --- atalhos de modo ---
        for key in PRESETS:
            if inp.isKeyDown(key):
                self.setMode(key)

        # --- orbitar ---
        turn = 1.4 * dt
        if inp.isKeyPressed("left"):
            self.azT -= turn
        if inp.isKeyPressed("right"):
            self.azT += turn
        if inp.isKeyPressed("up"):
            self.elT += turn
        if inp.isKeyPressed("down"):
            self.elT -= turn
        if inp.isMousePressed(1):
            self.azT -= inp.mouseDelta[0] * 0.006
            self.elT += inp.mouseDelta[1] * 0.006

        # --- zoom (exponencial: o mesmo gesto aproxima proporcionalmente) ---
        k = 1.0
        if inp.isKeyPressed("w") or inp.isKeyPressed("=") or inp.isKeyPressed("+"):
            k *= math.exp(-1.2 * dt)
        if inp.isKeyPressed("s") or inp.isKeyPressed("-"):
            k *= math.exp(1.2 * dt)
        if inp.mouseWheel:
            k *= math.exp(-0.12 * inp.mouseWheel)
        self.distT = min(max(self.distT * k, DIST_MIN), DIST_MAX)

        # --- deslocar o alvo ---
        speed = 9.0 * dt * max(self.dist / 30.0, 0.3)
        right = (math.cos(self.az), 0.0, -math.sin(self.az))
        if inp.isKeyPressed("a"):
            self.pan[0] -= right[0] * speed
            self.pan[2] -= right[2] * speed
        if inp.isKeyPressed("d"):
            self.pan[0] += right[0] * speed
            self.pan[2] += right[2] * speed
        if inp.isKeyPressed("q"):
            self.pan[1] -= speed
        if inp.isKeyPressed("e"):
            self.pan[1] += speed

        self.elT = min(max(self.elT, EL_MIN), EL_MAX)

        # --- ponto-alvo conforme o modo ---
        if self.mode == "astronauta" and "astronauta" in follow:
            ax, ay, az = follow["astronauta"]
            base = (ax, ay + 1.5, az)
        elif self.mode == "nave" and "nave" in follow:
            base = follow["nave"]
        else:
            base = tuple(self.anchor)
        desired = [base[0] + self.pan[0], base[1] + self.pan[1], base[2] + self.pan[2]]
        desired[0] = min(max(desired[0], -45.0), 45.0)
        desired[2] = min(max(desired[2], -45.0), 45.0)
        desired[1] = min(max(desired[1], 0.5), 25.0)

        # --- suavização temporal (independente da taxa de quadros) ---
        self.az = _approach(self.az, self.azT, dt)
        self.el = _approach(self.el, self.elT, dt)
        self.dist = _approach(self.dist, self.distT, dt)
        for i in range(3):
            self.target[i] = _approach(self.target[i], desired[i], dt, rate=12.0)
        self._rebuild()

    def _rebuild(self):
        el = min(max(self.el, EL_MIN), EL_MAX)
        d = min(max(self.dist, DIST_MIN), DIST_MAX)
        t = self.target
        pos = [t[0] + d * math.sin(self.az) * math.cos(el),
               t[1] + d * math.sin(el),
               t[2] + d * math.cos(self.az) * math.cos(el)]
        if self.obstacle is not None:
            pos = list(self.obstacle(pos, 1.0))
        pos[1] = max(pos[1], FLOOR_MARGIN)               # nunca abaixo do piso
        self.position = pos
        self.camera.transform = Matrix.makeLookAt(pos, t)
