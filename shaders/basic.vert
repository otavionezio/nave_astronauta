// Material sem iluminação (cores de vértice / cor sólida): estrelas, brilho dos motores, marcas.
layout(location = 0) in vec3 vertexPosition;
layout(location = 1) in vec3 vertexColor;
uniform mat4 projectionMatrix;
uniform mat4 viewMatrix;
uniform mat4 modelMatrix;
out vec3 color;

void main()
{
    gl_Position = projectionMatrix * viewMatrix * modelMatrix * vec4(vertexPosition, 1.0);
    color = vertexColor;
}
