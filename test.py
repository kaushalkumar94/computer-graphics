import glfw
from OpenGL.GL import *

# Initialize GLFW
if not glfw.init():
    raise Exception("GLFW can't be initialized")

# Create a windowed mode window and its OpenGL context
window = glfw.create_window(800, 600, "OpenGL Blank Window", None, None)

if not window:
    glfw.terminate()
    raise Exception("GLFW window can't be created")

# Make the window's context current
glfw.make_context_current(window)

# Main loop
while not glfw.window_should_close(window):
    glfw.poll_events()

    # Set background color and clear
    glClearColor(0.1, 0.2, 0.3, 1)  # RGBA
    glClear(GL_COLOR_BUFFER_BIT)

    glfw.swap_buffers(window)

# Clean up
glfw.terminate()
