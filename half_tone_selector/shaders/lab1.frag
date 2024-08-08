#include "color.glsl"
#include "draw.glsl"

uniform vec2 u_resolution;
uniform float u_lightness;
layout(location=0) out vec4 out_color;
layout(location=1) out float e;

void main(void) {
    vec2 half_res = u_resolution / 2.0;
    float s = min(half_res.x, half_res.y);
    vec2 coord = (gl_FragCoord.xy - half_res) / s;

    vec3 lab = vec3(u_lightness, 0.4*coord.x, 0.4*coord.y);
    vec3 rgb = oklab_to_rgb(lab);
    vec3 clamped_rgb = clamp(rgb, 0.0, 1.0);
    vec3 clamped_lab = rgb_to_oklab(clamped_rgb);
    vec3 srgb = rgb_to_srgb(clamped_rgb);

    float d = (rgb == clamped_rgb) ? 0.0 : distance(lab, clamped_lab);

    vec3 clamp_line = mix(
        srgb,
        (u_lightness < 0.5) ? vec3(1.0) : vec3(0.0),
        outline(2.5*d, 0.0025, s) * 0.2);
    out_color = vec4(clamp_line, 1.0);
    e = ceil(clamp(d, 0.0, 1.0));
}