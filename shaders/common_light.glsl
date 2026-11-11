// ---------------------------------------------------------------------------
// Iluminação: struct Light + lightCalc (ambiente, difusa e, opcionalmente,
// especular de Phong). Incluído por lit.frag.
//   - define USE_SPECULAR => modelo de Phong; sem ele => modelo de Lambert.
// ---------------------------------------------------------------------------
struct Light
{
    int lightType;      // 1 = ambiente, 2 = direcional, 3 = pontual
    vec3 color;
    vec3 direction;     // luz direcional: para onde os raios apontam (mundo)
    vec3 position;      // luz pontual (mundo)
    vec3 attenuation;   // coeficientes (a, b, c) de 1 / (a + b*d + c*d^2)
};

uniform Light light0;
uniform Light light1;
uniform Light light2;
uniform Light light3;

uniform vec3 viewPosition;        // posição da câmera (mundo): só o especular usa
uniform float specularStrength;
uniform float shininess;

// directionalVisibility: 1 = luz solar plena; < 1 dentro da sombra projetada.
// A sombra só reduz a luz DIRETA direcional (ambiente e pontuais não são afetadas).
vec3 lightCalc(Light light, vec3 pointPosition, vec3 pointNormal, float directionalVisibility)
{
    float ambient = 0.0;
    float diffuse = 0.0;
    float specular = 0.0;
    float attenuation = 1.0;
    vec3 lightDirection = vec3(0.0);

    if (light.lightType == 1)            // ambiente
    {
        ambient = 1.0;
    }
    else if (light.lightType == 2)       // direcional
    {
        lightDirection = normalize(light.direction);
    }
    else if (light.lightType == 3)       // pontual
    {
        lightDirection = normalize(pointPosition - light.position);
        float d = length(light.position - pointPosition);
        attenuation = 1.0 / (light.attenuation[0] + light.attenuation[1] * d
                             + light.attenuation[2] * d * d);
    }

    if (light.lightType > 1)
    {
        // SOMBREAMENTO da superfície (lei de Lambert): cos do ângulo entre a normal
        // e a direção PARA a luz; negativo => superfície de costas para a luz.
        pointNormal = normalize(pointNormal);
        diffuse = max(dot(pointNormal, -lightDirection), 0.0);
        diffuse *= attenuation;
#ifdef USE_SPECULAR
        if (diffuse > 0.0)
        {
            vec3 viewDirection = normalize(viewPosition - pointPosition);
            vec3 reflectDirection = reflect(lightDirection, pointNormal);
            specular = max(dot(viewDirection, reflectDirection), 0.0);
            specular = specularStrength * pow(specular, shininess) * attenuation;
        }
#endif
        if (light.lightType == 2)
        {
            diffuse *= directionalVisibility;
            specular *= directionalVisibility;
        }
    }
    return light.color * (ambient + diffuse + specular);
}
