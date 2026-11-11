"""
Nó do grafo de cena (Object3D): matriz de transformação local + pai + filhos.
Base: STEMKOSKI & PASCALE (2022), seção 4.2 e 6.2 (direção).

Transformações locais x globais (applyMatrix):
    localCoord=True  ->  T_novo = T @ M   (M age no sistema de coordenadas do próprio objeto)
    localCoord=False ->  T_novo = M @ T   (M age no sistema do PAI / "mundo")
Matriz de mundo:  W = W_pai @ T_local   (aplicada recursivamente até a raiz).

Adaptações: setPosition por indexação (ndarray.itemset foi removido no NumPy 2.0);
scale() aceita escala por eixo; getWorldDirection (luzes filhas de outros nós).
"""
import numpy
from core.matrix import Matrix


class Object3D(object):

    def __init__(self):
        self.transform = Matrix.makeIdentity()
        self.parent = None
        self.children = []
        # cache preenchido pelo Renderer a cada quadro (evita recalcular a cadeia de pais)
        self.worldCache = None

    def add(self, child):
        self.children.append(child)
        child.parent = self

    def remove(self, child):
        self.children.remove(child)
        child.parent = None

    # transformação deste objeto relativa à raiz do grafo
    def getWorldMatrix(self):
        if self.parent is None:
            return self.transform
        return self.parent.getWorldMatrix() @ self.transform

    # lista de todos os descendentes (pré-ordem: pai sempre antes dos filhos)
    def getDescendantList(self):
        descendants = []
        nodesToProcess = [self]
        while len(nodesToProcess) > 0:
            node = nodesToProcess.pop(0)
            descendants.append(node)
            nodesToProcess = node.children + nodesToProcess
        return descendants

    # ---- transformações geométricas ----
    def applyMatrix(self, matrix, localCoord=True):
        if localCoord:
            self.transform = self.transform @ matrix
        else:
            self.transform = matrix @ self.transform

    def translate(self, x, y, z, localCoord=True):
        self.applyMatrix(Matrix.makeTranslation(x, y, z), localCoord)

    def rotateX(self, angle, localCoord=True):
        self.applyMatrix(Matrix.makeRotationX(angle), localCoord)

    def rotateY(self, angle, localCoord=True):
        self.applyMatrix(Matrix.makeRotationY(angle), localCoord)

    def rotateZ(self, angle, localCoord=True):
        self.applyMatrix(Matrix.makeRotationZ(angle), localCoord)

    def scale(self, sx, sy=None, sz=None, localCoord=True):
        self.applyMatrix(Matrix.makeScale(sx, sy, sz), localCoord)

    # ---- posição / direção ----
    def getPosition(self):
        return [self.transform[0, 3], self.transform[1, 3], self.transform[2, 3]]

    def getWorldPosition(self):
        w = self.getWorldMatrix()
        return [w[0, 3], w[1, 3], w[2, 3]]

    def setPosition(self, position):
        self.transform[0, 3] = position[0]
        self.transform[1, 3] = position[1]
        self.transform[2, 3] = position[2]

    def lookAt(self, targetPosition):
        self.transform = Matrix.makeLookAt(self.getWorldPosition(), targetPosition)

    # submatriz 3x3 de rotação (com escala, se houver)
    def getRotationMatrix(self):
        return numpy.array(self.transform[0:3, 0:3])

    # "frente" do objeto = eixo -z local
    def getDirection(self):
        return list(self.getRotationMatrix() @ numpy.array([0, 0, -1]))

    def getWorldDirection(self):
        w = self.getWorldMatrix()
        d = w[0:3, 0:3] @ numpy.array([0.0, 0.0, -1.0])
        return list(d / numpy.linalg.norm(d))

    def setDirection(self, direction):
        position = self.getPosition()
        target = [position[0] + direction[0], position[1] + direction[1], position[2] + direction[2]]
        self.lookAt(target)
