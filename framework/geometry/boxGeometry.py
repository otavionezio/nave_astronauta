from geometry.geometry import Geometry


class BoxGeometry(Geometry):
    """
    Caixa centrada na origem (STEMKOSKI & PASCALE, 2022, 4.3.2 / 5.2.2 / 6.3.2).
    Ordem das faces: x+, x-, y+, y-, z+, z-  (6 vértices por face, 2 triângulos CCW).

    Adaptação: uvTile (opcional). Se informado, as coordenadas UV de cada face vão de
    0 até (tamanho da face / uvTile), de modo que a textura (wrap = REPEAT) se repita
    com a mesma densidade em faces grandes e pequenas, sem esticar.
    """

    def __init__(self, width=1, height=1, depth=1, uvTile=None):
        super().__init__()
        P0 = [-width / 2, -height / 2, -depth / 2]
        P1 = [width / 2, -height / 2, -depth / 2]
        P2 = [-width / 2, height / 2, -depth / 2]
        P3 = [width / 2, height / 2, -depth / 2]
        P4 = [-width / 2, -height / 2, depth / 2]
        P5 = [width / 2, -height / 2, depth / 2]
        P6 = [-width / 2, height / 2, depth / 2]
        P7 = [width / 2, height / 2, depth / 2]

        C1, C2 = [1, 0.5, 0.5], [0.5, 0, 0]
        C3, C4 = [0.5, 1, 0.5], [0, 0.5, 0]
        C5, C6 = [0.5, 0.5, 1], [0, 0, 0.5]

        positionData = [P5, P1, P3, P5, P3, P7,   # x+
                        P0, P4, P6, P0, P6, P2,   # x-
                        P6, P7, P3, P6, P3, P2,   # y+
                        P0, P1, P5, P0, P5, P4,   # y-
                        P4, P5, P7, P4, P7, P6,   # z+
                        P1, P0, P2, P1, P2, P3]   # z-
        colorData = [C1] * 6 + [C2] * 6 + [C3] * 6 + [C4] * 6 + [C5] * 6 + [C6] * 6

        T0, T1, T2, T3 = [0, 0], [1, 0], [0, 1], [1, 1]
        faceUV = [T0, T1, T3, T0, T3, T2]
        if uvTile is None:
            uvData = faceUV * 6
        else:
            # (u,v) de cada face: x±: (depth, height)  y±: (width, depth)  z±: (width, height)
            faceSizes = [(depth, height)] * 2 + [(width, depth)] * 2 + [(width, height)] * 2
            uvData = []
            for fu, fv in faceSizes:
                su, sv = fu / uvTile, fv / uvTile
                uvData += [[t[0] * su, t[1] * sv] for t in faceUV]

        N1, N2 = [1, 0, 0], [-1, 0, 0]
        N3, N4 = [0, 1, 0], [0, -1, 0]
        N5, N6 = [0, 0, 1], [0, 0, -1]
        normalData = [N1] * 6 + [N2] * 6 + [N3] * 6 + [N4] * 6 + [N5] * 6 + [N6] * 6

        self.addAttribute("vec3", "vertexPosition", positionData)
        self.addAttribute("vec3", "vertexColor", colorData)
        self.addAttribute("vec2", "vertexUV", uvData)
        self.addAttribute("vec3", "vertexNormal", normalData)
        self.addAttribute("vec3", "faceNormal", normalData)
        self.countVertices()
