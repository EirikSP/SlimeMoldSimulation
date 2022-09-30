#version 430

uniform sampler2D srcTex;
//layout(r8, location=0) restrict readonly uniform image2D srcTex;

out float intensity;

uniform float decay_rate;
uniform int width;



float tex(int x, int y){
    //return imageLoad(srcTex, ivec2(x, y)).r;
    return texelFetch(srcTex, ivec2(x, y), 0).r;
}

float average(int x, int y){
    float total = 0.0;

    total += tex(x + 1, y + 0);
    total += tex(x - 1, y + 0);
    total += tex(x + 0, y + 1);
    total += tex(x + 0, y - 1);
    total += tex(x + 1, y + 1);
    total += tex(x - 1, y - 1);
    total += tex(x + 1, y - 1);
    total += tex(x - 1, y + 1);

    return total;
}

float dt = 0.0166;
uniform float diffuse_speed;


void main(){
    int width = width;
    ivec2 pos = ivec2(gl_VertexID%width, gl_VertexID/width);
    float avg_pixel = (average(pos.x, pos.y) + tex(pos.x, pos.y))/9.0;
    float pix = tex(pos.x, pos.y);
    float pixel = mix(pix, avg_pixel, diffuse_speed*dt);
    intensity = max(0.0, pixel - decay_rate*dt);

}