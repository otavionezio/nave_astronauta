"""
Renderer: desenha um Scene a partir de uma Camera.
Base: STEMKOSKI & PASCALE (2022), seções 4.5, 5.8, 6.5 e 6.9.2.

Dois passes quando as sombras estão ativas:
  1) PASSE DE SOMBRA : cena vista da luz (câmera ortográfica da luz), usando o
     DepthMaterial -> grava a profundidade de cada pixel na textura do mapa de sombras;
  2) PASSE PRINCIPAL : cena vista da câmera do usuário; os shaders dos materiais
     Lambert/Phong comparam a profundidade de cada fragmento (no espaço da luz)
     com a profundidade guardada no mapa.

Adaptações em relação ao livro (todas visam desempenho/robustez):
  * as matrizes de mundo são calculadas UMA vez por quadro (node.worldCache);
  * as malhas são agrupadas por programa/material: luzes, câmera e sombra são
    enviadas uma vez por programa, e os uniforms do material só quando o material muda;
  * a cor de limpeza é restaurada depois do passe de sombra (o livro deixa branca);
  * o passe de sombra fixa o estado do OpenGL (sem culling, preenchimento);
  * parâmetro useShadows=False p/ camadas auxiliares (HUD) sem refazer o passe de sombra.
"""
import pygame
from OpenGL.GL import *
from core.mesh import Mesh
from light.light import Light
from light.shadow import Shadow

# uniforms que dependem do quadro/câmera (enviados uma vez por programa)
PER_FRAME_UNIFORMS = ("viewMatrix", "projectionMatrix", "viewPosition",
                      "light0", "light1", "light2", "light3", "shadow0")


class Renderer(object):

    def __init__(self, clearColor=(0, 0, 0), windowSize=None):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_MULTISAMPLE)        # antialiasing (se o contexto tiver amostras)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.clearColor = list(clearColor)
        glClearColor(self.clearColor[0], self.clearColor[1], self.clearColor[2], 1)

        if windowSize is None:
            windowSize = pygame.display.get_surface().get_size()
        self.windowSize = tuple(windowSize)

        self.shadowsEnabled = False
        self.shadowObject = None
        self.drawCalls = 0              # estatística do último render()

    def enableShadows(self, shadowLight, strength=0.5, resolution=(512, 512),
                      cameraBounds=(-5, 5, -5, 5, 0, 20), bias=0.01, slopeBias=0.0, pcf=0):
        self.shadowsEnabled = True
        self.shadowObject = Shadow(shadowLight, strength=strength, resolution=resolution,
                                   cameraBounds=cameraBounds, bias=bias,
                                   slopeBias=slopeBias, pcf=pcf)

    # ------------------------------------------------------------------
    @staticmethod
    def _updateWorldMatrices(root, descendants):
        # pré-ordem: o pai sempre é visitado antes dos filhos, então o cache dele já existe
        for node in descendants:
            if node is root:
                node.worldCache = node.getWorldMatrix()
            else:
                node.worldCache = node.parent.worldCache @ node.transform

    def _shadowPass(self, meshes):
        target = self.shadowObject.renderTarget
        glBindFramebuffer(GL_FRAMEBUFFER, target.framebufferRef)
        glViewport(0, 0, target.width, target.height)

        # branco = profundidade máxima: onde nada é desenhado não há sombra
        glClearColor(1, 1, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_CULL_FACE)
        glDisable(GL_BLEND)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        material = self.shadowObject.material
        glUseProgram(material.programRef)
        self.shadowObject.updateInternal()      # atualiza view/projection da câmera da luz
        material.uniforms["viewMatrix"].uploadData()
        material.uniforms["projectionMatrix"].uploadData()

        modelUniform = material.uniforms["modelMatrix"]
        for mesh in meshes:
            if not mesh.castShadow:
                continue
            if mesh.material.settings["drawStyle"] != GL_TRIANGLES:
                continue                         # só triângulos projetam sombra
            glBindVertexArray(mesh.vaoRef)
            modelUniform.data = mesh.worldCache
            modelUniform.uploadData()
            glDrawArrays(GL_TRIANGLES, 0, mesh.geometry.vertexCount)
            self.drawCalls += 1

        # restaura o estado que o passe principal espera
        glEnable(GL_BLEND)
        glClearColor(self.clearColor[0], self.clearColor[1], self.clearColor[2], 1)

    # ------------------------------------------------------------------
    def render(self, scene, camera, clearColor=True, clearDepth=True,
               renderTarget=None, useShadows=True):
        self.drawCalls = 0
        descendants = scene.getDescendantList()
        self._updateWorldMatrices(scene, descendants)

        meshes = [n for n in descendants if isinstance(n, Mesh) and n.visible]
        lightList = [n for n in descendants if isinstance(n, Light)][:4]
        while len(lightList) < 4:
            lightList.append(Light())            # luz "vazia": contribuição zero
        shadowsActive = self.shadowsEnabled and useShadows

        # ---- passe 1: mapa de sombras ----
        if shadowsActive:
            self._shadowPass(meshes)

        # ---- passe 2: cena principal ----
        if renderTarget is None:
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            glViewport(0, 0, self.windowSize[0], self.windowSize[1])
        else:
            glBindFramebuffer(GL_FRAMEBUFFER, renderTarget.framebufferRef)
            glViewport(0, 0, renderTarget.width, renderTarget.height)
        if clearColor:
            glClear(GL_COLOR_BUFFER_BIT)
        if clearDepth:
            glClear(GL_DEPTH_BUFFER_BIT)

        camera.updateViewMatrix()
        cameraPosition = camera.getWorldPosition()

        # agrupa por programa e material (menos trocas de estado)
        meshes.sort(key=lambda m: (m.material.programRef, id(m.material)))

        lastProgram = None
        lastMaterial = None
        for mesh in meshes:
            material = mesh.material
            uniforms = material.uniforms

            if material.programRef != lastProgram:
                glUseProgram(material.programRef)
                lastProgram = material.programRef
                lastMaterial = None
                # uniforms "por quadro": câmera, luzes, sombra
                uniforms["viewMatrix"].data = camera.viewMatrix
                uniforms["projectionMatrix"].data = camera.projectionMatrix
                uniforms["viewMatrix"].uploadData()
                uniforms["projectionMatrix"].uploadData()
                if "viewPosition" in uniforms:
                    uniforms["viewPosition"].data = cameraPosition
                    uniforms["viewPosition"].uploadData()
                if "light0" in uniforms:
                    for i in range(4):
                        name = "light" + str(i)
                        uniforms[name].data = lightList[i]
                        uniforms[name].uploadData()
                if shadowsActive and "shadow0" in uniforms:
                    uniforms["shadow0"].data = self.shadowObject
                    uniforms["shadow0"].uploadData()

            if material is not lastMaterial:
                # uniforms do material (cor, textura, brilho...) + estado do OpenGL
                for name, uniformObject in uniforms.items():
                    if name in PER_FRAME_UNIFORMS or name == "modelMatrix":
                        continue
                    if name == "useShadow" and not shadowsActive:
                        glUniform1i(uniformObject.variableRef, 0)
                        continue
                    uniformObject.uploadData()
                material.updateRenderSettings()
                lastMaterial = material

            # uniform por objeto: matriz de modelo (mundo)
            uniforms["modelMatrix"].data = mesh.worldCache
            uniforms["modelMatrix"].uploadData()

            glBindVertexArray(mesh.vaoRef)
            glDrawArrays(material.settings["drawStyle"], 0, mesh.geometry.vertexCount)
            self.drawCalls += 1
