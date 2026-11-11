// Fragment shader dos materiais iluminados: cor base * textura * iluminação,
// com sombra projetada por shadow mapping (comparação de profundidade).
#include "common_shadow.glsl"
#include "common_light.glsl"

uniform vec3 baseColor;
uniform bool useTexture;
uniform sampler2D baseTexture;
uniform bool useShadow;
uniform Shadow shadow0;

in vec3 position;
in vec2 UV;
in vec3 normal;
in vec3 shadowPosition0;
out vec4 fragColor;

// 1 se o fragmento está mais distante da luz do que o ponto guardado no mapa
float shadowTest(vec3 coord, float bias)
{
    float closestDistanceToLight = texture(shadow0.depthTexture, coord.xy).r;
    return (coord.z > closestDistanceToLight + bias) ? 1.0 : 0.0;
}

// Fração (0..1) do fragmento que está na SOMBRA PROJETADA de outro objeto.
float computeShadowAmount(vec3 N)
{
    if (!useShadow) return 0.0;

    // 1) a superfície precisa estar voltada para a luz (senão já está escura pelo N.L)
    float cosAngle = dot(N, -normalize(shadow0.lightDirection));
    if (cosAngle <= 0.0) return 0.0;

    // 2) clip space [-1,1] -> coordenada de textura / profundidade [0,1]
    vec3 coord = shadowPosition0 * 0.5 + 0.5;
    if (coord.x < 0.0 || coord.x > 1.0 || coord.y < 0.0 || coord.y > 1.0 || coord.z > 1.0)
        return 0.0;                         // fora do volume da câmera da luz

    // 3) viés: evita "acne" (autossombra por precisão); cresce em superfícies rasantes
    float bias = max(shadow0.slopeBias * (1.0 - cosAngle), shadow0.bias);

    // 4) compara a profundidade do fragmento com a do mapa (com PCF opcional)
    if (shadow0.pcf <= 0) return shadowTest(coord, bias);

    vec2 texel = 1.0 / vec2(textureSize(shadow0.depthTexture, 0));
    float sum = 0.0;
    int n = shadow0.pcf;
    for (int x = -n; x <= n; x++)
        for (int y = -n; y <= n; y++)
            sum += shadowTest(vec3(coord.xy + vec2(x, y) * texel, coord.z), bias);
    return sum / float((2 * n + 1) * (2 * n + 1));
}

void main()
{
    vec4 color = vec4(baseColor, 1.0);
    if (useTexture)
        color *= texture(baseTexture, UV);

    vec3 N = normalize(normal);
    float visibility = 1.0 - (useShadow ? shadow0.strength : 0.0) * computeShadowAmount(N);

    vec3 total = vec3(0.0);
    total += lightCalc(light0, position, N, visibility);
    total += lightCalc(light1, position, N, visibility);
    total += lightCalc(light2, position, N, visibility);
    total += lightCalc(light3, position, N, visibility);

    fragColor = vec4(color.rgb * total, color.a);
}
