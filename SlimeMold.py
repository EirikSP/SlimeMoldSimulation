import moderngl_window as mglw
import moderngl
import numpy as np
import imgui
from moderngl_window.integrations.imgui import ModernglWindowRenderer



class config:
    width = 1920.0
    height = 1080.0

    decay_rate = 5.0
    diffuse_speed = 10.0
    particle_speed  = 50.0
    turn_range = 50
    sensor_dist = 10.0
    sensor_angle = np.pi/4
    sensor_size = 1




def generate_particles(N, width, height, r):
    R = np.random.random(N)
    pos_angle = np.random.random(N)*2.0*np.pi
    x = width + r*R*np.cos(pos_angle)
    y = height + r*R*np.sin(pos_angle)
    return np.c_[x, y, np.pi + pos_angle].astype('f4')



class App(mglw.WindowConfig):
    window_size = 1920, 1080
    resource_dir = "SlimeMold"
    aspect_ratio = None
    vsync = False
    gl_version = (4, 3)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        imgui.create_context()
        self.imgui = ModernglWindowRenderer(self.wnd)

        self.particle_count = 1000000
        self.addPart = False

        self.updateSpeed = 1/60
        self.last_time = 0.0

        self.width, self.height = (int(config.width), int(config.height))

        self.render_program = self.load_program(vertex_shader='vertex_shader.glsl', fragment_shader='fragment_shader.glsl')
        self.render_program['srcTex'] = 0

        self.particles = generate_particles(self.particle_count, self.width/3, self.height/3, 200.0)

        self.particle_buffer = self.ctx.buffer(data=self.particles.tobytes(), dynamic=True)
        self.next_batch = self.ctx.buffer(reserve=self.particles.nbytes, dynamic=True)

        self.particle_program = self.load_program(vertex_shader='particles.glsl', varyings=['out_pos', 'out_angle'])
        self.particle_step = self.ctx.vertex_array(self.particle_program, [(self.particle_buffer, '2f 1f', 'in_pos', 'angle')])

        self.texture_read = self.ctx.texture((self.width, self.height), components=1, dtype='f4')
        self.texture_read.filter = moderngl.NEAREST, moderngl.NEAREST
        self.texture_read.repeat_x, self.texture_read.repeat_y = False, False

        self.texture_write = self.ctx.texture((self.width, self.height), components=1, dtype='f4')
        self.texture_write.filter = moderngl.NEAREST, moderngl.NEAREST
        self.texture_write.repeat_x, self.texture_write.repeat_y = False, False
        
        self.texture_buffer = self.ctx.buffer(reserve=np.zeros((self.height, self.width), dtype='f4').nbytes)
        
        self.texture_read.bind_to_image(0, read=True, write=False)
        self.texture_write.bind_to_image(1, write=True, read= False)

        self.decay_program = self.load_program('decay.glsl')
        self.decay_program['srcTex'] = 0
        self.decay = self.ctx.vertex_array(self.decay_program, [])
        
        self.update_uniforms()

        self.display_buffer = self.ctx.buffer(np.array([
            # x    y     u  v
            -1.0, -1.0,  0.0, 0.0,  # lower left
            -1.0,  1.0,  0.0, 1.0,  # upper left
            1.0,   1.0,  1.0, 1.0, # upper right
            1.0,  -1.0,  1.0, 0.0,  # lower right
              
        ], dtype="f4"))


        self.render_array = self.ctx.vertex_array(self.render_program, [(self.display_buffer, '2f 2f', 'in_vert', 'in_texcoord')])

        #self.rendering = self.ctx.vertex_array(self.render_program, [(self.particle_buffer, '2f 2x4', 'in_vert')])
    
        
        
    def update_uniforms(self):
        self.particle_program['width'] = config.width
        self.particle_program['height'] = config.height
        self.particle_program['sensor_dist'] = config.sensor_dist
        self.particle_program['sensor_angle'] = config.sensor_angle
        self.particle_program['particle_speed'] = config.particle_speed
        self.particle_program['turn_range'] = config.turn_range
        self.particle_program['sensor_size'] = config.sensor_size


        self.decay_program['diffuse_speed'] = config.diffuse_speed
        self.decay_program['decay_rate'] = config.decay_rate
        self.decay_program['width'] = self.width
        

    def set_uniform(self, u_name, u_value):
        try:
            self.particle_program[u_name] = u_value
        except:
            print(f'uniform: {u_name} - not used in shader')


    def restart_sim(self):
        self.particles = generate_particles(self.particle_count, self.width/2, self.height/2, 200.0)


        self.particle_buffer = self.ctx.buffer(data=self.particles.tobytes(), dynamic=True)
        self.next_batch = self.ctx.buffer(reserve=self.particles.nbytes, dynamic=True)
        self.particle_step = self.ctx.vertex_array(self.particle_program, [(self.particle_buffer, '2f 1f', 'in_pos', 'angle')])
        self.texture_buffer = self.ctx.buffer(reserve=np.zeros((self.height, self.width), dtype='f4').nbytes)
        self.texture_read.write(self.texture_buffer)


    

    
    
    def render(self, time: float, frame_time: float):
        
        self.ctx.clear()
        
        self.texture_read.use(location=0)
        
        self.render_array.render(moderngl.TRIANGLE_FAN)
        
        
        #self.set_uniform('width', self.width)
        #self.set_uniform('height', self.height)
        

        #self.rendering.render(moderngl.POINTS, vertices=self.particle_count)
        
        self.texture_read.bind_to_image(0, write=False, read= True)
        self.texture_write.bind_to_image(1, write=True, read= False)

        

        self.particle_step.transform(self.next_batch,  vertices=self.particle_count)
        self.particle_buffer.write(self.next_batch.read())
        self.texture_read = self.texture_write
        
        
        self.decay.transform(self.texture_buffer, vertices=self.width * self.height)
        self.texture_read.write(self.texture_buffer)

        self.render_ui()


        

    
    def render_ui(self):
        imgui.new_frame()

        if imgui.begin("Settings"):
            imgui.push_item_width(imgui.get_window_width()*0.25)

            changed = False
            c, config.decay_rate = imgui.slider_float(
                "Decay Rate", config.decay_rate, 0.0, 8.0
            )
            changed = changed or c
            c, config.diffuse_speed = imgui.slider_float(
                "Diffusion Speed", config.diffuse_speed, 0.0, 60.0
            )
            changed = changed or c
            c, config.particle_speed = imgui.slider_float(
                "Particle Speed", config.particle_speed, 0.0, 100.0
            )
            changed = changed or c
            c, config.turn_range = imgui.slider_float(
                "Turning Range", config.turn_range, 0.0, 100.0
            )
            changed = changed or c
            c, config.sensor_dist = imgui.slider_float(
                "Sensor Distance", config.sensor_dist, 0.0, 50.0
            )
            changed = changed or c
            c, config.sensor_angle = imgui.slider_float(
                "Sensor Angle", config.sensor_angle, 0.0, np.pi*2
            )
            changed = changed or c
            c, config.sensor_size = imgui.slider_int(
                "Sensor Size", config.sensor_size, 0, 5
            )
            changed = changed or c
            if changed:
                self.update_uniforms()
            
            if imgui.button("Restart Simulation"):
                 self.restart_sim()
            
            imgui.pop_item_width()



        imgui.end()

        imgui.render()
        self.imgui.render(imgui.get_draw_data())
    
    def mouse_press_event(self, x, y, button):
        new_particles = generate_particles(10000, x, self.height - y, 100.0)
        self.particle_buffer.write(data=new_particles, offset=self.particle_count*3)
        self.particle_count += 10000
        self.imgui.mouse_press_event(x, y, button)

    def key_event(self, key, action, modifiers):
        keys = self.wnd.keys

        self.imgui.key_event(key, action, modifiers)


    def mouse_position_event(self, x, y, dx, dy):
        self.imgui.mouse_position_event(x, y, dx, dy)

    def mouse_drag_event(self, x, y, dx, dy):
        self.imgui.mouse_drag_event(x, y, dx, dy)

    def mouse_scroll_event(self, x_offset, y_offset):
        self.imgui.mouse_scroll_event(x_offset, y_offset)

    

    def mouse_release_event(self, x: int, y: int, button: int):
        self.imgui.mouse_release_event(x, y, button)
        

        
        


if __name__=='__main__':
    mglw.run_window_config(App)