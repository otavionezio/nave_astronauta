"""
Máquina de estados e linha do tempo da interação NAVE x ASTRONAUTA.

IDEIA CENTRAL
  Cada pose (posição, ângulos das juntas, potência dos motores...) é uma FUNÇÃO PURA de
  (estado atual, tempo decorrido dentro do estado, tempo total).  O estado avança por
  `dt` (delta time, em segundos) e NUNCA por "quadros":

        stateTime += dt          # e não: stateTime += 1

  Por isso a animação dura o mesmo tempo real a 15, 60 ou 240 FPS.  Se `dt` cruza o fim
  de um estado, o tempo que sobra é transferido ao estado seguinte (sem perder precisão).
  Pausar = chamar update(0): o estado e as poses permanecem exatamente como estavam.

ESTADOS (cada transição depende do PROGRESSO do estado atual)
  APROXIMACAO          a nave voa até o ponto de inspeção, freando (ease-out) e curvando;
  ESTABILIZACAO        a nave paira, gira (yaw) para encarar o astronauta e reduz os motores;
  REACAO_DO_ASTRONAUTA o astronauta percebe a nave (cabeça acompanha), gira o corpo e
                       CAMINHA até a marca de inspeção;
  SINALIZACAO          já na marca, ergue o braço esquerdo e acena;
  RESPOSTA_DA_NAVE     SÓ DEPOIS do aceno a nave responde: 3 pulsos dos motores,
                       balizas piscando e leve cabeceio;
  RETOMADA             1) o astronauta baixa o braço; 2) SÓ QUANDO o braço chegou ao
                       repouso (armRaise == 0) a nave volta a se deslocar e parte;
  CONCLUIDO            a nave sai de cena; o astronauta volta a olhar à frente.
"""
import math
from dataclasses import dataclass
from enum import Enum


class State(Enum):
    APROXIMACAO = 1
    ESTABILIZACAO = 2
    REACAO_DO_ASTRONAUTA = 3
    SINALIZACAO = 4
    RESPOSTA_DA_NAVE = 5
    RETOMADA = 6
    CONCLUIDO = 7


ORDER = [State.APROXIMACAO, State.ESTABILIZACAO, State.REACAO_DO_ASTRONAUTA, State.SINALIZACAO,
         State.RESPOSTA_DA_NAVE, State.RETOMADA, State.CONCLUIDO]

# duração (s) de cada estado; RETOMADA = baixar o braço + partida da nave
ARM_LOWER_TIME = 1.0
DEPARTURE_TIME = 6.5
DURATION = {
    State.APROXIMACAO: 7.0,
    State.ESTABILIZACAO: 2.6,
    State.REACAO_DO_ASTRONAUTA: 5.4,
    State.SINALIZACAO: 3.8,
    State.RESPOSTA_DA_NAVE: 3.6,
    State.RETOMADA: ARM_LOWER_TIME + DEPARTURE_TIME,
}
LOOP_DELAY = 4.0            # no modo --loop, espera após CONCLUIDO antes de reiniciar

LABEL = {
    State.APROXIMACAO: "1/6  APROXIMACAO - a nave entra na area de inspecao",
    State.ESTABILIZACAO: "2/6  ESTABILIZACAO - a nave freia e gira para encarar o astronauta",
    State.REACAO_DO_ASTRONAUTA: "3/6  REACAO - o astronauta percebe a nave e caminha ate a marca",
    State.SINALIZACAO: "4/6  SINALIZACAO - o astronauta ergue o braco e acena",
    State.RESPOSTA_DA_NAVE: "5/6  RESPOSTA DA NAVE - pulsos dos motores e balizas",
    State.RETOMADA: "6/6  RETOMADA - braco baixa; so entao a nave parte",
    State.CONCLUIDO: "CONCLUIDO - pressione R para reiniciar",
}

# ------------------------- geometria do cenário (metros) -------------------------
ASTRONAUT_START = (0.0, 0.0)             # (x, z)
ASTRONAUT_START_YAW = math.pi            # olhando para +z (para a câmera inicial)
MARK = (-1.6, 2.4)                       # marca de inspeção no piso
EYE_HEIGHT = 2.0
HOLD = (-18.0, 8.0, 6.0)                 # onde a nave paira durante a interação
SHIP_PITCH_FACE = -0.16                  # leve inclinação do nariz para baixo (olhando o astronauta)
APPROACH_PATH = [(-80.0, 22.0, -60.0), (-52.0, 17.0, -42.0), (-22.0, 10.5, -16.0), HOLD]
DEPARTURE_PATH = [HOLD, (HOLD[0] + 6.0, HOLD[1] + 1.0, HOLD[2] - 12.0), (30.0, 12.0, -32.0),
                  (75.0, 22.0, -42.0)]
STRIDE = 1.5                             # comprimento de um ciclo completo de passada (m)


# ------------------------------- funções auxiliares -------------------------------
def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(x):
    x = clamp(x)
    return x * x * (3.0 - 2.0 * x)


def ease_out_cubic(x):
    return 1.0 - (1.0 - clamp(x)) ** 3          # começa rápido, termina com velocidade 0


def ease_in_cubic(x):
    return clamp(x) ** 3                         # começa com velocidade 0, acelera


def wrap_angle(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def angle_lerp(a, b, t):
    return a + wrap_angle(b - a) * t             # interpola pelo caminho mais curto


def yaw_to(sx, sz, dx, dz):
    """Yaw (rotação em y) para que a "frente" (-z) de um objeto em (sx, sz) aponte para (dx, dz).
    Com Ry(yaw), a frente vira (-sen yaw, 0, -cos yaw); logo yaw = atan2(-(dx-sx), -(dz-sz))."""
    return math.atan2(-(dx - sx), -(dz - sz))


def bezier(path, u):
    p0, p1, p2, p3 = path
    a, b, c, d = (1 - u) ** 3, 3 * (1 - u) ** 2 * u, 3 * (1 - u) * u ** 2, u ** 3
    return tuple(a * p0[i] + b * p1[i] + c * p2[i] + d * p3[i] for i in range(3))


def bezier_tangent(path, u):
    p0, p1, p2, p3 = path
    a, b, c = 3 * (1 - u) ** 2, 6 * (1 - u) * u, 3 * u ** 2
    return tuple(a * (p1[i] - p0[i]) + b * (p2[i] - p1[i]) + c * (p3[i] - p2[i]) for i in range(3))


def heading(path, u):
    """(yaw, pitch) de um objeto que voa ao longo da curva no parâmetro u."""
    vx, vy, vz = bezier_tangent(path, clamp(u))
    return math.atan2(-vx, -vz), math.atan2(vy, math.hypot(vx, vz))


YAW_FACE = yaw_to(HOLD[0], HOLD[2], MARK[0], MARK[1])                 # nave encara a marca
YAW_WALK = math.atan2(-(MARK[0] - ASTRONAUT_START[0]), -(MARK[1] - ASTRONAUT_START[1]))
YAW_SHIP = yaw_to(MARK[0], MARK[1], HOLD[0], HOLD[2])                  # astronauta encara a nave
WALK_DISTANCE = math.hypot(MARK[0] - ASTRONAUT_START[0], MARK[1] - ASTRONAUT_START[1])


# --------------------------------- poses ---------------------------------
@dataclass
class ShipPose:
    position: tuple = (0.0, 0.0, 0.0)
    yaw: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    enginePower: float = 0.0       # 0 (apagado) .. 1 (máximo): chama, brilho e luz dos motores
    beaconOn: bool = False
    visible: bool = True
    departureEnabled: bool = False


@dataclass
class AstronautPose:
    x: float = 0.0
    z: float = 0.0
    bob: float = 0.0               # deslocamento vertical (respiração / passada)
    yaw: float = 0.0
    torsoYaw: float = 0.0
    headYaw: float = 0.0           # em relação ao tronco
    headPitch: float = 0.0         # > 0 olha para cima
    lHip: float = 0.0              # > 0 balança a perna para a frente
    rHip: float = 0.0
    lKnee: float = 0.0             # flexão (>= 0)
    rKnee: float = 0.0
    lShoulderPitch: float = 0.0    # > 0 braço para a frente
    lShoulderRoll: float = 0.0     # > 0 afasta o braço do corpo (lateral); ~2.5 = braço para cima
    lElbow: float = 0.0
    lWave: float = 0.0             # oscilação lateral do antebraço (aceno)
    rShoulderPitch: float = 0.0
    rShoulderRoll: float = 0.0
    rElbow: float = 0.0
    armRaise: float = 0.0          # 0 = braço em repouso .. 1 = erguido (usado na condição de partida)
    walking: bool = False
    speed: float = 0.0
    waveCycles: float = 0.0        # acenos já completados (progresso)


# ----------------------------- diretor da interação -----------------------------
class InteractionDirector(object):

    def __init__(self, loop=False):
        self.loop = loop
        self.reset()

    def reset(self):
        self.state = State.APROXIMACAO
        self.stateTime = 0.0
        self.totalTime = 0.0                  # tempo simulado (não avança durante a pausa)
        self.history = [(State.APROXIMACAO, 0.0)]   # (estado, instante em que começou)
        self.departureStartedAt = None        # instante em que a nave voltou a se mover
        self._refresh()

    # ---------- avanço do tempo ----------
    def duration(self, state=None):
        return DURATION.get(state or self.state, float("inf"))

    @property
    def progress(self):
        d = self.duration()
        return 0.0 if d == float("inf") else clamp(self.stateTime / d)

    def update(self, dt):
        """Avança a simulação em `dt` segundos (dt = 0 => pausado)."""
        if dt <= 0.0:
            return
        t = dt
        while True:
            if self.state is State.CONCLUIDO:
                self.stateTime += t
                self.totalTime += t
                break
            remaining = self.duration() - self.stateTime
            if t < remaining:
                self.stateTime += t
                self.totalTime += t
                break
            # o estado termina dentro deste quadro: o tempo que sobra vai para o próximo
            t -= remaining
            self.totalTime += remaining
            self.state = ORDER[ORDER.index(self.state) + 1]
            self.stateTime = 0.0
            self.history.append((self.state, self.totalTime))
        if self.state is State.CONCLUIDO and self.loop and self.stateTime >= LOOP_DELAY:
            self.reset()
            return
        self._refresh()

    # ---------- poses ----------
    def _refresh(self):
        self.shipPose = self._computeShip()
        self.astronautPose = self._computeAstronaut()
        # condição explícita: a nave só parte depois que o braço chegou ao repouso
        if (self.state is State.RETOMADA and self.shipPose.departureEnabled
                and self.departureStartedAt is None):
            self.departureStartedAt = self.totalTime - (self.stateTime - ARM_LOWER_TIME)

    def _hover(self, amplitude):
        return 0.12 * math.sin(2 * math.pi * self.totalTime / 3.4) * amplitude

    def _flightAttitude(self, path, easing, q, span):
        """(yaw, pitch, roll) ao longo de uma curva; roll = inclinação nas curvas (proporcional
        à taxa de variação do yaw, calculada por diferença finita no tempo)."""
        yaw, pitch = heading(path, easing(q))
        e = 0.02
        q0, q1 = clamp(q - e), clamp(q + e)
        y0, _ = heading(path, easing(q0))
        y1, _ = heading(path, easing(q1))
        rate = wrap_angle(y1 - y0) / max((q1 - q0) * span, 1e-6)
        return yaw, clamp(0.5 * pitch, -0.25, 0.25), clamp(0.9 * rate, -0.30, 0.30)

    def _computeShip(self):
        s, ts = self.state, self.stateTime
        P = ShipPose()
        if s is State.APROXIMACAO:
            d = DURATION[s]
            q = ts / d
            P.position = bezier(APPROACH_PATH, ease_out_cubic(q))     # decelera até parar
            P.yaw, P.pitch, P.roll = self._flightAttitude(APPROACH_PATH, ease_out_cubic, q, d)
            P.enginePower = 0.45 + 0.55 * (1.0 - clamp(q))
            return P

        hold = HOLD
        face = (YAW_FACE, SHIP_PITCH_FACE)
        if s is State.ESTABILIZACAO:
            d = DURATION[s]
            p = clamp(ts / d)
            e = smoothstep(p)
            yaw0, pitch0 = heading(APPROACH_PATH, 1.0)
            yawRate = 6 * p * (1 - p) * wrap_angle(face[0] - yaw0) / d      # derivada do smoothstep
            P.yaw = angle_lerp(yaw0, face[0], e)
            P.pitch = lerp(clamp(0.5 * pitch0, -0.25, 0.25), face[1], e)
            P.roll = clamp(0.25 * yawRate, -0.2, 0.2)
            P.position = (hold[0], hold[1] + self._hover(e), hold[2])
            P.enginePower = lerp(0.45, 0.30, e)
            return P

        if s in (State.REACAO_DO_ASTRONAUTA, State.SINALIZACAO):
            P.yaw, P.pitch = face
            P.position = (hold[0], hold[1] + self._hover(1.0), hold[2])
            P.enginePower = 0.30
            return P

        if s is State.RESPOSTA_DA_NAVE:
            p = clamp(ts / DURATION[s])
            pulse = 0.5 * (1.0 - math.cos(2 * math.pi * 3 * p))        # 3 pulsos suaves
            P.yaw = face[0]
            P.pitch = face[1] + 0.05 * math.sin(2 * math.pi * 2 * p)  # leve cabeceio
            P.position = (hold[0], hold[1] + self._hover(1.0), hold[2])
            P.enginePower = 0.30 + 0.70 * pulse
            P.beaconOn = int(p * 12) % 2 == 0
            return P

        if s is State.RETOMADA:
            if ts < ARM_LOWER_TIME:                    # espera o astronauta baixar o braço
                P.yaw, P.pitch = face
                P.position = (hold[0], hold[1] + self._hover(1.0), hold[2])
                P.enginePower = 0.30
                return P
            P.departureEnabled = True
            q = clamp((ts - ARM_LOWER_TIME) / DEPARTURE_TIME)
            u = ease_in_cubic(q)                       # parte devagar e acelera
            yawH, pitchH, roll = self._flightAttitude(DEPARTURE_PATH, ease_in_cubic, q, DEPARTURE_TIME)
            turn = smoothstep(q / 0.45)                # primeiro gira, depois acelera
            x, y, z = bezier(DEPARTURE_PATH, u)
            P.position = (x, y + self._hover(1.0 - smoothstep(q / 0.2)), z)
            P.yaw = angle_lerp(face[0], yawH, turn)
            P.pitch = lerp(face[1], pitchH, turn)
            P.roll = roll * turn
            P.enginePower = lerp(0.30, 1.0, smoothstep(q / 0.35))
            return P

        # CONCLUIDO: a nave já saiu de cena
        P.position = DEPARTURE_PATH[-1]
        P.visible = False
        P.enginePower = 0.0
        return P

    def _computeAstronaut(self):
        s, ts, T = self.state, self.stateTime, self.totalTime
        A = AstronautPose()
        x, z = ASTRONAUT_START
        yaw = ASTRONAUT_START_YAW
        walked = 0.0
        speed = 0.0

        # --- posição e orientação do corpo ---
        past = ORDER.index(s) > ORDER.index(State.REACAO_DO_ASTRONAUTA)
        if s is State.REACAO_DO_ASTRONAUTA:
            d = DURATION[s]
            p = clamp(ts / d)
            if p < 0.15:                                         # gira para a direção da caminhada
                yaw = angle_lerp(ASTRONAUT_START_YAW, YAW_WALK, smoothstep(p / 0.15))
            elif p < 0.85:
                yaw = YAW_WALK
            else:                                                # chega e gira para a nave
                yaw = angle_lerp(YAW_WALK, YAW_SHIP, smoothstep((p - 0.85) / 0.15))
            q = clamp((p - 0.15) / 0.70)
            e = smoothstep(q)
            x = lerp(ASTRONAUT_START[0], MARK[0], e)
            z = lerp(ASTRONAUT_START[1], MARK[1], e)
            walked = WALK_DISTANCE * e
            speed = WALK_DISTANCE * 6 * q * (1 - q) / (0.70 * d)
        elif past:
            x, z = MARK
            yaw = YAW_SHIP

        # --- passada: fase proporcional à DISTÂNCIA caminhada (os pés não "patinam") ---
        phi = 2 * math.pi * walked / STRIDE
        g = clamp(speed / 0.35)                                  # peso da animação de marcha
        A.walking = speed > 1e-3
        A.speed = speed
        A.lHip = 0.42 * g * math.sin(phi)
        A.rHip = -A.lHip
        A.lKnee = 0.75 * g * max(0.0, math.cos(phi))
        A.rKnee = 0.75 * g * max(0.0, -math.cos(phi))
        A.torsoYaw = 0.06 * g * math.sin(phi)
        swing = 0.30 * g * math.sin(phi)
        A.lShoulderPitch, A.rShoulderPitch = -swing, swing
        A.bob = 0.03 * g * abs(math.sin(phi)) + 0.008 * math.sin(2 * math.pi * 0.3 * T)
        A.x, A.z, A.yaw = x, z, yaw

        # --- braço esquerdo (prateado): aceno ---
        raise_ = 0.0
        wave = 0.0
        cycles = 0.0
        if s is State.SINALIZACAO:
            p = clamp(ts / DURATION[s])
            raise_ = smoothstep(p / 0.22)
            w = clamp((p - 0.22) / 0.68)
            cycles = 3.0 * w
            wave = 0.5 * math.sin(2 * math.pi * cycles) * smoothstep((p - 0.22) / 0.05)
        elif s is State.RESPOSTA_DA_NAVE:
            raise_ = 1.0
            cycles = 3.0
            wave = 0.06 * math.sin(2 * math.pi * 0.8 * T)
        elif s is State.RETOMADA:
            raise_ = 1.0 - smoothstep(ts / ARM_LOWER_TIME)       # chega exatamente a 0
            cycles = 3.0
        A.armRaise = raise_
        A.lShoulderRoll = 0.07 + raise_ * (2.55 - 0.07)
        A.lShoulderPitch = lerp(A.lShoulderPitch, 0.15, raise_)
        A.lElbow = 0.10 + 0.40 * raise_
        A.lWave = wave
        A.waveCycles = cycles
        A.rShoulderRoll = 0.07
        A.rElbow = 0.12

        # --- cabeça: acompanha a nave (percepção) ---
        ship = self.shipPose
        dx, dy, dz = ship.position[0] - x, ship.position[1] - EYE_HEIGHT, ship.position[2] - z
        horizontal = math.hypot(dx, dz)
        target = wrap_angle(math.atan2(-dx, -dz) - yaw)
        if s is State.APROXIMACAO:
            dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            awareness = smoothstep((60.0 - dist) / 28.0)         # percebe a nave ao se aproximar
        elif s is State.CONCLUIDO:
            awareness = 1.0 - smoothstep(ts / 1.5)
        else:
            awareness = 1.0
        scan = 0.35 * math.sin(0.6 * T)                          # olha em volta enquanto não percebeu
        A.headYaw = clamp(target, -1.1, 1.1) * awareness + (1.0 - awareness) * scan
        A.headPitch = clamp(math.atan2(dy, horizontal), -0.3, 0.6) * awareness
        return A

    # ---------- texto para a interface ----------
    def label(self):
        return LABEL[self.state]
