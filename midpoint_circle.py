import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

clicked_points = []  # store center and radius point

def midpoint_circle(radius):
    points = []
    x = 0
    y = radius
    d = 1 - radius
    points.extend(symmetric_points(x, y))
    while x < y:
        x += 1
        if d < 0:
            d += 2 * x + 1
        else:
            y -= 1
            d += 2 * (x - y) + 1
        points.extend(symmetric_points(x, y))
    return points

def symmetric_points(x, y):
    return [
        (x, y), (-x, y), (x, -y), (-x, -y),
        (y, x), (-y, x), (y, -x), (-y, -x)
    ]

def main():
    global clicked_points
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    gluOrtho2D(-4, 4, -3, 3)  # 2D view

    drawn_circle = None  # store (center, radius)

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
                    r = math.sqrt((px - cx) ** 2 + (py - cy) ** 2)
                    drawn_circle = (cx, cy, r)
                    clicked_points.clear()

        glClear(GL_COLOR_BUFFER_BIT)

        # Draw circle if set
        if drawn_circle:
            cx, cy, r = drawn_circle
            circle_points = midpoint_circle(int(r * 100))
            glBegin(GL_POINTS)
            glColor3f(1.0, 1.0, 0.0)  # yellow
            for (x, y) in circle_points:
                glVertex2f(cx + x / 100.0, cy + y / 100.0)
            glEnd()

        pygame.display.flip()
        pygame.time.wait(10)

    pygame.quit()

if __name__ == "__main__":
    main()
