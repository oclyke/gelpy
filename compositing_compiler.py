import moderngl
import numpy as np
from moderngl_window import WindowConfig, run_window_config
import sys

from collections import deque

COMPOSITOR_DICTIONARY = {
    'clear': '''
        fragColor = vec4(0.0, 0.0, 0.0, 0.0);
    ''',
    'copy': '''
        fragColor = srcColor;
    ''',
    'source': '''
        fragColor = srcColor;
    ''',
    'destination': '''
        fragColor = dstColor;
    ''',
    'source-over': '''
        fragColor = srcColor + dstColor * (1.0 - srcColor.a);
    ''',
    'destination-over': '''
        fragColor = dstColor + srcColor * (1.0 - dstColor.a);
    ''',
    'source-in': '''
        fragColor = srcColor * dstColor.a;
    ''',
    'destination-in': '''
        fragColor = dstColor * srcColor.a;
    ''',
    'source-out': '''
        fragColor = srcColor * (1.0 - dstColor.a);
    ''',
    'destination-out': '''
        fragColor = dstColor * (1.0 - srcColor.a);
    ''',
    'source-atop': '''
        fragColor = srcColor * dstColor.a + dstColor * (1.0 - srcColor.a);
    ''',
    'destination-atop': '''
        fragColor = dstColor * srcColor.a + srcColor * (1.0 - dstColor.a);
    ''',
    'xor': '''
        fragColor = srcColor * (1.0 - dstColor.a) + dstColor * (1.0 - srcColor.a);
    ''',
}

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

class CompositionSpecification:
    """
    Compositor program assembles snippets of OpenGL code into a single
    shader program.

    In this simple example we specify a pipeline with only:
    - a source texture program
    - a destination texture program
    - a compositing program

    For the time being each of the inputs must work in the same environment.

    Source Snippet:
    - Should populate the SourceTexture uniform

    Destination Snippet:
    - Should populate the DestinationTexture uniform

    Compositing Snippet:
    - Should combine the source and destination textures into a single output
      using the fragColor output variable
    """
    def __init__(self, context, source, destination, compositing):
        self.ctx = context
        self.source = source
        self.destination = destination
        self.compositing = compositing
    
    def compile(self):
        """
        Compile the compositor program
        """
        vertex_shader = '''
            #version 410 core
            in vec2 in_vert;
            void main() {
                gl_Position = vec4(in_vert, 0.0, 1.0);
            }
        '''

        fragment_shader = f'''
            #version 410 core
            vec4 srcColor;
            vec4 dstColor;
            out vec4 fragColor;
            void main() {{
                {{
                    {self.source}
                }}
                {{
                    {self.destination}
                }}
                {{
                    {self.compositing}
                }}
            }}
        '''

        return self.ctx.program(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader,
        )


class Example(WindowConfig):
    gl_version = (4, 1)
    window_size = (512, 512)
    title = "Porter-Duff Compositing Example (Compiled)"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_compositor = 'source-over'

        self.framerate = RollingAverage(length=64)

        self.specification = CompositionSpecification(
            self.ctx,
            source='''
                float y = gl_FragCoord.y / 512.0;
                srcColor = vec4(0.0, 0.0, y, 0.5);
            ''',
            destination='''
                float x = gl_FragCoord.x / 512.0;
                dstColor = vec4(x, 0.0, 0.0, 0.5);
            ''',
            compositing=COMPOSITOR_DICTIONARY[self.current_compositor],
        )
        self.program = self.specification.compile()

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
        self.vao = self.ctx.simple_vertex_array(self.program, vbo, 'in_vert')

    def render(self, time, frame_time):
        avg = self.framerate.update(frame_time)
        sys.stdout.write('\r')
        sys.stdout.flush()
        sys.stdout.write(f'fps: {1/avg:.2f}')
        sys.stdout.flush()

        # Render to the first framebuffer
        self.ctx.screen.use()
        self.vao.render(moderngl.TRIANGLE_STRIP)

# Run the application
run_window_config(Example)
