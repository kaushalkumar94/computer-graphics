import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import sys


# --- Weiler-Atherton Polygon Clipping Algorithm ---

def get_intersection(p1, p2, p3, p4):
    """
    Finds the intersection of two line segments, (p1, p2) and (p3, p4).
    Returns the intersection point or None if they don't intersect within the segments.
    """
    s1_x, s1_y = p2[0] - p1[0], p2[1] - p1[1]
    s2_x, s2_y = p4[0] - p3[0], p4[1] - p3[1]

    denom = (-s2_x * s1_y + s1_x * s2_y)
    if denom == 0:
        return None  # Parallel or collinear

    # Use a small epsilon to handle floating point inaccuracies
    epsilon = 1e-6
    if abs(denom) < epsilon:
        return None

    s_num = -s1_y * (p1[0] - p3[0]) + s1_x * (p1[1] - p3[1])
    t_num = s2_x * (p1[1] - p3[1]) - s2_y * (p1[0] - p3[0])

    s = s_num / denom
    t = t_num / denom

    if epsilon < s < 1 - epsilon and epsilon < t < 1 - epsilon:
        # Intersection detected
        i_x = p1[0] + (t * s1_x)
        i_y = p1[1] + (t * s1_y)
        return (i_x, i_y)

    return None  # No intersection within segments


def is_inside(p, polygon):
    """
    Checks if a point is inside a polygon using the ray-casting algorithm.
    """
    if not polygon:
        return False
    x, y = p
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def weiler_atherton_clip(subject_polygon, clip_polygon):
    """
    Clips a subject polygon against a clip polygon using the Weiler-Atherton algorithm.
    """
    if not subject_polygon or not clip_polygon:
        return []

    # 1. Build lists of vertices including intersections
    subj_list, clip_list = list(subject_polygon), list(clip_polygon)

    # --- Find Intersections ---
    intersections_map = {}  # Using a map to avoid duplicate intersection points
    for i in range(len(clip_list)):
        p1 = clip_list[i - 1]
        p2 = clip_list[i]
        for j in range(len(subj_list)):
            p3 = subj_list[j - 1]
            p4 = subj_list[j]

            intersect_pt = get_intersection(p1, p2, p3, p4)
            if intersect_pt:
                # Round to avoid floating point issues
                pt_key = (round(intersect_pt[0], 5), round(intersect_pt[1], 5))
                if pt_key not in intersections_map:
                    intersections_map[pt_key] = {'clip_idx': i, 'subj_idx': j}

    intersections = [{'pt': k, **v} for k, v in intersections_map.items()]

    # No intersections, check for trivial cases
    if not intersections:
        if is_inside(subject_polygon[0], clip_polygon):
            return [subject_polygon]
        if is_inside(clip_polygon[0], subject_polygon):
            return [clip_polygon]
        return []

    # --- Insert Intersections into Polygon Lists ---
    def insert_intersections(polygon, poly_intersections, idx_key):
        # Sort points on the same edge by distance from start vertex
        for i in poly_intersections:
            p_start = polygon[i[idx_key] - 1]
            i['dist'] = (i['pt'][0] - p_start[0]) ** 2 + (i['pt'][1] - p_start[1]) ** 2

        # Insert sorted points
        for i in sorted(poly_intersections, key=lambda x: (x[idx_key], x['dist']), reverse=True):
            polygon.insert(i[idx_key], i['pt'])

    insert_intersections(clip_list, [i for i in intersections], 'clip_idx')
    insert_intersections(subj_list, [i for i in intersections], 'subj_idx')

    # --- Build Linked List Structure ---
    def build_linked_list(polygon_list, other_polygon, is_subject):
        linked_list = []
        for pt in polygon_list:
            node = {'pt': pt, 'link': None, 'visited': False}
            # Check if it's an intersection point
            if pt in [i['pt'] for i in intersections]:
                node['is_intersection'] = True
                prev_idx = (polygon_list.index(pt) - 1 + len(polygon_list)) % len(polygon_list)
                prev_pt = polygon_list[prev_idx]
                if is_subject:
                    node['type'] = 'leaving' if is_inside(prev_pt, clip_polygon) else 'entering'
            else:
                node['is_intersection'] = False
            linked_list.append(node)
        return linked_list

    subj_linked = build_linked_list(subj_list, clip_polygon, True)
    clip_linked = build_linked_list(clip_list, subject_polygon, False)

    # Link intersection nodes between the two lists
    for s_node in subj_linked:
        if s_node['is_intersection']:
            for c_node in clip_linked:
                if c_node['pt'] == s_node['pt']:
                    s_node['link'] = c_node
                    c_node['link'] = s_node
                    break

    # --- Traverse and Build Result Polygons ---
    clipped_polygons = []
    entering_nodes = [n for n in subj_linked if n.get('type') == 'entering']

    for start_node in entering_nodes:
        if start_node['visited']:
            continue

        current_poly = []
        current_node = start_node

        # This loop traces one complete clipped polygon
        while True:
            # Mark the current intersection node as visited
            current_node['visited'] = True

            # 1. Follow the subject polygon's path until the next intersection
            idx = subj_linked.index(current_node)
            while True:
                idx = (idx + 1) % len(subj_linked)
                next_node_subj = subj_linked[idx]
                current_poly.append(next_node_subj['pt'])

                if next_node_subj['is_intersection']:
                    next_node_subj['visited'] = True
                    current_node = next_node_subj['link']  # Switch to the clip list
                    break

            # 2. Follow the clipping polygon's path until the next intersection
            idx = clip_linked.index(current_node)
            while True:
                idx = (idx + 1) % len(clip_linked)
                next_node_clip = clip_linked[idx]
                current_poly.append(next_node_clip['pt'])

                if next_node_clip['is_intersection']:
                    current_node = next_node_clip['link']  # Switch back to the subject list
                    break

            # 3. If we've returned to where we started, this clipped polygon is complete
            if current_node == start_node:
                break

        if current_poly:
            # Remove duplicate points before adding the polygon to the final list
            final_poly = []
            [final_poly.append(p) for p in current_poly if p not in final_poly]
            clipped_polygons.append(final_poly)

    return clipped_polygons


# --- Pygame and OpenGL Setup ---

# Global variables
state = 'draw_subject_start'
subject_polygon = []
clip_polygon = []
clipped_polygons = []
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
    global state, subject_polygon, clip_polygon, clipped_polygons

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
                    subject_polygon, clip_polygon, clipped_polygons = [], [], []
                    print("Canvas reset.")

                if event.key == pygame.K_d:
                    if state == 'drawing_subject':
                        if len(subject_polygon) >= 3:
                            state = 'draw_clip_start'
                        else:
                            print("Subject polygon must have at least 3 vertices.")
                    elif state == 'drawing_clip':
                        if len(clip_polygon) >= 3:
                            clipped_polygons = weiler_atherton_clip(subject_polygon, clip_polygon)
                            state = 'clipped'
                        else:
                            print("Clipping polygon must have at least 3 vertices.")

            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos[0], WINDOW_HEIGHT - event.pos[1]
                if state == 'draw_subject_start' or state == 'drawing_subject':
                    subject_polygon.append((x, y))
                    state = 'drawing_subject'
                elif state == 'draw_clip_start' or state == 'drawing_clip':
                    clip_polygon.append((x, y))
                    state = 'drawing_clip'

        # --- Drawing logic ---
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Draw subject polygon (blue)
        draw_polygon(subject_polygon, (0.5, 0.5, 1.0), 2.0, is_drawing=(state == 'drawing_subject'))

        # Draw clip polygon (red)
        draw_polygon(clip_polygon, (1.0, 0.5, 0.5), 2.0, is_drawing=(state == 'drawing_clip'))

        # Draw rubber-band line
        if state == 'drawing_subject' and subject_polygon:
            last_vertex = subject_polygon[-1]
            glColor3f(0.7, 0.7, 0.7)
            glBegin(GL_LINES);
            glVertex2f(*last_vertex);
            glVertex2f(*mouse_pos);
            glEnd()
        elif state == 'drawing_clip' and clip_polygon:
            last_vertex = clip_polygon[-1]
            glColor3f(0.7, 0.7, 0.7)
            glBegin(GL_LINES);
            glVertex2f(*last_vertex);
            glVertex2f(*mouse_pos);
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
        elif state == 'draw_clip_start':
            text = "Click to place vertices for the CLIPPING polygon."
        elif state == 'drawing_clip':
            text = f"Drawing CLIPPING ({len(clip_polygon)} vertices). Press 'D' to finish and clip."
        elif state == 'clipped':
            text = "Clipping complete. Press 'R' to reset."
        else:
            text = ""

        draw_text(text, 10, WINDOW_HEIGHT - 30, font)

        pygame.display.flip()
        pygame.time.wait(10)


if __name__ == '__main__':
    main()

