from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Window size
width, height = 500, 500

# Bresenham's Line Drawing Algorithm
def bresenham_line(x1, y1, x2, y2):
    points = []
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    while True:
        points.append((x1, y1))
        if x1 == x2 and y1 == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy
    return points

def draw_line():
    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(1.0, 1.0, 1.0)  # White line

    points = bresenham_line(50, 50, 400, 300)

    glBegin(GL_POINTS)
    for x, y in points:
        glVertex2i(x, y)
    glEnd()

    glFlush()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(width, height)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Bresenham's Line Drawing Algorithm")
    glClearColor(0.0, 0.0, 0.0, 0.0)  # Black background
    gluOrtho2D(0, width, 0, height)
    glutDisplayFunc(draw_line)
    glutMainLoop()

if __name__ == "__main__":
    main()
