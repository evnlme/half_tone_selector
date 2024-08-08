#include "color.glsl"
#include "draw.glsl"

uniform vec2 u_resolution;
uniform vec3 lab_1;
uniform vec3 lab_2;
uniform sampler2D pattern;
uniform sampler2D e;
out vec4 out_color;

void main(void) {
    vec2 half_res = u_resolution / 2.0;
    float s = min(half_res.x, half_res.y);
    vec2 coord = (gl_FragCoord.xy - half_res) / s;

    vec3 color_1 = oklab_to_srgb(lab_1);
    vec3 color_2 = oklab_to_srgb(lab_2);
    vec2 lab_1_coord = lab_1.yz / 0.4;
    vec2 lab_2_coord = lab_2.yz / 0.4;
    vec3 outline_color = (lab_1.x < 0.5) ? vec3(1.0) : vec3(0.0);
    float r1 = circle_outline(vec2(0.0), coord, length(lab_1_coord), 0.0025, s);
    float r2 = circle_outline(vec2(0.0), coord, length(lab_2_coord), 0.0025, s);

    vec3 target = texture(pattern, gl_FragCoord.xy / u_resolution).xyz;
    target = mix(target, outline_color, max(r1, r2));
    target = mix(target, color_1, 1.0-circle(vec2(0.0), coord, 0.333/0.4, s));
    target = mix(target, color_2, circle(lab_2_coord, coord, 0.1, s));
    target = mix(target, color_1, circle(lab_1_coord, coord, 0.1, s));
    target = mix(target, outline_color, circle_outline(lab_2_coord, coord, 0.1, 0.005, s));
    target = mix(target, outline_color, circle_outline(lab_1_coord, coord, 0.1, 0.0125, s));
    out_color = vec4(target, 1.0);
}