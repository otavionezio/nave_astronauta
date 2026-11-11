// Passe de sombra: só transforma o vértice para o clip space DA LUZ.
layout(location = 0) in vec3 vertexPosition;
uniform mat4 projectionMatrix;   // ortográfica da câmera da luz
uniform mat4 viewMatrix;         // view da câmera da luz
uniform mat4 modelMatrix;

void main()
{
    gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(vertexPosition, 1.0);
}
