from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

width, height = 500, 500

def symmetric_dda(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1

    # Find absolute values
    abs_dx = abs(dx)
    abs_dy = abs(dy)

    # Determine how many times to scale by 2
    if abs_dx >= abs_dy:
        length = abs_dx
    else:
        length = abs_dy

    # Find the smallest n such that 2^n >= length
    n = 1
    while length > (1 << n):  # 1<<n means 2^n
        n += 1

    # Calculate increments
    x_inc = dx / (1 << n)
    y_inc = dy / (1 << n)

    x = x1
    y = y1

    glBegin(GL_POINTS)
    for _ in range(1 << n):
        glVertex2f(round(x), round(y))
        x += x_inc
        y += y_inc
    glEnd()

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(1.0, 1.0, 1.0)  # white color
    symmetric_dda(50, 50, 400, 300)
    glFlush()

def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)  # black background
    gluOrtho2D(0, width, 0, height)

if __name__ == "__main__":
    glutInit()
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(width, height)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Symmetric DDA Line Drawing - Basic OpenGL")
    init()
    glutDisplayFunc(display)
    glutMainLoop()
