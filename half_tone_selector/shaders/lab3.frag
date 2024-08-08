#include "color.glsl"
#include "draw.glsl"

uniform vec2 u_resolution;
uniform vec3 lab_1;
uniform vec3 lab_2;
out vec4 out_color;

void main(void) {
    float s = u_resolution.x;
    float h2 = 0.5 * u_resolution.y / s;
    vec2 coord = gl_FragCoord.xy / s;

    vec3 color_1 = oklab_to_srgb(lab_1);
    vec3 color_2 = oklab_to_srgb(lab_2);
    vec2 lab_1_coord = vec2(lab_1.x, h2);
    vec2 lab_2_coord = vec2(lab_2.x, h2);
    vec3 outline_color_1 = (lab_1.x < 0.5) ? vec3(1.0) : vec3(0.0);
    vec3 outline_color_2 = (lab_2.x < 0.5) ? vec3(1.0) : vec3(0.0);

    vec3 lab = vec3(coord.x, lab_1.y, lab_1.z);
    vec3 rgb = oklab_to_rgb(lab);
    vec3 clamped_rgb = clamp(rgb, 0.0, 1.0);
    vec3 clamped_lab = rgb_to_oklab(clamped_rgb);
    vec3 target = rgb_to_srgb(clamped_rgb);

    float d = (rgb == clamped_rgb) ? 0.0 : distance(lab, clamped_lab);

    target = mix(target,
        (coord.x < 0.5) ? vec3(1.0) : vec3(0.0),
        outline(2.5*d, 0.0025, s) * 0.2);
    target = mix(target, color_2, circle(lab_2_coord, coord, h2*0.5, s));
    target = mix(target, color_1, circle(lab_1_coord, coord, h2*0.5, s));
    target = mix(target, outline_color_2, circle_outline(lab_2_coord, coord, h2*0.5, h2*0.02, s));
    target = mix(target, outline_color_1, circle_outline(lab_1_coord, coord, h2*0.5, h2*0.08, s));
    out_color = vec4(target, 1.0);
}