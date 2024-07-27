uniform vec2 u_resolution;
uniform float u_lightness;
layout(location=0) out vec4 out_color;
layout(location=1) out float e;

vec3 oklab_to_linear_rgb(vec3 lab) {
    const mat3 m1 = mat3(
        1,  0.3963377774,  0.2158037573,
        1, -0.1055613458, -0.0638541728,
        1, -0.0894841775, -1.2914855480
    );
    const mat3 m2 = mat3(
         4.0767416621, -3.3077115913,  0.2309699292,
        -1.2684380046,  2.6097574011, -0.3413193965,
        -0.0041960863, -0.7034186147,  1.7076147010
    );
    return pow(lab * m1, vec3(3.0)) * m2;
}

vec3 linear_rgb_to_oklab(vec3 rgb) {
    const mat3 m1 = mat3(
        0.4122214708, 0.5363325363, 0.0514459929,
        0.2119034982, 0.6806995451, 0.1073969566,
        0.0883024619, 0.2817188376, 0.6299787005
    );
    const mat3 m2 = mat3(
        0.2104542553,  0.7936177850, -0.0040720468,
        1.9779984951, -2.4285922050,  0.4505937099,
        0.0259040371,  0.7827717662, -0.8086757660
    );
    return pow(rgb * m1, vec3(1.0/3.0)) * m2;
}

vec3 linear_rgb_to_rgb(vec3 linear_rgb) {
    return mix(
        1.055 * pow(linear_rgb, vec3(1.0/2.4)) - 0.055,
        12.92 * linear_rgb,
        step(linear_rgb, vec3(0.0031308)));
}

float outline(float r, float width, float scale) {
    float inner_edge = clamp(r * scale, 0.0, 1.0);
    float outer_edge = clamp((r-width) * scale, 0.0, 1.0);
    return inner_edge * (1.0 - outer_edge);
}

void main(void) {
    vec2 half_res = u_resolution / 2.0;
    float s = min(half_res.x, half_res.y);
    vec2 coord = (gl_FragCoord.xy - half_res) / s;

    vec3 lab = vec3(u_lightness, 0.4*coord.x, 0.4*coord.y);
    vec3 linear_rgb = oklab_to_linear_rgb(lab);
    vec3 clamped_rgb = clamp(linear_rgb, 0.0, 1.0);
    vec3 clamped_lab = linear_rgb_to_oklab(clamped_rgb);
    vec3 rgb = linear_rgb_to_rgb(clamped_rgb);

    float d = (linear_rgb == clamped_rgb) ? 0.0 : distance(lab, clamped_lab);

    vec3 clamp_line = mix(
        rgb,
        (u_lightness < 0.5) ? vec3(1.0) : vec3(0.0),
        outline(2.5*d, 0.0025, s) * 0.2);
    out_color = vec4(clamp_line, 1.0);
    e = ceil(clamp(d, 0.0, 1.0));
}