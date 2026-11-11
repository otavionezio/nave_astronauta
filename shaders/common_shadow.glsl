// ---------------------------------------------------------------------------
// Struct Shadow: dados do shadow mapping (preenchidos pelo Renderer; ver
// core/uniform.py, caso "Shadow"). Incluído por lit.vert e lit.frag.
// ---------------------------------------------------------------------------
struct Shadow
{
    vec3 lightDirection;        // direção dos raios da luz que projeta a sombra
    mat4 projectionMatrix;      // projeção ORTOGRÁFICA da câmera da luz
    mat4 viewMatrix;            // view da câmera da luz (inversa da matriz da luz)
    sampler2D depthTexture;     // mapa de profundidade gerado no passe de sombra
    float strength;             // 0..1: fração da luz direta removida na sombra
    float bias;                 // viés mínimo da comparação de profundidade
    float slopeBias;            // viés extra proporcional a (1 - cos) da inclinação
    int pcf;                    // raio do filtro de vizinhança (0 = sombra dura)
};
