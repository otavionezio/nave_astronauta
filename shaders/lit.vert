// Vertex shader dos materiais iluminados (Lambert e Phong) com suporte a sombra.
#include "common_shadow.glsl"

// localizações fixas: o mesmo VAO serve ao programa principal e ao DepthMaterial
layout(location = 0) in vec3 vertexPosition;
layout(location = 2) in vec2 vertexUV;
layout(location = 3) in vec3 vertexNormal;

uniform mat4 projectionMatrix;
uniform mat4 viewMatrix;
uniform mat4 modelMatrix;
uniform vec2 repeatUV;
uniform bool useShadow;
uniform Shadow shadow0;

out vec3 position;          // posição no MUNDO
out vec2 UV;
out vec3 normal;            // normal no MUNDO
out vec3 shadowPosition0;   // posição do vértice no clip space da LUZ

void main()
{
    vec4 worldPosition = modelMatrix * vec4(vertexPosition, 1.0);
    gl_Position = projectionMatrix * viewMatrix * worldPosition;

    position = worldPosition.xyz;
    UV = vertexUV * repeatUV;
    // matriz normal = inversa transposta de mat3(model): correta mesmo com escala não uniforme
    normal = normalize(transpose(inverse(mat3(modelMatrix))) * vertexNormal);

    shadowPosition0 = vec3(0.0);
    if (useShadow)
    {
        // mesma posição, mas vista pela câmera da luz (projeção ortográfica => w = 1)
        vec4 lightClip = shadow0.projectionMatrix * shadow0.viewMatrix * worldPosition;
        shadowPosition0 = vec3(lightClip);
    }
}
