#!/usr/bin/env python3
"""
Gera as capturas de tela de docs/img/ (renderização fora da janela, para a documentação).
Usa tests/headless_env: com Pygame+PyOpenGL instalados abre um contexto real; sem eles (Linux+Mesa),
usa a camada de teste. Uso:  python tools/gerar_capturas.py
"""
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "tests"))
import headless_env  # noqa: E402

W, H = 1280, 720
REAL = headless_env.setup(W, H)
from app import Application, Options  # noqa: E402

OUT = os.path.join(ROOT, "docs", "img")
os.makedirs(OUT, exist_ok=True)
FI = headless_env.FakeInput


def capture(name, t, mode="1", keys=(), shadows=True, hud=True):
    app = Application((W, H), Options(hud=hud, shadows=shadows))
    app.update(t, FI())
    app.update(0.0, FI(down={mode} | set(keys)))
    for _ in range(4):
        app.orbit.update(1.0, FI(), app._followPoints())
    app.update(0.0, FI())
    app.render()
    headless_env.readFramebuffer(W, H).save(os.path.join(OUT, name))
    print("gerado", name)


capture("01_visao_geral_estabilizacao.png", 9.0)
capture("02_astronauta_sinalizando.png", 17.5, mode="2")
capture("03_resposta_da_nave.png", 20.4, mode="3")
capture("04_mapa_de_sombras_g.png", 13.0, keys=("g",))
capture("05_sem_sombras_comparacao.png", 13.0, shadows=False)
capture("06_nave_partindo.png", 27.0, mode="3")
