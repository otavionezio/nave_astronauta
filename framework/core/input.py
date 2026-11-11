"""
Entrada do usuário (teclado e mouse) via Pygame.
Base: STEMKOSKI & PASCALE (2022), seção 2.5 (listas keyDown / keyPressed / keyUp).
Adaptações: remoção segura de teclas (evita ValueError), mouse (arrasto e roda).

  * keyDown / keyUp  : eventos DISCRETOS, duram só uma iteração do loop principal;
  * keyPressed       : estado CONTÍNUO entre o KEYDOWN e o KEYUP.
"""
import pygame


class Input(object):

    def __init__(self):
        self.quit = False
        self.keyDownList = []
        self.keyPressedList = []
        self.keyUpList = []
        # mouse
        self.mouseDelta = (0, 0)       # deslocamento desde o último quadro
        self.mouseWheel = 0            # +1 / -1 por "clique" da roda
        self.mouseButtonsPressed = set()

    def update(self):
        # estados discretos valem por um único quadro
        self.keyDownList = []
        self.keyUpList = []
        self.mouseDelta = (0, 0)
        self.mouseWheel = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit = True

            if event.type == pygame.KEYDOWN:
                keyName = pygame.key.name(event.key)
                self.keyDownList.append(keyName)
                if keyName not in self.keyPressedList:
                    self.keyPressedList.append(keyName)

            if event.type == pygame.KEYUP:
                keyName = pygame.key.name(event.key)
                if keyName in self.keyPressedList:
                    self.keyPressedList.remove(keyName)
                self.keyUpList.append(keyName)

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.mouseButtonsPressed.add(event.button)
            if event.type == pygame.MOUSEBUTTONUP:
                self.mouseButtonsPressed.discard(event.button)
            if event.type == pygame.MOUSEMOTION:
                self.mouseDelta = (self.mouseDelta[0] + event.rel[0],
                                   self.mouseDelta[1] + event.rel[1])
            if event.type == pygame.MOUSEWHEEL:
                self.mouseWheel += event.y

    def isKeyDown(self, keyCode):
        return keyCode in self.keyDownList

    def isKeyPressed(self, keyCode):
        return keyCode in self.keyPressedList

    def isKeyUp(self, keyCode):
        return keyCode in self.keyUpList

    def isMousePressed(self, button=1):
        return button in self.mouseButtonsPressed
