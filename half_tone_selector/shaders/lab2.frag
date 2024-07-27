uniform vec2 u_resolution;
uniform vec3 lab_1;
uniform vec3 lab_2;
uniform sampler2D pattern;
uniform sampler2D e;
out vec4 out_color;

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

vec3 linear_rgb_to_rgb(vec3 linear_rgb) {
    return mix(
        1.055 * pow(linear_rgb, vec3(1.0/2.4)) - 0.055,
        12.92 * linear_rgb,
        step(linear_rgb, vec3(0.0031308)));
}

vec3 oklab_to_rgb(vec3 lab) {
    vec3 linear_rgb = oklab_to_linear_rgb(lab);
    vec3 clamped_rgb = clamp(linear_rgb, 0.0, 1.0);
    vec3 rgb = linear_rgb_to_rgb(clamped_rgb);
    return rgb;
}

float outline(float r, float width, float scale) {
    float inner_edge = clamp(r * scale, 0.0, 1.0);
    float outer_edge = clamp((r-width) * scale, 0.0, 1.0);
    return inner_edge * (1.0 - outer_edge);
}

float circle(vec2 pos, vec2 coord, float radius, float scale) {
    float dist = distance(pos, coord);
    return 1.0 - clamp((dist-radius) * scale, 0.0, 1.0);
}

float circle_outline(vec2 pos, vec2 coord, float radius, float width, float scale) {
    float dist = distance(pos, coord);
    return outline(dist-radius, width, scale);
}

void main(void) {
    vec2 half_res = u_resolution / 2.0;
    float s = min(half_res.x, half_res.y);
    vec2 coord = (gl_FragCoord.xy - half_res) / s;

    vec3 color_1 = oklab_to_rgb(lab_1);
    vec3 color_2 = oklab_to_rgb(lab_2);
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