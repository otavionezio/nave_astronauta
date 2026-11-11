# Plano de testes

Legenda de situação: **✔ automatizado e passando** (na camada de teste da Mesa — ver README §11) ·
**☐ manual — NÃO executado** (o grupo precisa fazer na própria máquina, com Pygame e PyOpenGL reais).

## A. Como executar os testes automatizados

```bash
# 1) Lógica (não precisa de OpenGL, Pygame nem janela) — 35 testes
python -m unittest tests.test_logic -v

# 2) Gráficos (renderizam quadros e checam pixels) — 21 testes
python -m unittest tests.test_render_headless -v
#    Sem janela/GPU (Linux + Mesa) use a camada de teste:
FORCE_HEADLESS_SHIM=1 python tests/test_render_headless.py
#    Se nenhum contexto OpenGL puder ser criado, os testes são PULADOS (e avisam).

# 3) Sensibilidade dos testes de sombra (degrada o viés de propósito; índices 0..6)
FORCE_HEADLESS_SHIM=1 python tests/mutation_shadow_bias.py 0
```

Ferramentas de inspeção visual: `python tests/render_frames.py 9 17 --mode 2` (salva PNGs em `tests/output/`),
`python tools/gerar_capturas.py` (regenera `docs/img/`).

## B. Testes automatizados (o que cada um verifica)

### B1. `tests/test_logic.py` — lógica, sem OpenGL

| Requisito | Teste | Resultado esperado | Situação |
|---|---|---|---|
| Transformações | `test_composicao_aplica_a_direita_primeiro` | `T·S` escala e depois translada: (1,0,0) → (7,0,0) | ✔ |
| Hierarquia | `test_hierarquia_pai_filho`, `test_translacao_local_x_global` | posição/direção de mundo do filho = pai ∘ filho; `localCoord` muda o eixo | ✔ |
| Câmera | `test_perspectiva_mapeia_near_e_far`, `test_ortografica_mapeia_caixa_no_cubo`, `test_lookat_aponta_para_o_alvo` | z do near → −1, far → +1; caixa → cubo; frente = direção ao alvo | ✔ |
| NumPy 2 | `test_matriz_nao_tem_itemset` | nenhum `.itemset(` no código | ✔ |
| Interação | `test_ordem_e_instantes_dos_estados` | 7 estados na ordem, começando em 0; 7; 9,6; 15; 18,8; 22,4; 29,9 s | ✔ |
| Interação | `test_nave_nao_se_move_na_espera` | da estabilização até a partida a nave só oscila (< 0,2 m) | ✔ |
| Causa e efeito | `test_astronauta_so_anda_depois_da_nave_estabilizar`, `test_chega_na_marca_e_o_braco_so_sobe_depois` | astronauta imóvel até a REAÇÃO; braço em repouso enquanto anda; chega à marca | ✔ |
| Causa e efeito | `test_resposta_da_nave_so_depois_do_aceno_completo`, `test_tres_pulsos_dos_motores` | motores constantes durante o aceno; 3 acenos concluídos antes da resposta; exatamente 3 picos de potência | ✔ |
| Causa e efeito | `test_nave_so_parte_depois_que_o_braco_baixou` | `departureEnabled` ⇒ `armRaise == 0`; partida 1,0 s após o início de RETOMADA | ✔ |
| Conclusão/reinício | `test_conclusao_perceptivel_e_reinicio`, `test_modo_loop_reinicia_sozinho` | nave invisível em CONCLUIDO; `reset()` volta ao estado inicial; `--loop` reinicia | ✔ |
| Delta time | `test_independente_da_taxa_de_quadros` | poses a 15/30/60/144 FPS = a 240 FPS (tol. 1e-6) em 9 instantes | ✔ |
| Delta time | `test_dt_irregular_nao_altera_o_resultado`, `test_um_unico_passo_grande_equivale_a_varios_pequenos` | `dt` aleatório ou um passo de 17,3 s dão o mesmo resultado | ✔ |
| Pausa | `test_pausa_mantem_exatamente_o_estado`, `test_retomar_continua_coerente` | 500× `update(0)` não muda nada; pausar+retomar = nunca ter pausado | ✔ |
| Marcha | `test_passada_proporcional_a_distancia` | distância andada = 2,88 m (sem "patinar") | ✔ |
| Câmera | `test_elevacao_e_distancia_limitadas`, `test_camera_nunca_abaixo_do_piso`, `test_alvo_limitado_ao_deck` | 4° ≤ el ≤ 86°, 3 ≤ d ≤ 90, y ≥ 0,4, alvo no deck | ✔ |
| Câmera | `test_orbita…`, `test_mouse_e_roda`, `test_presets`, `test_camera_continua_com_a_animacao_pausada`, `test_empurra_a_camera_para_fora_do_obstaculo` | órbita, mouse, atalhos 1–4, dt real, obstáculo | ✔ |
| Shaders | `test_shaders_existem_e_includes_resolvem`, `test_shaders_sem_apis_removidas`, `test_localizacoes_de_atributos_coerentes` | sem `texture2D`; todo atributo com `layout(location)`; `vertexPosition` = 0 em todo vertex shader | ✔ |
| Texturas | `test_texturas_geradas_sao_reprodutiveis`, `test_texturas_repetiveis` | gerador determinístico; borda contínua (repetível) | ✔ |

### B2. `tests/test_render_headless.py` — gráficos (render real, 960×540)

| Requisito | Teste | Como mede / resultado esperado | Situação |
|---|---|---|---|
| Shaders | `test_materiais_e_shaders_compilam` | Phong+sombra, Lambert, Surface, Point, Depth compilam e ligam | ✔ |
| Normais/malha | `test_primitivas_sem_nan_normais_unitarias_e_faces_para_fora` | sem NaN; \|N\| = 1; volume com sinal > 0 e ≈ analítico (culling correto) | ✔ |
| Render | `test_quadro_sem_erro_gl_e_nao_vazio` | `glGetError() == 0`; imagem com desvio-padrão > 8; matrizes de mundo finitas | ✔ |
| Modelos | `test_modelos_tem_hierarquia_e_muitas_pecas` | ≥ 100 primitivas por modelo; profundidade da hierarquia ≥ 5 | ✔ |
| Textura | `test_textura_de_imagem_aplicada_ao_piso`, `test_uv_proporcional_ao_tamanho` | variação pixel a pixel no piso > 1,2; UV máx. = 9,0 num deck de 36 m | ✔ |
| Sombra | `test_sombra_do_astronauta_aparece_no_chao` | no ponto do piso previsto pela direção do sol, escurece (sombras ligadas × desligadas); o ponto simétrico (lado iluminado) **não** escurece | ✔ |
| Sombra | `test_sombra_da_nave_aparece_no_chao`, `test_sombra_some_quando_a_nave_sai_de_cena` | idem para a nave; some em CONCLUIDO | ✔ |
| Sombra | `test_sombra_acompanha_o_movimento` | centroide da sombra do astronauta se desloca > 2,5 px entre t=10,5 e 13,5 s | ✔ |
| Acne | `test_sem_acne_em_piso_livre` | em 3 pontos de piso livre, ligar/desligar sombras muda < 0,8 (média) e < 12 (máx.) | ✔ |
| Viés | `test_sombra_encosta_na_base_sem_flutuar` | poste isolado: sombra escurecida a 0,45/0,80/1,50 m da base; lado do sol intacto | ✔ |
| Mapa | `test_mapa_de_profundidade_visivel_com_g` | miniatura com contraste (σ > 6) e fundo branco | ✔ |
| Luzes | `test_luz_dos_motores_segue_a_nave`, `test_potencia_dos_motores_muda_a_cor_da_luz` | luz pontual filha da nave: segue a posição; cor varia > 0,5 nos pulsos | ✔ |
| FPS | `test_imagem_final_independe_da_taxa_de_quadros` | quadro em t=16 s a 30 FPS × 144 FPS: diferença média < 0,05 | ✔ |
| Pausa | `test_pausa_congela_a_cena_mas_nao_a_camera` | pausado: imagem idêntica após 120 quadros; câmera ainda move; retomar avança o tempo | ✔ |
| Controles | `test_reiniciar_volta_ao_estado_inicial`, `test_velocidade_da_simulacao`, `test_hud_aparece_e_pode_ser_ocultado` | `R`, `.`, HUD | ✔ |
| Câmera | `test_camera_nao_entra_na_caixa_da_nave` | zoom mínimo no centro da nave: câmera empurrada para fora | ✔ |

**Sensibilidade (mutação, `tests/mutation_shadow_bias.py`):** sem viés → `test_sem_acne…` falha (diferença média 20,9);
metade dos valores atuais → falha (3,97); viés 0,02 e 0,03 → `test_sombra_encosta…` falha; **viés 0,01 → NÃO falha** (limite do teste).

## C. Testes manuais — **NÃO executados** (fazer antes de apresentar)

Registrem data, máquina (SO, GPU, versões de Python/Pygame/PyOpenGL) e resultado em cada linha.

| ID | Procedimento | Resultado esperado | Resultado obtido |
|---|---|---|---|
| M-01 | `python -m venv .venv`, ativar, `pip install -r requirements.txt` | instala sem erro | ☐ |
| M-02 | `python main.py` | janela 1280×720; console mostra Vendor/Renderer/OpenGL ≥ 3.3; sem exceção de shader/textura | ☐ |
| M-03 | observar a cena parada por 1 s | deck texturizado, pad, pilares, planeta, estrelas; **sombras** dos pilares e contêineres | ☐ |
| M-04 | assistir à sequência completa (≈ 30 s) | 6 estados no HUD em ordem; a nave só parte após o braço descer; fim em "CONCLUIDO" | ☐ |
| M-05 | `ESPAÇO` durante a caminhada; esperar 5 s; `ESPAÇO` | tudo congela; a câmera ainda orbita (setas); retoma de onde parou | ☐ |
| M-06 | `R` em qualquer momento; `python main.py --loop` | reinicia; com `--loop` recomeça sozinho ~4 s após concluir | ☐ |
| M-07 | setas, mouse (arrastar, roda), W/S, A/D, Q/E, teclas 1–4 | câmera obedece; nunca atravessa o piso; é empurrada para fora da nave | ☐ |
| M-08 | `python main.py --fps 15` e `--fps 120` com cronômetro | a sequência dura o mesmo tempo (≈ 30 s ± 1 s); `15 FPS` só fica menos fluida | ☐ |
| M-09 | `,` e `.` | velocidade 0,25× … 4× (HUD mostra) | ☐ |
| M-10 | `G` | miniatura do mapa de profundidade no canto superior direito | ☐ |
| M-11 | `--no-shadows` × padrão | sem sombras projetadas × com sombras; iluminação (N·L) permanece | ☐ |
| M-12 | `--pcf 0`, `--pcf 2`, `--shadow-res 1024/4096` | bordas duras × suaves; resolução afeta a nitidez | ☐ |
| M-13 | observar o astronauta em `2` e a nave em `3` | peças reconhecíveis, sem faces "viradas" ou buracos; sem falhas de depth | ☐ |
| M-14 | procurar **acne** (listras/ruído nas superfícies voltadas ao sol) e sombra "flutuando" | nenhuma; se houver, aumentar `bias` em `lighting.SHADOW` (ex.: 0,0008) | ☐ |
| M-15 | `python main.py --gl-check` por 1 sequência | nenhum erro do PyOpenGL | ☐ |
| M-16 | `--no-msaa` | roda sem antialiasing (use se a criação da janela falhar) | ☐ |
| M-17 | fechar com `ESC` e pelo botão da janela | encerra sem exceção | ☐ |
| M-18 | medir FPS no HUD (`python main.py --fps 0`) | ≥ 30 FPS; registrar o valor | ☐ |
| M-19 | em outra máquina/SO, se possível | mesmo comportamento | ☐ |

Se algo falhar, copiem a mensagem **completa** do erro: os pontos de maior risco (não verificáveis aqui) são a criação da janela/contexto
core 3.3 por Pygame, o formato das chamadas do PyOpenGL real, MSAA e a compatibilidade PyOpenGL × NumPy 2.
