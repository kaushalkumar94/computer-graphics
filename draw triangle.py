import glfw
from OpenGL.GL import *

# Initialize GLFW
if not glfw.init():
    raise Exception("GLFW can't be initialized")

# Create window
window = glfw.create_window(800, 600, "Colored Triangle", None, None)

if not window:
    glfw.terminate()
    raise Exception("GLFW window can't be created")

glfw.make_context_current(window)

# Main render loop
while not glfw.window_should_close(window):
    glfw.poll_events()

    glClearColor(0.1, 0.2, 0.3, 1)
    glClear(GL_COLOR_BUFFER_BIT)

    glBegin(GL_TRIANGLES)
    glColor3f(1, 0, 0)     # Red
    glVertex2f(-0.5, -0.5)
    glColor3f(0, 1, 0)     # Green
    glVertex2f(0.5, -0.5)
    glColor3f(0, 0, 1)     # Blue
    glVertex2f(0.0, 0.5)
    glEnd()

    glfw.swap_buffers(window)

# Cleanup
glfw.terminate()
