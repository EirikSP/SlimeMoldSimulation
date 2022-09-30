#version 430

layout(r32f, location=1) restrict writeonly uniform image2D destTex;
layout(r32f, location=0) restrict readonly uniform image2D srcTex;

//uniform sampler2D srcTex;

#define PI 3.141592653


in vec2 in_pos;
in float angle;

out vec2 out_pos;
out float out_angle;

uniform float width;
uniform float height;

float dt = 0.0166;
uniform float particle_speed = 0.3;
uniform float turn_range = 100.0;
uniform float sensor_dist = 1.0;
uniform float sensor_angle = PI/4.0;
uniform int sensor_size = 2;


float random (vec2 st) {
    return fract(sin(dot(st.xy,vec2(12.9898,78.233)))*43758.5453123);
}

float get_fermone(ivec2 ipos){
    return imageLoad(srcTex, ipos).r;
    //return texelFetch(srcTex, ipos, 0).r;
}


void write_slime(vec2 pos){
    imageStore(destTex, ivec2(pos.x, pos.y), vec4(1.0));
}

float direction_change(float left, float center, float right){
    if(center - left > 0.0001 && center - right > 0.0001){
        return 0.0;
    }
    if (center - left < -0.0001 && center - right < -0.0001){
        return (random(in_pos) - 0.5)*2.0*turn_range*dt;
    }
    if (right - left < -0.0001){
        return (1.0)*turn_range*dt;
    }
    if (right - left > 0.0001){
        return (random(in_pos))*turn_range*(-1.0)*dt;
    }
    return 0.0;
}

float sens(vec2 position , float angl_off, float len){
    vec2 sens_pos = len*vec2((cos(angle + angl_off)), (sin(angle + angl_off)));
    ivec2 center_sens = ivec2(position.x, position.y) + ivec2(sens_pos.x, sens_pos.y);
    float sum = 0.0;
    float n = 0.0;
    for(int xOffset=-sensor_size; xOffset<=sensor_size; xOffset++){
        for(int yOffset=-sensor_size; yOffset<=sensor_size; yOffset++){
            ivec2 cell = center_sens + ivec2(xOffset, yOffset);

            if(cell.x >= 0 && cell.x <= width && cell.y >= 0 && cell.y <= height){
                sum += get_fermone(cell);
                n += 1.0;
            }
        }
    }

    return sum/n;

}


float get_turn(vec2 pos, float angle){
    float left = sens(pos, sensor_angle, sensor_dist);
    float center = sens(pos, 0.0, sensor_dist);
    float right = sens(pos, -sensor_angle, sensor_dist);
    



    return direction_change(left, center, right);
}


void main(){
    out_angle = angle + get_turn(in_pos, angle);
    vec2 in_vel = particle_speed*vec2(cos(out_angle), sin(out_angle));
    out_pos = vec2(in_pos.x + in_vel.x*dt, in_pos.y + in_vel.y*dt);
    
    
    if(out_pos.x >= width){
        out_pos.x = width - 1.0;
        out_angle = random(out_pos)*2*PI;
    }
    if(out_pos.x <= 0.0 ){
        out_pos.x = 1.0;
        out_angle = random(out_pos)*2*PI;
    }
    if(out_pos.y >= height){
        out_pos.y = height- 1.0;
        out_angle = random(out_pos)*2*PI;
    }
    if(out_pos.y <= 0.0 ){
        out_pos.y = 1.0;
        out_angle = random(out_pos)*2*PI;
    }
    write_slime(out_pos);
}