import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import sys


# --- Point Clipping Algorithm ---

def is_point_inside(px, py, xmin, ymin, xmax, ymax):
    """
    Checks if a point (px, py) is inside the clipping window.
    """
    return xmin <= px <= xmax and ymin <= py <= ymax


# --- Pygame and OpenGL Setup ---

# Global variables to manage state and drawing
state = 'draw_point'  # Start by drawing points
coords = []
clipping_window_params = {}
points = []
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600


def init_gl():
    """Initializes OpenGL for 2D drawing."""
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glClearColor(0.1, 0.1, 0.1, 1.0)  # Set a background color (dark gray)
    glPointSize(8.0)  # Set a larger point size to make them visible


def draw_clipping_window():
    """Draws the clipping window rectangle."""
    if 'xmin' in clipping_window_params:
        glColor3f(1.0, 0.0, 0.0)  # Red color
        glLineWidth(2.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(clipping_window_params['xmin'], clipping_window_params['ymin'])
        glVertex2f(clipping_window_params['xmax'], clipping_window_params['ymin'])
        glVertex2f(clipping_window_params['xmax'], clipping_window_params['ymax'])
        glVertex2f(clipping_window_params['xmin'], clipping_window_params['ymax'])
        glEnd()


def draw_points():
    """Draws all points, coloring them based on whether they are inside the clip window."""
    glBegin(GL_POINTS)
    for p in points:
        # If clipping has happened, color points based on their position
        if state == 'clipped':
            if is_point_inside(p[0], p[1], **clipping_window_params):
                glColor3f(0.0, 1.0, 0.0)  # Green for inside
            else:
                glColor3f(0.5, 0.5, 1.0)  # Blue for outside
        else:
            glColor3f(0.8, 0.8, 0.8)  # White for pre-clipping

        glVertex2f(p[0], p[1])
    glEnd()


def draw_text(text, x, y, font):
    """Renders text on the screen using Pygame."""
    text_surface = font.render(text, True, (255, 255, 255, 255), (30, 30, 30, 255))
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    glWindowPos2d(x, y)
    glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)


def main():
    """Main application loop."""
    global state, coords, clipping_window_params, points

    pygame.init()
    display = (WINDOW_WIDTH, WINDOW_HEIGHT)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Point Clipping (Pygame/OpenGL) - Press 'C' to Clip, 'R' to Reset")

    font = pygame.font.Font(None, 24)
    init_gl()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Reset everything
                    state = 'draw_point'
                    coords = []
                    clipping_window_params = {}
                    points = []
                    print("Canvas reset.")

                if event.key == pygame.K_c and state == 'draw_point':
                    if points:
                        state = 'draw_window_start'
                        coords = []
                        print("Switched to clipping mode. Define the window.")
                    else:
                        print("Please draw at least one point before trying to clip.")

            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos[0], WINDOW_HEIGHT - event.pos[1]

                if state == 'draw_point':
                    points.append((x, y))
                elif state == 'draw_window_start':
                    coords.append((x, y))
                    state = 'draw_window_end'
                elif state == 'draw_window_end':
                    coords.append((x, y))
                    p1 = coords[0]
                    p2 = coords[1]
                    xmin, xmax = sorted([p1[0], p2[0]])
                    ymin, ymax = sorted([p1[1], p2[1]])
                    clipping_window_params = {'xmin': xmin, 'ymin': ymin, 'xmax': xmax, 'ymax': ymax}

                    coords = []
                    state = 'clipped'  # Final state

        # Drawing logic
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        draw_points()
        draw_clipping_window()

        # Display instructions
        if state == 'draw_point':
            text = "Click to draw points. Press 'C' to start clipping."
        elif state == 'draw_window_start':
            text = "Click to set the first corner of the clipping window."
        elif state == 'draw_window_end':
            text = "Click to set the second corner of the clipping window."
        elif state == 'clipped':
            text = "Clipping complete. Press 'R' to reset."
        else:
            text = ""
        draw_text(text, 10, WINDOW_HEIGHT - 30, font)

        pygame.display.flip()
        pygame.time.wait(10)


if __name__ == '__main__':
    main()

