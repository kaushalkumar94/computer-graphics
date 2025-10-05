import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import sys

# --- Cohen-Sutherland Line Clipping Algorithm ---

INSIDE = 0  # 0000
LEFT = 1  # 0001
RIGHT = 2  # 0010
BOTTOM = 4  # 0100
TOP = 8  # 1000


def compute_outcode(x, y, xmin, ymin, xmax, ymax):
    """Computes the 4-bit outcode for a point."""
    code = INSIDE
    if x < xmin:
        code |= LEFT
    elif x > xmax:
        code |= RIGHT
    if y < ymin:
        code |= BOTTOM
    elif y > ymax:
        code |= TOP
    return code


def cohen_sutherland_clip(x1, y1, x2, y2, xmin, ymin, xmax, ymax):
    """Clips a line from P1=(x1,y1) to P2=(x2,y2) against a rectangle."""
    outcode1 = compute_outcode(x1, y1, xmin, ymin, xmax, ymax)
    outcode2 = compute_outcode(x2, y2, xmin, ymin, xmax, ymax)
    accepted = False

    while True:
        # Case 1: Both endpoints are inside the clipping window.
        if not (outcode1 | outcode2):
            accepted = True
            break
        # Case 2: Both endpoints are outside and in the same region.
        elif outcode1 & outcode2:
            break
        # Case 3: Line needs clipping.
        else:
            x, y = 0.0, 0.0
            # Choose an endpoint that is outside the window.
            outcode_out = outcode1 if outcode1 else outcode2

            # Find the intersection point.
            if outcode_out & TOP:
                x = x1 + (x2 - x1) * (ymax - y1) / (y2 - y1) if (y2 - y1) != 0 else x1
                y = ymax
            elif outcode_out & BOTTOM:
                x = x1 + (x2 - x1) * (ymin - y1) / (y2 - y1) if (y2 - y1) != 0 else x1
                y = ymin
            elif outcode_out & RIGHT:
                y = y1 + (y2 - y1) * (xmax - x1) / (x2 - x1) if (x2 - x1) != 0 else y1
                x = xmax
            elif outcode_out & LEFT:
                y = y1 + (y2 - y1) * (xmin - x1) / (x2 - x1) if (x2 - x1) != 0 else y1
                x = xmin

            # Update the outside endpoint to the intersection point.
            if outcode_out == outcode1:
                x1, y1 = x, y
                outcode1 = compute_outcode(x1, y1, xmin, ymin, xmax, ymax)
            else:
                x2, y2 = x, y
                outcode2 = compute_outcode(x2, y2, xmin, ymin, xmax, ymax)

    return (x1, y1, x2, y2) if accepted else None


# --- Pygame and OpenGL Setup ---

# Global variables
state = 'draw_line_start'
clip_window = {}
original_lines, clipped_lines = [], []
temp_coords = []
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600


def init_gl():
    """Initializes OpenGL for 2D drawing."""
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glClearColor(0.1, 0.1, 0.1, 1.0)


def draw_lines(lines, color, line_width):
    """Draws a list of lines."""
    if not lines: return
    glColor3f(*color)
    glLineWidth(line_width)
    glBegin(GL_LINES)
    for line in lines:
        glVertex2f(line[0], line[1])
        glVertex2f(line[2], line[3])
    glEnd()


def draw_rectangle(rect, color, line_width):
    """Draws a rectangle."""
    if not rect: return
    glColor3f(*color)
    glLineWidth(line_width)
    glBegin(GL_LINE_LOOP)
    glVertex2f(rect['xmin'], rect['ymin'])
    glVertex2f(rect['xmax'], rect['ymin'])
    glVertex2f(rect['xmax'], rect['ymax'])
    glVertex2f(rect['xmin'], rect['ymax'])
    glEnd()


def draw_text(text, x, y, font):
    """Renders text on the screen using Pygame."""
    text_surface = font.render(text, True, (255, 255, 255, 255), (30, 30, 30, 255))
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    glWindowPos2d(x, y)
    glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)


def reset_all():
    """Resets all drawing variables."""
    global state, clip_window, original_lines, clipped_lines, temp_coords
    state = 'draw_line_start'
    clip_window = {}
    original_lines, clipped_lines = [], []
    temp_coords = []


def main():
    """Main application loop."""
    global state, clip_window, original_lines, clipped_lines, temp_coords

    pygame.init()
    display = (WINDOW_WIDTH, WINDOW_HEIGHT)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Line Clipping App - 'C' to Clip, 'R' to Reset")

    font = pygame.font.Font(None, 24)
    init_gl()
    mouse_pos = (0, 0)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEMOTION:
                mouse_pos = (event.pos[0], WINDOW_HEIGHT - event.pos[1])

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_all()
                    print("Canvas reset.")
                elif event.key == pygame.K_c and original_lines:
                    state = 'draw_clip_rect_start'
                    temp_coords = []

            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos[0], WINDOW_HEIGHT - event.pos[1]

                if state in ['draw_line_start', 'draw_line_end']:
                    temp_coords.append((x, y))
                    if len(temp_coords) == 2:
                        original_lines.append(tuple(temp_coords[0] + temp_coords[1]))
                        temp_coords = []
                        state = 'draw_line_start'
                    else:
                        state = 'draw_line_end'
                elif state == 'draw_clip_rect_start':
                    temp_coords.append((x, y))
                    state = 'drawing_clip_rect'
                elif state == 'drawing_clip_rect':
                    temp_coords.append((x, y))
                    p1, p2 = temp_coords
                    xmin, xmax = sorted([p1[0], p2[0]])
                    ymin, ymax = sorted([p1[1], p2[1]])

                    clip_window = {'xmin': xmin, 'ymin': ymin, 'xmax': xmax, 'ymax': ymax}
                    clipped_lines = []
                    for line in original_lines:
                        clipped = cohen_sutherland_clip(*line, **clip_window)
                        if clipped:
                            clipped_lines.append(clipped)

                    state = 'clipped'
                    temp_coords = []

        # --- Drawing logic ---
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        draw_lines(original_lines, (0.5, 0.5, 1.0), 2.0)
        if state == 'clipped':
            draw_lines(clipped_lines, (0.0, 1.0, 0.0), 3.0)

        # Draw clip rectangle (final or preview)
        draw_rectangle(clip_window, (1.0, 0.5, 0.5), 2.0)
        if state == 'drawing_clip_rect':
            p1, p2 = temp_coords[0], mouse_pos
            glColor3f(1.0, 0.5, 0.5);
            glBegin(GL_LINE_LOOP)
            glVertex2f(p1[0], p1[1]);
            glVertex2f(p2[0], p1[1]);
            glVertex2f(p2[0], p2[1]);
            glVertex2f(p1[0], p2[1])
            glEnd()

        # Draw rubber-band line
        if state == 'draw_line_end':
            glColor3f(0.7, 0.7, 0.7);
            glBegin(GL_LINES);
            glVertex2f(*temp_coords[0]);
            glVertex2f(*mouse_pos);
            glEnd()

        # --- Display instructions ---
        if state == 'draw_line_start':
            text = "Click to set the start point of a line. Press 'C' to clip."
        elif state == 'draw_line_end':
            text = "Click to set the end point of the line."
        elif state == 'draw_clip_rect_start':
            text = "Click to set the first corner of the clipping RECTANGLE."
        elif state == 'drawing_clip_rect':
            text = "Click to set the second corner of the clipping RECTANGLE."
        elif state == 'clipped':
            text = "Clipping complete. Press 'R' to reset."
        else:
            text = ""
        draw_text(text, 10, WINDOW_HEIGHT - 30, font)

        pygame.display.flip()
        pygame.time.wait(10)


if __name__ == '__main__':
    main()
