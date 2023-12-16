import glfw
from OpenGL.GL import *

# Initialize glfw
if not glfw.init():
    raise Exception("glfw cannot be initialized!")

# These hints help to align glfw with the OpenGL version we are using
# In this case, we are using OpenGL 4.1 on a 2021 Macbook Pro with M1 chip
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

# Creating a window
window = glfw.create_window(800, 600, "My OpenGL Window", None, None)
if not window:
    glfw.terminate()
    raise Exception("glfw window cannot be created!")

glfw.make_context_current(window)

# Create a shader program
def compile_shader(source, shader_type):
    shader = glCreateShader(shader_type)
    glShaderSource(shader, source)
    glCompileShader(shader)
    if glGetShaderiv(shader, GL_COMPILE_STATUS) != GL_TRUE:
        raise RuntimeError(glGetShaderInfoLog(shader))
    return shader

vertex_shader = """
#version 410 core
layout (location = 0) in vec3 aPos;

void main()
{
    gl_Position = vec4(aPos, 1.0);
}
"""

fragment_shader = """
#version 410 core
out vec4 FragColor;

void main()
{
    FragColor = vec4(1.0, 0.0, 0.0, 1.0);
}
"""

shader = glCreateProgram()
vshader = compile_shader(vertex_shader, GL_VERTEX_SHADER)
fshader = compile_shader(fragment_shader, GL_FRAGMENT_SHADER)
glAttachShader(shader, vshader)
glAttachShader(shader, fshader)
glLinkProgram(shader)


# Create VBO (Vertex Buffer Object)
vertices = [-0.5, -0.5, 0.0, 
             0.5, -0.5, 0.0, 
             0.0,  0.5, 0.0]
vertices = (GLfloat * len(vertices))(*vertices)

vbo = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, vbo)
glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_STATIC_DRAW)

# Create VAO (Vertex Array Object)
vao = glGenVertexArrays(1)
glBindVertexArray(vao)
glEnableVertexAttribArray(0)
glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

# Main loop
while not glfw.window_should_close(window):
    glfw.poll_events()

    glClear(GL_COLOR_BUFFER_BIT)


    # Use the shader program
    glUseProgram(shader)

    # Bind the VAO and draw
    glBindVertexArray(vao)
    glDrawArrays(GL_TRIANGLES, 0, 3)

    glfw.swap_buffers(window)

# Clean up the shader program
glDeleteProgram(shader)

# Terminate glfw
glfw.terminate()
