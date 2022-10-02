#version 430

in vec2 vert_tex;

uniform sampler2D srcTex;

out vec4 fragColor;



void main(){
    vec3 col = vec3(1.0, 0.0, 0.0)*texture(srcTex, vert_tex).r;
    fragColor = vec4(col, 1.0);
}