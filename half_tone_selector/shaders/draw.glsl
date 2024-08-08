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