#version 430

in vec2 in_vert;
in vec2 in_texcoord;

out vec2 vert_tex;

void main(){
     vert_tex = in_texcoord;
     gl_Position = vec4(in_vert, 0.0, 1.0);
}
