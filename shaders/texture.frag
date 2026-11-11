uniform vec3 baseColor;
uniform sampler2D baseTexture;
in vec2 UV;
out vec4 fragColor;

void main()
{
    vec4 color = vec4(baseColor, 1.0) * texture(baseTexture, UV);
    if (color.a < 0.01)
        discard;
    fragColor = color;
}
