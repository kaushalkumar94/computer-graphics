from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Window size
width, height = 500, 500

def dda_line(x1, y1, x2, y2):
    """Draw a line using DDA algorithm with OpenGL points."""
    dx = x2 - x1
    dy = y2 - y1
    steps = int(max(abs(dx), abs(dy)))

    x_inc = dx / steps
    y_inc = dy / steps

    x = x1
    y = y1

    glBegin(GL_POINTS)
    for _ in range(steps + 1):
        glVertex2f(x, y)
        x += x_inc
        y += y_inc
    glEnd()

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(1.0, 1.0, 1.0)  # white line
    dda_line(10, 10, 590, 300)
    glFlush()

def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)  # black background
    glColor3f(1.0, 1.0, 1.0)  # default color: white
    gluOrtho2D(0, width, 0, height)  # 2D projection

if __name__ == "__main__":
    glutInit()
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(width, height)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"DDA Line Drawing - Basic OpenGL")
    init()
    glutDisplayFunc(display)
    glutMainLoop()
