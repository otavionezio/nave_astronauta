#!/usr/bin/env python3
"""
Gera as texturas de imagem do projeto (PNG 512x512, repetíveis / "tileable").

  textures/painel_metalico.png : piso da plataforma (placas de aço com rebites e arranhões)
  textures/casco_cinza.png     : casco da nave (painéis cinza com ventilações e rebites)

ORIGEM: criadas algoritmicamente por este script (NumPy + Pillow), sem imagens de
terceiros. A semente fixa torna o resultado reprodutível.   Uso:  python tools/gerar_texturas.py

Como ficam repetíveis: o ruído é filtrado no domínio da frequência (FFT), o que o torna
periódico por construção; painéis, rebites e frisos usam coordenadas módulo o tamanho.
"""
import os
import numpy as np
from PIL import Image

SIZE = 512
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "textures")


def periodic_noise(rng, cutoffX, cutoffY):
    """Ruído periódico com suavização independente em x e y (cutoff menor = mais liso)."""
    f = np.fft.fft2(rng.standard_normal((SIZE, SIZE)))
    fy = np.fft.fftfreq(SIZE)[:, None]
    fx = np.fft.fftfreq(SIZE)[None, :]
    f *= np.exp(-((fx / cutoffX) ** 2 + (fy / cutoffY) ** 2))
    n = np.real(np.fft.ifft2(f))
    return (n - n.mean()) / n.std()


def wrapped_dist(a, center):
    d = np.abs(a - center)
    return np.minimum(d, SIZE - d)


def rivets(img, positions, radius=5):
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    for cx, cy in positions:
        dist = np.hypot(wrapped_dist(xx, cx), wrapped_dist(yy, cy))
        body = dist < radius
        img[body] *= 0.80 + 0.35 * np.clip(1 - dist[body] / radius, 0, 1)     # cúpula clara
        ring = (dist >= radius) & (dist < radius + 2)
        img[ring] *= 0.55                                                     # sombra ao redor
        hl = np.hypot(wrapped_dist(xx, cx - 1.5), wrapped_dist(yy, cy - 1.5)) < 1.6
        img[hl] *= 1.35


def make_floor():
    rng = np.random.default_rng(40_000)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    P = SIZE // 2                                  # 2 x 2 placas
    lx, ly = xx % P, yy % P
    edge = np.minimum(np.minimum(lx, ly), np.minimum(P - 1 - lx, P - 1 - ly))

    base = np.full((SIZE, SIZE), 0.30)
    # aço escovado (ruído esticado em x) + manchas largas + variação por placa
    base += 0.045 * periodic_noise(rng, 0.02, 0.35)
    base += 0.040 * periodic_noise(rng, 0.03, 0.03)
    plate_id = (yy // P) * 2 + (xx // P)
    base *= (1.0, 0.92, 1.06, 0.97)[0] * np.choose(plate_id, [1.0, 0.9, 1.07, 0.96])

    # juntas escuras e chanfro claro (luz vindo de cima/esquerda)
    base[edge < 3] *= 0.30
    bevel = (edge >= 3) & (edge < 7)
    base[bevel] *= 1.22
    inner = (edge >= 7) & (edge < 10)
    base[inner] *= 0.85

    # friso de segurança dourado nas placas inferiores
    stripe = ((ly > P - 30) & (ly < P - 18)) & (yy >= P)
    diag = ((lx + ly) // 14) % 2 == 0
    base_rgb = np.stack([base * 0.92, base * 0.97, base * 1.08], axis=-1)   # tom azulado
    haz = stripe & diag
    base_rgb[haz] = np.array([0.62, 0.46, 0.10])
    base_rgb[stripe & ~diag] = np.array([0.05, 0.05, 0.05])

    # rebites nos quatro cantos de cada placa
    pts = [(x * P + o, y * P + p) for x in range(2) for y in range(2)
           for o in (22, P - 23) for p in (22, P - 23)]
    for c in range(3):
        channel = base_rgb[:, :, c].copy()
        rivets(channel, pts)
        base_rgb[:, :, c] = channel

    # arranhões: riscas finas claras
    for _ in range(140):
        x0, y0 = rng.integers(0, SIZE, 2)
        length = rng.integers(12, 60)
        ang = rng.uniform(-0.3, 0.3)
        for t in range(length):
            x = int(x0 + t * np.cos(ang)) % SIZE
            y = int(y0 + t * np.sin(ang)) % SIZE
            base_rgb[y, x] = np.clip(base_rgb[y, x] * 1.5 + 0.03, 0, 1)
    return base_rgb


def make_hull():
    rng = np.random.default_rng(40_001)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    xs = [0, 150, 300, 410, 512]                   # colunas de painéis (períodos 512)
    ys = [0, 90, 220, 330, 512]
    base = np.full((SIZE, SIZE), 0.44)
    base += 0.03 * periodic_noise(rng, 0.03, 0.12)
    base += 0.03 * periodic_noise(rng, 0.04, 0.04)

    col = np.digitize(xx, xs[1:-1])
    row = np.digitize(yy, ys[1:-1])
    shade = rng.uniform(0.82, 1.12, size=(4, 4))
    base *= shade[row, col]

    # junta entre painéis + chanfro
    dx = np.minimum(wrapped_dist(xx, 0), 1e9)
    seam = np.zeros((SIZE, SIZE), bool)
    for b in xs[:-1]:
        seam |= wrapped_dist(xx, b) < 2
    for b in ys[:-1]:
        seam |= wrapped_dist(yy, b) < 2
    base[seam] *= 0.35
    for b in xs[:-1]:
        base[(wrapped_dist(xx, b + 4) < 2)] *= 1.18
    for b in ys[:-1]:
        base[(wrapped_dist(yy, b + 4) < 2)] *= 1.18

    # ventilações (fendas horizontais) em alguns painéis
    for (c, r) in [(1, 1), (3, 2), (0, 3)]:
        x0, x1, y0, y1 = xs[c] + 18, xs[c + 1] - 18, ys[r] + 18, ys[r + 1] - 18
        for k, y in enumerate(range(y0, y1, 9)):
            base[y:y + 3, x0:x1] *= 0.30
            base[y + 3:y + 4, x0:x1] *= 1.25

    rgb = np.stack([base * 0.97, base * 1.0, base * 1.06], axis=-1)

    # faixas escuras de desgaste (manchas verticais)
    streak = np.clip(periodic_noise(rng, 0.2, 0.01) * 0.05, -0.08, 0.08)
    rgb += streak[:, :, None]

    # fileira de rebites ao longo das juntas
    pts = []
    for b in xs[:-1]:
        pts += [(b + 9, y) for y in range(20, SIZE, 48)]
    for c in range(3):
        channel = rgb[:, :, c].copy()
        rivets(channel, pts, radius=3)
        rgb[:, :, c] = channel
    return rgb


def save(arr, name):
    img = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
    path = os.path.normpath(os.path.join(OUT, name))
    Image.fromarray(img, "RGB").save(path)
    print("gerado:", path, img.shape)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    save(make_floor(), "painel_metalico.png")
    save(make_hull(), "casco_cinza.png")
