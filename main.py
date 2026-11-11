#!/usr/bin/env python3
"""
Nave x Astronauta — cena 3D animada (Python + Pygame + PyOpenGL + framework de
Stemkoski & Pascale, 2022).

    python main.py                 execução normal
    python main.py --loop          reinicia sozinho ao concluir
    python main.py --fps 15        limita a 15 FPS (prova de independência da taxa de quadros)
    python main.py --size 1600x900 --shadow-res 4096 --pcf 2
    python main.py --no-shadows    desliga o shadow mapping (comparação)
    python main.py --gl-check      liga a verificação de erros do PyOpenGL (mais lento)
"""
import argparse
import sys


def parseArgs(argv):
    p = argparse.ArgumentParser(description="Nave x Astronauta (Computação Gráfica)")
    p.add_argument("--size", default="1280x720", help="tamanho da janela, ex.: 1280x720")
    p.add_argument("--fps", type=int, default=60, help="limite de FPS (0 = sem limite)")
    p.add_argument("--loop", action="store_true", help="reinicia a sequência automaticamente")
    p.add_argument("--no-hud", action="store_true", help="oculta o HUD")
    p.add_argument("--no-shadows", action="store_true", help="desliga as sombras")
    p.add_argument("--shadow-res", type=int, default=2048, help="resolução do mapa de sombras")
    p.add_argument("--pcf", type=int, default=1, help="raio do filtro PCF (0 = sombra dura)")
    p.add_argument("--no-msaa", action="store_true", help="sem antialiasing")
    p.add_argument("--gl-check", action="store_true", help="verifica erros do PyOpenGL a cada chamada")
    return p.parse_args(argv)


def main(argv=None):
    args = parseArgs(sys.argv[1:] if argv is None else argv)

    try:
        # precisa vir ANTES de importar OpenGL.GL: sem a verificação, cada chamada fica bem mais rápida
        import OpenGL
        OpenGL.ERROR_CHECKING = bool(args.gl_check)

        import bootstrap  # noqa: F401
        from core.base import Base
        from core.openGLUtils import OpenGLUtils
        from app import Application, Options
    except ImportError as erro:
        print("Dependência ausente: %s\nInstale com:  pip install -r requirements.txt" % erro)
        return 1

    width, height = (int(v) for v in args.size.lower().split("x"))
    options = Options(loop=args.loop, hud=not args.no_hud, shadows=not args.no_shadows,
                      shadowResolution=args.shadow_res, pcf=args.pcf)

    class Main(Base):
        def initialize(self):
            OpenGLUtils.printSystemInfo()
            self.app = Application(self.screenSize, options)
            self.captionTimer = 0.0

        def update(self):
            if self.input.isKeyDown("escape"):
                self.running = False
            self.app.update(self.deltaTime, self.input)
            self.app.render()
            self.captionTimer += self.deltaTime
            if self.captionTimer > 0.4:             # título da janela: estado + FPS
                import pygame
                pygame.display.set_caption(self.app.caption())
                self.captionTimer = 0.0

    Main(screenSize=(width, height), title="Nave x Astronauta", maxFps=args.fps,
         multisample=not args.no_msaa).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
