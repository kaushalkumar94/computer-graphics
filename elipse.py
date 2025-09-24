import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

clicked_points = []

def midpoint_ellipse(rx, ry):
    points = []
    x = 0
    y = ry

    # Decision parameter for region 1 
    d1 = (ry * ry) - (rx * rx * ry) + (0.25 * rx * rx)
    dx = 2 * ry * ry * x
    dy = 2 * rx * rx * y

    # Region 1
    while dx < dy:
        points.extend(symmetric_points(x, y))
        if d1 < 0:
            x += 1
            dx += 2 * ry * ry
            d1 += dx + (ry * ry)
        else:
            x += 1
            y -= 1
            dx += 2 * ry * ry
            dy -= 2 * rx * rx
            d1 += dx - dy + (ry * ry)

    # Decision parameter for region 2
    d2 = ((ry * ry) * ((x + 0.5) * (x + 0.5))) + ((rx * rx) * ((y - 1) * (y - 1))) - (rx * rx * ry * ry)

    # Region 2
    while y >= 0:
        points.extend(symmetric_points(x, y))
        if d2 > 0:
            y -= 1
            dy -= 2 * rx * rx
            d2 += (rx * rx) - dy
        else:
            y -= 1
            x += 1
            dx += 2 * ry * ry
            dy -= 2 * rx * rx
            d2 += dx - dy + (rx * rx)

    return points

def symmetric_points(x, y):
    return [
        (x, y), (-x, y), (x, -y), (-x, -y)
    ]

def main():
    global clicked_points
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    gluOrtho2D(-4, 4, -3, 3)  # 2D view

    drawn_ellipse = None  # store (center, rx, ry)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == MOUSEBUTTONDOWN:
                # Convert screen coords to OpenGL coords
                mx, my = event.pos
                w, h = display
                x = (mx / w) * 8 - 4       # map to -4..4
                y = (1 - my / h) * 6 - 3   # map to -3..3
                clicked_points.append((x, y))

                if len(clicked_points) == 2:
                    cx, cy = clicked_points[0]
                    px, py = clicked_points[1]
                    rx = abs(px - cx)
                    ry = abs(py - cy)
                    drawn_ellipse = (cx, cy, rx, ry)
                    clicked_points.clear()

        glClear(GL_COLOR_BUFFER_BIT)

        # Draw ellipse if set
        if drawn_ellipse:
            cx, cy, rx, ry = drawn_ellipse
            ellipse_points = midpoint_ellipse(int(rx * 100), int(ry * 100))
            glBegin(GL_POINTS)
            glColor3f(0.0, 1.0, 1.0)  # cyan
            for (x, y) in ellipse_points:
                glVertex2f(cx + x / 100.0, cy + y / 100.0)
            glEnd()

        pygame.display.flip()
        pygame.time.wait(10)

    pygame.quit()

if __name__ == "__main__":
    main()
