import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import sys


# --- Sutherland-Hodgman Polygon Clipping Algorithm ---

def get_intersection(p1, p2, edge_start, edge_end):
    """
    Finds the intersection of a line segment (p1, p2) with an infinite line defined by an edge.
    This is a modified version to work with the infinite edge lines for clipping.
    """
    s1_x, s1_y = p2[0] - p1[0], p2[1] - p1[1]
    edge_x, edge_y = edge_end[0] - edge_start[0], edge_end[1] - edge_start[1]

    denom = (-edge_x * s1_y + s1_x * edge_y)
    if denom == 0:
        return None  # Parallel

    s_num = -s1_y * (p1[0] - edge_start[0]) + s1_x * (p1[1] - edge_start[1])
    t_num = edge_x * (p1[1] - edge_start[1]) - edge_y * (p1[0] - edge_start[0])

    s = s_num / denom
    t = t_num / denom

    if 0 <= t <= 1:  # Only care if intersection is on the segment p1-p2
        i_x = p1[0] + (t * s1_x)
        i_y = p1[1] + (t * s1_y)
        return (i_x, i_y)

    return None


def is_inside(p, edge_start, edge_end):
    """
    Checks if a point 'p' is on the 'inside' of an infinite line defined by an edge.
    Assumes a clockwise ordering of the clip polygon vertices.
    Uses the cross-product to determine the side.
    """
    return (edge_end[0] - edge_start[0]) * (p[1] - edge_start[1]) - (edge_end[1] - edge_start[1]) * (
                p[0] - edge_start[0]) <= 0


def sutherland_hodgman_clip(subject_polygon, clip_polygon):
    """
    Clips a subject polygon against a convex clip polygon using the Sutherland-Hodgman algorithm.
    """
    if not subject_polygon or not clip_polygon:
        return []

    clipped_vertices = list(subject_polygon)

    # Iterate through each edge of the clipping polygon
    for i in range(len(clip_polygon)):
        edge_start = clip_polygon[i - 1]
        edge_end = clip_polygon[i]

        input_list = list(clipped_vertices)
        clipped_vertices = []

        if not input_list:
            break  # No vertices left to clip

        s = input_list[-1]  # Start with the last vertex of the input list

        for e in input_list:
            s_inside = is_inside(s, edge_start, edge_end)
            e_inside = is_inside(e, edge_start, edge_end)

            if s_inside and e_inside:
                # Case 1: Both vertices are inside -> Add the second vertex 'e'
                clipped_vertices.append(e)
            elif s_inside and not e_inside:
                # Case 2: S is inside, E is outside -> Add the intersection
                intersection = get_intersection(s, e, edge_start, edge_end)
                if intersection:
                    clipped_vertices.append(intersection)
            elif not s_inside and not e_inside:
                # Case 3: Both vertices are outside -> Do nothing
                pass
            elif not s_inside and e_inside:
                # Case 4: S is outside, E is inside -> Add intersection and then 'e'
                intersection = get_intersection(s, e, edge_start, edge_end)
                if intersection:
                    clipped_vertices.append(intersection)
                clipped_vertices.append(e)

            s = e  # Move to the next edge

    return [clipped_vertices] if clipped_vertices else []


# --- Pygame and OpenGL Setup ---

# Global variables
state = 'draw_subject_start'
subject_polygon = []
clip_polygon = []
clipped_polygons = []
temp_coords = []  # For drawing the clip rectangle
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


def draw_polygon(polygon, color, line_width, fill=False, is_drawing=False):
    """Draws a polygon with a given color and line width."""
    if not polygon:
        return

    glColor3f(*color)
    glLineWidth(line_width)

    draw_mode = GL_LINE_STRIP if is_drawing else (GL_POLYGON if fill else GL_LINE_LOOP)

    glBegin(draw_mode)
    for vertex in polygon:
        glVertex2f(*vertex)
    glEnd()


def draw_text(text, x, y, font):
    """Renders text on the screen using Pygame."""
    text_surface = font.render(text, True, (255, 255, 255, 255), (30, 30, 30, 255))
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    glWindowPos2d(x, y)
    glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)


def main():
    """Main application loop."""
    global state, subject_polygon, clip_polygon, clipped_polygons, temp_coords

    pygame.init()
    display = (WINDOW_WIDTH, WINDOW_HEIGHT)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Polygon Clipping (Pygame/OpenGL) - 'D' to Finish Poly, 'R' to Reset")

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
                    state = 'draw_subject_start'
                    subject_polygon, clip_polygon, clipped_polygons, temp_coords = [], [], [], []
                    print("Canvas reset.")

                if event.key == pygame.K_d:
                    if state == 'drawing_subject':
                        if len(subject_polygon) >= 3:
                            state = 'draw_clip_rect_start'
                        else:
                            print("Subject polygon must have at least 3 vertices.")

            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos[0], WINDOW_HEIGHT - event.pos[1]
                if state == 'draw_subject_start' or state == 'drawing_subject':
                    subject_polygon.append((x, y))
                    state = 'drawing_subject'
                elif state == 'draw_clip_rect_start':
                    temp_coords.append((x, y))
                    state = 'drawing_clip_rect'
                elif state == 'drawing_clip_rect':
                    temp_coords.append((x, y))
                    p1, p2 = temp_coords
                    xmin, xmax = sorted([p1[0], p2[0]])
                    ymin, ymax = sorted([p1[1], p2[1]])
                    # Create a clockwise rectangle for clipping
                    clip_polygon = [(xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin)]
                    clipped_polygons = sutherland_hodgman_clip(subject_polygon, clip_polygon)
                    state = 'clipped'
                    temp_coords = []

        # --- Drawing logic ---
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Draw subject polygon (blue)
        draw_polygon(subject_polygon, (0.5, 0.5, 1.0), 2.0, is_drawing=(state == 'drawing_subject'))

        # Draw final clip polygon (red)
        draw_polygon(clip_polygon, (1.0, 0.5, 0.5), 2.0)

        # Draw rubber-band line for subject polygon
        if state == 'drawing_subject' and subject_polygon:
            last_vertex = subject_polygon[-1]
            glColor3f(0.7, 0.7, 0.7)
            glBegin(GL_LINES);
            glVertex2f(*last_vertex);
            glVertex2f(*mouse_pos);
            glEnd()

        # Draw preview of clipping rectangle
        if state == 'drawing_clip_rect':
            p1 = temp_coords[0]
            p2 = mouse_pos
            glColor3f(1.0, 0.5, 0.5)  # Red
            glBegin(GL_LINE_LOOP)
            glVertex2f(p1[0], p1[1])
            glVertex2f(p2[0], p1[1])
            glVertex2f(p2[0], p2[1])
            glVertex2f(p1[0], p2[1])
            glEnd()

        # Draw clipped result (green)
        if state == 'clipped':
            for poly in clipped_polygons:
                draw_polygon(poly, (0.0, 1.0, 0.0), 1.0, fill=True)

        # --- Display instructions ---
        if state == 'draw_subject_start':
            text = "Click to place vertices for the SUBJECT polygon."
        elif state == 'drawing_subject':
            text = f"Drawing SUBJECT ({len(subject_polygon)} vertices). Press 'D' to finish."
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

