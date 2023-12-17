import moderngl
import numpy as np
from moderngl_window import WindowConfig, run_window_config
import sys

from collections import deque

class RollingAverage:
    def __init__(self, length):
        self.history = deque(maxlen=length)
        self.sum = 0

    def update(self, value):
        self.history.append(value)
        return self.average()
    
    def average(self):
        if len(self.history) == 0:
            return 0
        return sum(self.history) / len(self.history)
        
class Example(WindowConfig):
    gl_version = (4, 1)
    window_size = (512, 512)
    title = "Porter-Duff Compositing Example"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.vertex_shader = '''
            #version 410 core
            in vec2 in_vert;
            void main() {
                gl_Position = vec4(in_vert, 0.0, 1.0);
            }
        '''

        # Compositor programs
        self.compositors = {}
        self.compositors["clear"] = self.ctx.program(
            vertex_shader=self.vertex_shader,
            fragment_shader='''
                #version 410 core
                out vec4 fragColor;
                void main() {
                    fragColor = vec4(0.0, 0.0, 0.0, 0.0);
                }
            ''',
        )
        self.compositors["copy"] = self.ctx.program(
            vertex_shader=self.vertex_shader,
            fragment_shader='''
                #version 410 core
                uniform sampler2D Texture1;
                out vec4 fragColor;
                void main() {
                    fragColor = texture(Texture1, gl_FragCoord.xy / 512.0);
                }
            ''',
        )
        self.compositors["source"] = self.ctx.program(
            vertex_shader=self.vertex_shader,
            fragment_shader='''
                #version 410 core
                uniform sampler2D Texture1;
                out vec4 fragColor;
                void main() {
                    fragColor = texture(Texture1, gl_FragCoord.xy / 512.0);
                }
            ''',
        )
        self.compositors["destination"] = self.ctx.program(
            vertex_shader=self.vertex_shader,
            fragment_shader='''
                #version 410 core
                uniform sampler2D Texture2;
                out vec4 fragColor;
                void main() {
                    fragColor = texture(Texture2, gl_FragCoord.xy / 512.0);
                }
            ''',
        )
        self.compositors["source-over"] = self.ctx.program(
            vertex_shader=self.vertex_shader,
            fragment_shader='''
                #version 410 core
                uniform sampler2D Texture1;
                uniform sampler2D Texture2;
                out vec4 fragColor;
                void main() {
                    vec4 srcColor = texture(Texture1, gl_FragCoord.xy / 512.0);
                    vec4 dstColor = texture(Texture2, gl_FragCoord.xy / 512.0);
                    fragColor = srcColor + dstColor * (1.0 - srcColor.a);
                }
            ''',
        )
        self.compositors["destination-over"] = self.ctx.program(
            vertex_shader=self.vertex_shader,
            fragment_shader='''
                #version 410 core
                uniform sampler2D Texture1;
                uniform sampler2D Texture2;
                out vec4 fragColor;
                void main() {
                    vec4 srcColor = texture(Texture1, gl_FragCoord.xy / 512.0);
                    vec4 dstColor = texture(Texture2, gl_FragCoord.xy / 512.0);
                    fragColor = dstColor + srcColor * (1.0 - dstColor.a);
                }
            ''',
        )
        self.compositors["source-in"] = self.ctx.program(
            vertex_shader=self.vertex_shader,
            fragment_shader='''
                #version 410 core
                uniform sampler2D Texture1;
                uniform sampler2D Texture2;
                out vec4 fragColor;
                void main() {
                    vec4 srcColor = texture(Texture1, gl_FragCoord.xy / 512.0);
                    vec4 dstColor = texture(Texture2, gl_FragCoord.xy / 512.0);
                    fragColor = srcColor * dstColor.a;
                }
            ''',
        )
        self.compositors["destination-in"] = self.ctx.program(
            vertex_shader=self.vertex_shader,
            fragment_shader='''
                #version 410 core
                uniform sampler2D Texture1;
                uniform sampler2D Texture2;
                out vec4 fragColor;
                void main() {
                    vec4 srcColor = texture(Texture1, gl_FragCoord.xy / 512.0);
                    vec4 dstColor = texture(Texture2, gl_FragCoord.xy / 512.0);
                    fragColor = dstColor * srcColor.a;
                }
            ''',
        )
        self.compositors["source-out"] = self.ctx.program(
            vertex_shader=self.vertex_shader,
            fragment_shader='''
                #version 410 core
                uniform sampler2D Texture1;
                uniform sampler2D Texture2;
                out vec4 fragColor;
                void main() {
                    vec4 srcColor = texture(Texture1, gl_FragCoord.xy / 512.0);
                    vec4 dstColor = texture(Texture2, gl_FragCoord.xy / 512.0);
                    fragColor = srcColor * (1.0 - dstColor.a);
                }
            ''',
        )
        self.compositors["destination-out"] = self.ctx.program(
            vertex_shader=self.vertex_shader,
            fragment_shader='''
                #version 410 core
                uniform sampler2D Texture1;
                uniform sampler2D Texture2;
                out vec4 fragColor;
                void main() {
                    vec4 srcColor = texture(Texture1, gl_FragCoord.xy / 512.0);
                    vec4 dstColor = texture(Texture2, gl_FragCoord.xy / 512.0);
                    fragColor = dstColor * (1.0 - srcColor.a);
                }
            ''',
        )
        self.compositors["source-atop"] = self.ctx.program(
            vertex_shader=self.vertex_shader,
            fragment_shader='''
                #version 410 core
                uniform sampler2D Texture1;
                uniform sampler2D Texture2;
                out vec4 fragColor;
                void main() {
                    vec4 srcColor = texture(Texture1, gl_FragCoord.xy / 512.0);
                    vec4 dstColor = texture(Texture2, gl_FragCoord.xy / 512.0);
                    fragColor = srcColor * dstColor.a + dstColor * (1.0 - srcColor.a);
                }
            ''',
        )
        self.compositors["destination-atop"] = self.ctx.program(
            vertex_shader=self.vertex_shader,
            fragment_shader='''
                #version 410 core
                uniform sampler2D Texture1;
                uniform sampler2D Texture2;
                out vec4 fragColor;
                void main() {
                    vec4 srcColor = texture(Texture1, gl_FragCoord.xy / 512.0);
                    vec4 dstColor = texture(Texture2, gl_FragCoord.xy / 512.0);
                    fragColor = dstColor * srcColor.a + srcColor * (1.0 - dstColor.a);
                }
            ''',
        )
        self.compositors["xor"] = self.ctx.program(
            vertex_shader=self.vertex_shader,
            fragment_shader='''
                #version 410 core
                uniform sampler2D Texture1;
                uniform sampler2D Texture2;
                out vec4 fragColor;
                void main() {
                    vec4 srcColor = texture(Texture1, gl_FragCoord.xy / 512.0);
                    vec4 dstColor = texture(Texture2, gl_FragCoord.xy / 512.0);
                    fragColor = srcColor * (1.0 - dstColor.a) + dstColor * (1.0 - srcColor.a);
                }
            ''',
        )

        # Compile shaders
        self.prog1 = self.ctx.program(
            vertex_shader=self.vertex_shader,
            fragment_shader='''
                #version 410 core
                out vec4 fragColor;
                void main() {
                    float gradient = gl_FragCoord.y / 512.0;
                    fragColor = vec4(0.0, 0.0, 1.0, gradient);
                }
            ''',
        )
        self.prog2 = self.ctx.program(
            vertex_shader=self.vertex_shader,
            fragment_shader='''
                #version 410 core
                out vec4 fragColor;
                void main() {
                    float x = gl_FragCoord.x / 256.0;
                    fragColor = vec4(x, 0.0, 0.0, 1.0);
                }
            ''',
        )

        # Vertex data
        vertices = np.array([
            -1.0, -1.0,
             1.0, -1.0,
            -1.0,  1.0,
             1.0,  1.0,
        ], dtype='f4')

        # Create vertex buffer
        vbo = self.ctx.buffer(vertices)

        # Create vertex array objects
        self.vao1 = self.ctx.simple_vertex_array(self.prog1, vbo, 'in_vert')
        self.vao2 = self.ctx.simple_vertex_array(self.prog2, vbo, 'in_vert')
        for name, pgm in self.compositors.items():
            vao = self.ctx.simple_vertex_array(pgm, vbo, 'in_vert')
            self.compositors[name] = {
                'vao': vao,
                'pgm': pgm,
            }

        # Offscreen framebuffers for the intermediate shaders
        self.fbo1 = self.ctx.framebuffer(color_attachments=[self.ctx.texture(self.window_size, 4)])
        self.fbo2 = self.ctx.framebuffer(color_attachments=[self.ctx.texture(self.window_size, 4)])

        # Define a variable to select the current compositor
        self.current_compositor = 'destination'

        self.framerate = RollingAverage(length=64)

    def render(self, time, frame_time):
        avg = self.framerate.update(frame_time)
        sys.stdout.write('\r')
        sys.stdout.flush()
        sys.stdout.write(f'fps: {1/avg:.2f}')
        sys.stdout.flush()

        # Render to the first framebuffer
        self.fbo1.use()
        self.vao1.render(moderngl.TRIANGLE_STRIP)

        # Render to the second framebuffer
        self.fbo2.use()
        self.vao2.render(moderngl.TRIANGLE_STRIP)

        # Bind the textures from both framebuffers
        self.fbo1.color_attachments[0].use(location=0)
        self.fbo2.color_attachments[0].use(location=1)

        # Use the selected compositor for final rendering
        compositor = self.compositors[self.current_compositor]
        program = compositor['pgm']
        virtual_array_object = compositor['vao']

        # Conditionally bind uniforms
        if 'Texture1' in program:
            program['Texture1'].value = 0
        if 'Texture2' in program:
            program['Texture2'].value = 1

        self.ctx.screen.use()
        virtual_array_object.render(moderngl.TRIANGLE_STRIP)


        # # Debugging: render the intermediate framebuffers
        # self.ctx.screen.use()
        # self.vao1.render(moderngl.TRIANGLE_STRIP)

# Run the application
run_window_config(Example)
