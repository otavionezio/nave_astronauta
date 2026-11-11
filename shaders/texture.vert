// Material de textura sem iluminação (HUD e visualização do mapa de profundidade).
layout(location = 0) in vec3 vertexPosition;
layout(location = 2) in vec2 vertexUV;
uniform mat4 projectionMatrix;
uniform mat4 viewMatrix;
uniform mat4 modelMatrix;
uniform vec2 repeatUV;
uniform vec2 offsetUV;
out vec2 UV;

void main()
{
    gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(vertexPosition, 1.0);
    UV = vertexUV * repeatUV + offsetUV;
}
