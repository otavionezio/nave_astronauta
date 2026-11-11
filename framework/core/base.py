"""
Janela + loop principal (Pygame/OpenGL).
Base: STEMKOSKI & PASCALE (2022), seções 2.1 e 2.4.3.

Adaptações:
  * pede contexto OpenGL 3.3 core explicitamente e tenta de novo sem MSAA se a
    placa/driver não oferecer multisample;
  * deltaTime vem do retorno de clock.tick() (segundos desde o quadro anterior)
    e é LIMITADO (maxDeltaTime) para que uma pausa longa (arrastar a janela,
    breakpoint) não produza um "salto" enorme na animação.

Animação independente da taxa de quadros: todo movimento usa deltaTime
(distância = velocidade * deltaTime), nunca "um passo por quadro".
"""
import pygame


class Base(object):

    def __init__(self, screenSize=(1280, 720), title="Graphics Window",
                 maxFps=60, maxDeltaTime=0.05, multisample=True):
        pygame.init()
        self.screenSize = tuple(screenSize)
        displayFlags = pygame.DOUBLEBUF | pygame.OPENGL

        def configure(samples):
            pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)          # buffer de profundidade explícito
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1 if samples else 0)
            pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, samples)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
            pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                            pygame.GL_CONTEXT_PROFILE_CORE)

        try:
            configure(4 if multisample else 0)
            self.screen = pygame.display.set_mode(self.screenSize, displayFlags)
        except pygame.error:
            configure(0)          # sem antialiasing
            self.screen = pygame.display.set_mode(self.screenSize, displayFlags)
        pygame.display.set_caption(title)

        self.running = True
        self.clock = pygame.time.Clock()
        self.maxFps = maxFps                  # 0 = sem limite
        self.maxDeltaTime = maxDeltaTime
        self.deltaTime = 0.0                  # segundos do último quadro
        self.time = 0.0                       # tempo total de execução (s)

        from core.input import Input
        self.input = Input()

    # a implementar nas classes filhas
    def initialize(self):
        pass

    def update(self):
        pass

    def run(self):
        ## startup ##
        self.initialize()
        self.clock.tick()          # descarta o tempo gasto na inicialização

        ## main loop ##
        while self.running:
            ## process input ##
            self.input.update()
            if self.input.quit:
                self.running = False

            ## tempo: delta time do quadro anterior ##
            elapsed = self.clock.tick(self.maxFps) / 1000.0
            self.deltaTime = min(elapsed, self.maxDeltaTime)
            self.time += self.deltaTime

            ## update + render ##
            self.update()
            pygame.display.flip()

        ## shutdown ##
        pygame.quit()
