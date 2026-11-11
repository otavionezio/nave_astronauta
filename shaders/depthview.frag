// Depuração: mostra o mapa de sombras (canal R) em tons de cinza, com contraste realçado.
uniform vec3 baseColor;
uniform sampler2D baseTexture;
in vec2 UV;
out vec4 fragColor;

void main()
{
    float d = texture(baseTexture, UV).r;
    float v = clamp((d - 0.3) / 0.7, 0.0, 1.0);
    fragColor = vec4(vec3(v) * baseColor, 1.0);
}
