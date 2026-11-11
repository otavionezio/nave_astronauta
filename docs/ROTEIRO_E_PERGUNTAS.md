# Roteiro da apresentação (≈ 10 min) e perguntas técnicas

> Os dois integrantes precisam falar e **explicar sua própria contribuição** (30% da nota é individual).
> Distribuam os blocos abaixo (A / B) conforme o que cada um realmente fez e estudou.
> Ensaiem com cronômetro. Deixem a aplicação **já aberta** (`python main.py`) antes de começar.

## 1. Roteiro cronometrado

| Tempo | Bloco | Quem | O que mostrar / dizer |
|---|---|---|---|
| 0:00–0:40 | Tema e objetivos | `[A]` | Nave espacial + astronauta, estética Warhammer 40.000, plataforma de inspeção. Requisitos do enunciado em uma frase cada. |
| 0:40–2:10 | **Demonstração da cena e da interação** | `[A]` | Deixe a sequência rodar (≈ 30 s). Narre os estados que aparecem no HUD: aproximação → estabilização → reação (caminha) → sinalização (aceno) → resposta (3 pulsos) → retomada (braço baixa, **só então** a nave parte). Enfatize a causa e efeito. |
| 2:10–3:30 | Modelagem por primitivas e hierarquia | `[B]` | Tecla `2`: astronauta (125 primitivas, 14 juntas). Tecla `3`: nave. Mostre `modeling.PartBuilder.add` (T·R·S) e `Astronaut.applyPose`. Explique: ombro → cotovelo → mão herdam a transformação do pai; ombreira segue 35%. |
| 3:30–4:30 | Animação por delta time | `[B]` | Mostre `animation.py` (`stateTime += dt`). **Demonstre:** feche e rode `--fps 15` e `--fps 120`: a sequência dura o mesmo tempo. Cite os testes (15–240 FPS idênticos). |
| 4:30–5:30 | Câmera e controles | `[A]` | Orbite (setas/mouse), zoom, teclas 1–4, **`ESPAÇO` pausa (a câmera continua)**, `R` reinicia, `,`/`.` velocidade. Mostre `camera.py` (esfera + look-at; limites). |
| 5:30–6:30 | Textura, iluminação e materiais | `[B]` | Deck e casco: textura PNG com UV (`uvTile`, `GL_REPEAT`). 4 luzes. Phong = ambiente + difusa + especular (ouro × tecido). A luz laranja dos motores muda nos pulsos. |
| 6:30–8:15 | **Shadow mapping** | `[A]` ou `[B]` | `--no-shadows` × padrão. Tecla `G`: mapa de profundidade. Explique os 2 passes (abaixo), mostre `Renderer._shadowPass`, `lit.vert` (`shadowPosition0`), `lit.frag` (`computeShadowAmount`). Distinga sombreamento × sombra projetada. Mencione acne/viés. |
| 8:15–9:15 | Shaders e organização | `[B]` | Tabela de atributos/uniforms (README §9.8); `layout(location)`; `shaders/` com `#include`; framework do livro × adaptações (README §14). |
| 9:15–10:00 | Divisões e fechamento | `[A]+[B]` | Quem fez o quê; uso de IA declarado (o que a IA fez; o que vocês revisaram/testaram); limitações honestas. |

**Plano B se a janela falhar:** abram `docs/img/*.png` e o código; digam claramente que a validação foi numa camada de teste.

## 2. O passo a passo do shadow mapping (para explicar no quadro)

1. A luz direcional ganha uma **câmera ortográfica** (`light/shadow.py`) olhando na direção dos raios.
2. **Passe 1:** `Renderer._shadowPass` desenha a cena inteira *vista da luz* com `DepthMaterial`. O fragment shader grava a
   profundidade (`gl_FragCoord.z`, 0 = perto da luz, 1 = longe) numa textura `R32F`. Resultado: "a distância ao objeto mais
   próximo da luz, em cada direção".
3. **Passe 2:** para cada vértice da cena normal, `lit.vert` calcula também `P_luz · V_luz · M · v` (onde ele cairia na imagem da luz).
4. No `lit.frag`: converte de [-1,1] para [0,1] → (u,v) para ler o mapa e `z` para comparar.
5. Se `z_fragmento > z_mapa + viés` ⇒ há algo mais perto da luz ⇒ **está na sombra** ⇒ reduz a luz direta.
6. Repete **todo quadro**, por isso a sombra acompanha o movimento.

## 3. Perguntas técnicas prováveis e respostas

**1. Qual a diferença entre sombreamento e sombra projetada?**
Sombreamento (shading) depende só da superfície e da luz: `N·L` — faces de costas para a luz ficam escuras. Sombra projetada exige
saber se **outro objeto** está no caminho da luz; por isso precisamos do mapa de profundidade. Uma face pode estar sombreada sem
estar na sombra de ninguém (e vice-versa: uma face voltada para a luz pode estar na sombra de outro objeto).

**2. Por que dois passes?** Para comparar profundidades é preciso primeiro *conhecer* a profundidade vista da luz (passe 1); só então
a cena principal pode consultá-la (passe 2). O passe 1 não vai para a tela: vai para um framebuffer (`RenderTarget`).

**3. Por que câmera ortográfica na luz?** A luz direcional tem raios paralelos; a projeção ortográfica também. Em perspectiva os raios
divergiriam (isso serve para luzes pontuais/spot). Com ortográfica, `w = 1` e não precisamos dividir por `w` no shader.

**4. O que é "acne de sombra" e como vocês trataram?** A superfície se sombreia a si mesma porque a profundidade interpolada e a
guardada diferem por pouco (precisão e inclinação). Usamos `bias` (0,0004) + `slopeBias` (0,0025·(1−N·L)). Medimos: sem viés o teste
detecta acne; metade dos valores já gera acne (folga ≈ 2×). Viés grande demais "descola" a sombra do objeto (*peter-panning*).

**5. Por que a textura de profundidade é R32F e não RGBA8 como no livro?** RGBA8 guarda 256 níveis; num volume de ~90 m cada nível
seria ≈ 0,35 m e o viés teria de ser enorme. Com float de 32 bits o viés fica pequeno. O resto da técnica é a da seção 6.9.

**6. Por que `· 0,5 + 0,5`?** O clip space vai de −1 a 1; coordenadas de textura e a profundidade guardada vão de 0 a 1.

**7. O que acontece fora do volume da câmera da luz?** Não há dado no mapa: o shader trata como "sem sombra" (teste de [0,1] + cor de borda
branca). Por isso a sombra da nave só aparece quando ela entra nos ±23 m.

**8. O que é PCF?** *Percentage-closer filtering*: em vez de uma comparação, faz 9 (3×3) e usa a média ⇒ bordas suaves em vez de serrilhadas.

**9. Como a animação fica independente da taxa de quadros?** O tempo do estado avança por `dt` em segundos (`stateTime += dt`), e as
poses são funções de `(estado, stateTime)`. Se um quadro cruza o fim de um estado, a sobra vai para o próximo. O `Base` limita `dt` a 0,05 s
para uma pausa longa não causar salto. Testes: 15, 30, 60, 144 e 240 FPS (e `dt` aleatório) dão o mesmo resultado.

**10. Como pausar sem congelar a visualização?** O `Application` passa `dt_simulado = 0` ao diretor (nada muda) e o `dt` real à câmera
(continua orbitando). Ao retomar, a simulação continua do mesmo ponto.

**11. Como garantem que a nave só parte depois do astronauta?** Na `RETOMADA` há duas fases: o braço baixa por 1,0 s
(`armRaise` vai a 0 exatamente) e só depois `departureEnabled` fica verdadeiro e a nave se move. Há testes que verificam
`departureEnabled ⇒ armRaise == 0` em todos os instantes.

**12. Como funciona a hierarquia? Ordem das matrizes?** Cada nó guarda uma matriz local; a de mundo é `W = W_pai · T_local`. Em `A @ B`,
B age primeiro. Para um braço: `T(ombro) · Rz(roll) · Rx(pitch)` — gira para a frente e depois para o lado; o cotovelo é filho do ombro,
então herda tudo. Recompomos as matrizes a partir dos ângulos a cada quadro (não acumulamos rotações ⇒ sem deriva numérica).

**13. Diferença entre `localCoord=True` e `False` em `applyMatrix`?** `True`: `T·M` (a operação ocorre nos eixos do próprio objeto, ex.: andar para a sua frente
depois de girar). `False`: `M·T` (nos eixos do pai/mundo).

**14. Atributo, uniform e varying — qual a diferença?** Atributo: dado **por vértice** (posição, UV, normal), vem de VBOs. Uniform: valor **igual para todo o desenho**
(matrizes, cor, luzes). Varying (`out`/`in`): o vertex shader calcula por vértice e o rasterizador **interpola** para o fragment shader (`position`, `UV`, `normal`, `shadowPosition0`).

**15. O que são VAO e VBO?** VBO: buffer na GPU com os dados de um atributo. VAO: guarda quais VBOs estão ligados a quais variáveis `in`. Cada `Mesh` tem seu VAO;
por isso fixamos `layout(location=N)`: o mesmo VAO precisa servir ao programa principal e ao `DepthMaterial`.

**16. Por que `GL_TRUE` em `glUniformMatrix4fv`?** O NumPy guarda por linhas; o GLSL espera por colunas; `GL_TRUE` pede a transposição.

**17. Por que a normal usa a inversa transposta?** Numa escala não uniforme, transformar a normal como um ponto a deixaria inclinada em relação à superfície.
A inversa transposta preserva a perpendicularidade (`lit.vert`; `Geometry.applyMatrix` e `PartBuilder` também).

**18. O que a perspectiva faz?** `makePerspective` leva o *frustum* ao cubo [−1,1]³; a divisão por `w` (feita pelo hardware) produz o encurtamento.
Near/far definem o intervalo de profundidade (0,1 a 1000 m).

**19. Como a câmera e a nave "olham" para algo?** `Matrix.makeLookAt`: constrói a base (right, up, −forward) a partir da posição e do alvo.
A câmera usa a inversa dessa matriz como `viewMatrix`. A nave usa `yaw_to` (ângulo em y) e `Ry(yaw)`.

**20. Como funciona o Phong no código?** `shaders/common_light.glsl::lightCalc`: ambiente (constante) + difusa `max(N·L,0)` + especular `specularStrength·max(R·V,0)^shininess`,
tudo multiplicado pela cor da luz e pela cor/textura do material. Lambert é o mesmo sem o termo especular (`USE_SPECULAR`).

**21. O que são UV e como evitaram esticar a textura?** UV mapeia cada vértice a um ponto da imagem. Em `BoxGeometry(uvTile=4)` as UV vão até (tamanho da face)/4,
com `GL_REPEAT`: a imagem se repete a cada 4 m. Mipmaps (`GL_LINEAR_MIPMAP_LINEAR`) evitam cintilação ao longe.

**22. Por que fundir geometrias (`merge`)?** Cada `Mesh` custa uma chamada de desenho (e outra no passe de sombra). 125 primitivas viraram 44 malhas; a cena inteira tem
70 malhas (128 desenhos por quadro com sombra). A hierarquia de animação continua nas articulações.

**23. Por que culling de faces e como sabem que o enrolamento está certo?** Faces de trás não aparecem; descartá-las economiza trabalho. Teste: o volume com sinal calculado
pelos triângulos é positivo e igual ao analítico ⇒ todos os triângulos têm a orientação anti-horária vista de fora.

**24. Limites do framework?** 4 luzes; uma `Shadow` (só direcional); sombras só dentro do volume ortográfico.

**25. O que mudaram em relação ao livro?** (README §14) `itemset` (NumPy 2), `texture2D`→`texture`, sombra em R32F com viés por inclinação e PCF, restauração do `clearColor`,
`layout(location)` fixo, normais sem NaN, normais por inversa transposta, luzes em coordenadas de mundo, cache de programas/matrizes, escala por eixo.

**26. Como validaram?** Camada de teste em `ctypes` sobre a Mesa (OpenGL 4.5 core por software): compilação dos shaders, 56 testes automáticos e inspeção visual — e **mutações** que
confirmam que os testes de sombra detectam acne e sombra descolada. **Não** testamos com Pygame/PyOpenGL reais nem em GPU: isso está na lista manual `[PREENCHER com o que vocês executaram]`.

## 4. Perguntas sobre a contribuição de cada um (respondam com fatos)

* "Qual trecho você escreveu/alterou? Mostre no código." → `[A: ...]` `[B: ...]`
* "Se eu mudar `bias` para 0, o que acontece? E `strength`?" → acne; sombras mais claras/escuras (demonstrem editando `lighting.SHADOW`).
* "Como faria a nave acenar de volta com uma luz?" → mudar `enginePower`/`beaconOn` na `RESPOSTA_DA_NAVE` (`animation._computeShip`).
* "Como adicionaria uma segunda sombra?" → o framework tem uma `Shadow`; seria preciso estendê-lo (novo `shadow1`, outro passe).
* "O que a IA fez e o que vocês fizeram?" → seção 14 do README, **preenchida com a verdade**.

> Dica de estudo: abram `animation.py`, `modeling.py`, `core/renderer.py`, `shaders/lit.frag` e **leiam em voz alta explicando cada bloco**.
> Se não conseguirem explicar um trecho, não digam que o escreveram: expliquem o que ele faz e peçam para mostrar o conceito no livro (cap. 3, 4, 5 e seção 6.9).
