// Passe de sombra: grava a profundidade (0 = perto da luz, 1 = longe) na textura R32F.
out vec4 fragColor;
void main()
{
    float z = gl_FragCoord.z;
    fragColor = vec4(z, z, z, 1.0);
}
