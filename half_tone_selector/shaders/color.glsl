const mat3 xy_to_xyz = mat3(
    1.0, 0.0,-1.0,
    0.0, 1.0,-1.0,
    0.0, 0.0, 1.0
);
const mat3 primaries_xy = mat3(
    0.64, 0.33, 1.0,
    0.30, 0.60, 1.0,
    0.15, 0.06, 1.0
);
const vec3 whitepoint_xy = vec3(0.3127, 0.3290, 1.0);
const mat3 primaries_xyz = transpose(xy_to_xyz * primaries_xy);
const vec3 whitepoint_xyz = xy_to_xyz * whitepoint_xy;
const vec3 coeff = whitepoint_xyz * inverse(primaries_xyz) / whitepoint_xyz.y;
const mat3 coeff_mat = mat3(
    coeff.x, 0.0, 0.0,
    0.0, coeff.y, 0.0,
    0.0, 0.0, coeff.z
);
const mat3 rgb_to_xyz_mat = coeff_mat * primaries_xyz;
const mat3 xyz_to_rgb_mat = inverse(rgb_to_xyz_mat);

vec3 rgb_to_xyz(vec3 rgb) {
    return rgb * rgb_to_xyz_mat;
}
vec3 xyz_to_rgb(vec3 xyz) {
    return xyz * xyz_to_rgb_mat;
}

const mat3 xyz_to_lms_mat = mat3(
    0.8189330101, 0.3618667424,-0.1288597137,
    0.0329845436, 0.9293118715, 0.0361456387,
    0.0482003018, 0.2643662691, 0.6338517070
);
const mat3 lms_to_xyz_mat = inverse(xyz_to_lms_mat);
const mat3 lms_to_oklab_mat = mat3(
    0.2104542553, 0.7936177850,-0.0040720468,
    1.9779984951,-2.4285922050, 0.4505937099,
    0.0259040371, 0.7827717662,-0.8086757660
);
const mat3 oklab_to_lms_mat = inverse(lms_to_oklab_mat);

vec3 xyz_to_oklab(vec3 xyz) {
    return pow(xyz * xyz_to_lms_mat, vec3(1.0/3.0)) * lms_to_oklab_mat;
}
vec3 oklab_to_xyz(vec3 lab) {
    return pow(lab * oklab_to_lms_mat, vec3(3.0)) * lms_to_xyz_mat;
}

vec3 rgb_to_oklab(vec3 rgb) {
    return xyz_to_oklab(rgb_to_xyz(rgb));
}
vec3 oklab_to_rgb(vec3 lab) {
    return xyz_to_rgb(oklab_to_xyz(lab));
}

vec3 rgb_to_srgb(vec3 linear_rgb) {
    return mix(
        1.055 * pow(linear_rgb, vec3(1.0/2.4)) - 0.055,
        12.92 * linear_rgb,
        step(linear_rgb, vec3(0.0031308)));
}

vec3 oklab_to_srgb(vec3 lab) {
    vec3 rgb = oklab_to_rgb(lab);
    vec3 clamped_rgb = clamp(rgb, 0.0, 1.0);
    vec3 srgb = rgb_to_srgb(clamped_rgb);
    return srgb;
}