from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional
import json
from pathlib import Path
import time

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from OpenGL.GLUT import *
except Exception as e:
    raise SystemExit("PyOpenGL and GLUT are required. Install with: pip install PyOpenGL PyOpenGL_accelerate\n" + str(e))

# ----------------------- State & Config -----------------------

Point = Tuple[int, int]
Color = Tuple[float, float, float]

DRAW_COLORS: List[Color] = [
    (1.0, 1.0, 1.0),  # 1 White
    (1.0, 0.0, 0.0),  # 2 Red
    (0.0, 1.0, 0.0),  # 3 Green
    (0.0, 0.5, 1.0),  # 4 Sky
    (1.0, 0.5, 0.0),  # 5 Orange
    (1.0, 1.0, 0.0),  # 6 Yellow
    (1.0, 0.0, 1.0),  # 7 Magenta
    (0.5, 0.8, 0.2),  # 8 Lime-ish
    (0.8, 0.8, 0.8),  # 9 Light gray
]

BG_COLORS: List[Color] = [
    (0.05, 0.05, 0.07),  # Dark slate
    (0.15, 0.15, 0.18),
    (0.0, 0.0, 0.0),
    (0.1, 0.0, 0.1),
    (0.0, 0.08, 0.0),
    (0.08, 0.03, 0.0),
]

class ShapeType:
    LINE = 'Line'
    CIRCLE = 'Circle'
    ELLIPSE = 'Ellipse'
    RECT = 'Rectangle'
    SQUARE = 'Square'
    TRIANGLE = 'Triangle'

@dataclass
class ErrorStats:
    steps: int = 0
    avg_abs_err: float = 0.0
    max_abs_err: float = 0.0

@dataclass
class Primitive:
    kind: str
    params: Tuple
    color: Color
    err: Optional[ErrorStats] = None

class App:
    def __init__(self):
        self.screen_w = 800
        self.screen_h = 600
        self.cx = 400
        self.cy = 300
        self.prims: List[Primitive] = []
        self.preview: Optional[Primitive] = None
        self.shape = ShapeType.LINE
        self.draw_color_idx = 0
        self.bg_color_idx = 0
        self.axes_on = True
        self.ticks_on = True
        self.preview_dotted = True
        self.triangle_pts: List[Point] = []
        self.hud_msg = ""
        self.line_thickness = 1  # Default line thickness

        self.dragging = False
        self.start_pt: Optional[Point] = None

    # ------------------ Low-level plotting ------------------
    def put_pixel(self, x: int, y: int):
        # Guard viewport
        if x < 0 or y < 0 or x >= self.screen_w or y >= self.screen_h:
            return
        glVertex2i(x, y)

    def put_pixel_thick(self, x: int, y: int, thickness: int):
        # Guard viewport
        if x < 0 or y < 0 or x >= self.screen_w or y >= self.screen_h:
            return
        for dx in range(-thickness//2, thickness//2+1):
            for dy in range(-thickness//2, thickness//2+1):
                glVertex2i(x + dx, y + dy)

    # ------------------ Algorithms ------------------
    def bresenham_line(self, x0: int, y0: int, x1: int, y1: int, collect_err=True, thickness: Optional[int]=None, pattern_bits: Optional[str]=None) -> ErrorStats:
        thickness = thickness or self.line_thickness
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1

        err = dx - dy
        stats = ErrorStats()

        # Prepare pattern
        pb = pattern_bits
        if pb:
            if self.symmetric_pattern and len(pb) > 1:
                pb = pb + pb[-2::-1]
        idx = 0

        while True:
            # Decide whether to plot this step
            plot_this = True
            if pb:
                plot_this = (pb[idx % len(pb)] == '1')
            # Always plot the final endpoint regardless of pattern
            if x == x1 and y == y1:
                plot_this = True
            if plot_this:
                glBegin(GL_POINTS)
                self.put_pixel_thick(x, y, thickness)
                glEnd()
            if collect_err:
                eabs = abs(err)
                stats.steps += 1
                stats.avg_abs_err += (eabs - stats.avg_abs_err) / stats.steps
                if eabs > stats.max_abs_err:
                    stats.max_abs_err = eabs
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
            idx += 1
        return stats

    def midpoint_circle(self, xc: int, yc: int, r: int, collect_err=True) -> ErrorStats:
        x = 0
        y = r
        d = 1 - r
        stats = ErrorStats()

        def plot8(cx, cy, x, y):
            glBegin(GL_POINTS)
            self.put_pixel_thick(cx + x, cy + y, self.line_thickness)
            self.put_pixel_thick(cx - x, cy + y, self.line_thickness)
            self.put_pixel_thick(cx + x, cy - y, self.line_thickness)
            self.put_pixel_thick(cx - x, cy - y, self.line_thickness)
            self.put_pixel_thick(cx + y, cy + x, self.line_thickness)
            self.put_pixel_thick(cx - y, cy + x, self.line_thickness)
            self.put_pixel_thick(cx + y, cy - x, self.line_thickness)
            self.put_pixel_thick(cx - y, cy - x, self.line_thickness)
            glEnd()

        while x <= y:
            plot8(xc, yc, x, y)
            if collect_err:
                eabs = abs(d)
                stats.steps += 1
                stats.avg_abs_err += (eabs - stats.avg_abs_err) / stats.steps
                if eabs > stats.max_abs_err:
                    stats.max_abs_err = eabs
            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1
        return stats

    def midpoint_ellipse(self, xc: int, yc: int, rx: int, ry: int, collect_err=True) -> ErrorStats:
        # Region 1
        x = 0
        y = ry
        rx2 = rx * rx
        ry2 = ry * ry
        d1 = ry2 - rx2 * ry + 0.25 * rx2
        dx = 2 * ry2 * x
        dy = 2 * rx2 * y
        stats = ErrorStats()

        def plot4(cx, cy, x, y):
            glBegin(GL_POINTS)
            self.put_pixel_thick(cx + x, cy + y, self.line_thickness)
            self.put_pixel_thick(cx - x, cy + y, self.line_thickness)
            self.put_pixel_thick(cx + x, cy - y, self.line_thickness)
            self.put_pixel_thick(cx - x, cy - y, self.line_thickness)
            glEnd()

        while dx < dy:
            plot4(xc, yc, x, y)
            if collect_err:
                eabs = abs(d1)
                stats.steps += 1
                stats.avg_abs_err += (eabs - stats.avg_abs_err) / stats.steps
                if eabs > stats.max_abs_err:
                    stats.max_abs_err = eabs
            if d1 < 0:
                x += 1
                dx = 2 * ry2 * x
                d1 += dx + ry2
            else:
                x += 1
                y -= 1
                dx = 2 * ry2 * x
                dy = 2 * rx2 * y
                d1 += dx - dy + ry2

        # Region 2
        d2 = ry2 * (x + 0.5) ** 2 + rx2 * (y - 1) ** 2 - rx2 * ry2
        while y >= 0:
            plot4(xc, yc, x, y)
            if collect_err:
                eabs = abs(d2)
                stats.steps += 1
                stats.avg_abs_err += (eabs - stats.avg_abs_err) / stats.steps
                if eabs > stats.max_abs_err:
                    stats.max_abs_err = eabs
            if d2 > 0:
                y -= 1
                dy = 2 * rx2 * y
                d2 += rx2 - dy
            else:
                y -= 1
                x += 1
                dx = 2 * ry2 * x
                dy = 2 * rx2 * y
                d2 += dx - dy + rx2
        return stats

    # Composite shapes via Bresenham on edges
    def draw_rect(self, x0, y0, x1, y1) -> ErrorStats:
        stats = ErrorStats()
        stats_a = self.bresenham_line(x0, y0, x1, y0)
        stats_b = self.bresenham_line(x1, y0, x1, y1)
        stats_c = self.bresenham_line(x1, y1, x0, y1)
        stats_d = self.bresenham_line(x0, y1, x0, y0)
        parts = [stats_a, stats_b, stats_c, stats_d]
        for s in parts:
            stats.steps += s.steps
            stats.max_abs_err = max(stats.max_abs_err, s.max_abs_err)
        # Weighted average of averages
        if stats.steps:
            stats.avg_abs_err = sum(s.avg_abs_err * s.steps for s in parts) / stats.steps
        return stats

    def draw_triangle(self, p0: Point, p1: Point, p2: Point) -> ErrorStats:
        stats = ErrorStats()
        s1 = self.bresenham_line(p0[0], p0[1], p1[0], p1[1])
        s2 = self.bresenham_line(p1[0], p1[1], p2[0], p2[1])
        s3 = self.bresenham_line(p2[0], p2[1], p0[0], p0[1])
        parts = [s1, s2, s3]
        for s in parts:
            stats.steps += s.steps
            stats.max_abs_err = max(stats.max_abs_err, s.max_abs_err)
        if stats.steps:
            stats.avg_abs_err = sum(s.avg_abs_err * s.steps for s in parts) / stats.steps
        return stats

    # ------------------ Rendering ------------------
    def draw_axes(self):
        glColor3f(0.4, 0.4, 0.45)
        glBegin(GL_POINTS)
        # X axis (horizontal)
        for x in range(0, self.screen_w):
            self.put_pixel(x, self.cy)
        # Y axis (vertical)
        for y in range(0, self.screen_h):
            self.put_pixel(self.cx, y)
        glEnd()

        if self.ticks_on:
            glBegin(GL_POINTS)
            tick = 8
            gap = max(16, min(self.screen_w, self.screen_h)//30)
            for x in range(0, self.screen_w, gap):
                for dy in range(-tick, tick+1):
                    self.put_pixel(x, self.cy + dy)
            for y in range(0, self.screen_h, gap):
                for dx in range(-tick, tick+1):
                    self.put_pixel(self.cx + dx, y)
            glEnd()

        # Quadrant labels
        self.draw_text(10, self.screen_h - 20, "QII")
        self.draw_text(self.cx + 10, self.screen_h - 20, "QI")
        self.draw_text(10, 20, "QIII")
        self.draw_text(self.cx + 10, 20, "QIV")

    def draw_text(self, x: int, y: int, text: str):
        glColor3f(0.8, 0.85, 0.9)
        glRasterPos2i(x, y)
        for ch in text:
            glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))

    def render_primitive(self, prim: Primitive):
        self.log_shape_properties(prim)
        glColor3f(*prim.color)
        kind = prim.kind
        p = prim.params
        if kind == ShapeType.LINE:
            self.bresenham_line(*p)
        elif kind == ShapeType.CIRCLE:
            self.midpoint_circle(*p)
        elif kind == ShapeType.ELLIPSE:
            self.midpoint_ellipse(*p)
        elif kind == ShapeType.RECT:
            x0, y0, x1, y1 = p
            self.draw_rect(x0, y0, x1, y1)
        elif kind == ShapeType.SQUARE:
            x0, y0, x1, y1 = p
            self.draw_rect(x0, y0, x1, y1)
        elif kind == ShapeType.TRIANGLE:
            (x0, y0), (x1, y1), (x2, y2) = p
            self.draw_triangle((x0, y0), (x1, y1), (x2, y2))
        self.log_shape_properties(prim)

    def render_preview(self):
        if not self.preview:
            return
        # dotted preview by skipping some points
        color = tuple(min(1.0, c + 0.2) for c in self.preview.color)
        glColor3f(*color)
        if self.preview_dotted:
            glEnable(GL_COLOR_LOGIC_OP)
            glLogicOp(GL_XOR)
        self.render_primitive(self.preview)
        if self.preview_dotted:
            glDisable(GL_COLOR_LOGIC_OP)

    # ------------------ GLUT Callbacks ------------------
    def display(self):
        bg = BG_COLORS[self.bg_color_idx]
        glClearColor(*bg, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        glPointSize(1)
        glDisable(GL_POINT_SMOOTH)

        # Axes and quadrants
        if self.axes_on:
            self.draw_axes()

        # Draw committed primitives
        for prim in self.prims:
            self.render_primitive(prim)

        # Draw in-progress preview
        self.render_preview()

        # HUD
        hud = f"Shape: {self.shape}  | DrawColor #{self.draw_color_idx+1}  | BG #{self.bg_color_idx+1}  | Prims: {len(self.prims)}"
        if self.hud_msg:
            hud += "  | " + self.hud_msg
        self.draw_text(10, 10 + 15, hud)
        self.draw_text(10, 10, "[L/C/E/R/S/T] shape  [1-9,D/F] color  [G/H] bg  [Z]undo [X]clear [A]axes [I]ticks [P]preview [Esc/Q]quit")

        glutSwapBuffers()

    def reshape(self, w, h):
        self.screen_w, self.screen_h = max(1, w), max(1, h)
        self.cx, self.cy = self.screen_w // 2, self.screen_h // 2
        glViewport(0, 0, self.screen_w, self.screen_h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        # 2D pixel-accurate ortho
        gluOrtho2D(0, self.screen_w, 0, self.screen_h)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def keyboard(self, key, x, y):
        try:
            k = key.decode('utf-8').lower()
        except:
            k = chr(key).lower() if isinstance(key, int) else ''
        if k == 'q' or ord(key) == 27:
            glutLeaveMainLoop()
            return
        if k == '+':
            self.line_thickness = min(10, self.line_thickness + 1)
            self.hud_msg = f"Thickness: {self.line_thickness}"
        elif k == '-':
            self.line_thickness = max(1, self.line_thickness - 1)
            self.hud_msg = f"Thickness: {self.line_thickness}"
        elif k in ['l', 'c', 'e', 'r', 's', 't']:
            mapping = {
                'l': ShapeType.LINE,
                'c': ShapeType.CIRCLE,
                'e': ShapeType.ELLIPSE,
                'r': ShapeType.RECT,
                's': ShapeType.SQUARE,
                't': ShapeType.TRIANGLE,
            }
            self.shape = mapping[k]
            self.triangle_pts.clear()
            self.hud_msg = f"Switched to {self.shape}"
        elif k in ['d', 'f'] or (k.isdigit() and k != '0'):
            if k == 'd':
                self.draw_color_idx = (self.draw_color_idx + 1) % len(DRAW_COLORS)
            elif k == 'f':
                self.draw_color_idx = (self.draw_color_idx - 1) % len(DRAW_COLORS)
            else:
                self.draw_color_idx = (int(k) - 1) % len(DRAW_COLORS)
            self.hud_msg = f"Draw color set #{self.draw_color_idx+1}"
        elif k in ['g', 'h']:
            if k == 'g':
                self.bg_color_idx = (self.bg_color_idx + 1) % len(BG_COLORS)
            else:
                self.bg_color_idx = (self.bg_color_idx - 1) % len(BG_COLORS)
            self.hud_msg = f"Background set #{self.bg_color_idx+1}"
        elif k == 'a':
            self.axes_on = not self.axes_on
        elif k == 'i':
            self.ticks_on = not self.ticks_on
        elif k == 'p':
            self.preview_dotted = not self.preview_dotted
        elif k == 'z':
            if self.prims:
                self.prims.pop()
                self.hud_msg = "Undo"
        elif k == 'x':
            self.prims.clear()
            self.hud_msg = "Cleared"
        glutPostRedisplay()

    def mouse(self, button, state, x, y):
        # GLUT gives y from top; convert to bottom origin
        y = self.screen_h - y
        if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            if self.shape == ShapeType.TRIANGLE:
                self.triangle_pts.append((x, y))
                if len(self.triangle_pts) == 3:
                    color = DRAW_COLORS[self.draw_color_idx]
                    err = self.draw_triangle(self.triangle_pts[0], self.triangle_pts[1], self.triangle_pts[2])
                    self.prims.append(Primitive(ShapeType.TRIANGLE, (self.triangle_pts[0], self.triangle_pts[1], self.triangle_pts[2]), color, err))
                    self.hud_msg = f"Triangle drawn | steps={err.steps} avg|d|={err.avg_abs_err:.2f} max|d|={err.max_abs_err:.2f}"
                    self.triangle_pts.clear()
                    glutPostRedisplay()
                else:
                    self.hud_msg = f"Triangle vertex {len(self.triangle_pts)} set"
            else:
                self.dragging = True
                self.start_pt = (x, y)
                self.preview = None
        elif button == GLUT_LEFT_BUTTON and state == GLUT_UP:
            if self.dragging and self.start_pt is not None:
                x0, y0 = self.start_pt
                x1, y1 = x, y
                color = DRAW_COLORS[self.draw_color_idx]
                err = None
                if self.shape == ShapeType.LINE:
                    err = self.bresenham_line(x0, y0, x1, y1)
                    self.prims.append(Primitive(ShapeType.LINE, (x0, y0, x1, y1), color, err))
                elif self.shape == ShapeType.RECT or self.shape == ShapeType.SQUARE:
                    if self.shape == ShapeType.SQUARE:
                        side = max(abs(x1 - x0), abs(y1 - y0))
                        x1 = x0 + (side if x1 >= x0 else -side)
                        y1 = y0 + (side if y1 >= y0 else -side)
                    err = self.draw_rect(min(x0,x1), min(y0,y1), max(x0,x1), max(y0,y1))
                    self.prims.append(Primitive(self.shape, (min(x0,x1), min(y0,y1), max(x0,x1), max(y0,y1)), color, err))
                elif self.shape == ShapeType.CIRCLE:
                    r = int(((x1 - x0)**2 + (y1 - y0)**2) ** 0.5)
                    err = self.midpoint_circle(x0, y0, r)
                    self.prims.append(Primitive(ShapeType.CIRCLE, (x0, y0, r), color, err))
                elif self.shape == ShapeType.ELLIPSE:
                    rx = abs(x1 - x0)
                    ry = abs(y1 - y0)
                    err = self.midpoint_ellipse(x0, y0, rx, ry)
                    self.prims.append(Primitive(ShapeType.ELLIPSE, (x0, y0, rx, ry), color, err))
                self.preview = None
                self.dragging = False
                self.start_pt = None
                if err:
                    self.hud_msg = f"{self.shape} drawn | steps={err.steps} avg|d|={err.avg_abs_err:.2f} max|d|={err.max_abs_err:.2f}"
                glutPostRedisplay()

    def motion(self, x, y):
        if not self.dragging or self.start_pt is None:
            return
        y = self.screen_h - y
        x0, y0 = self.start_pt
        x1, y1 = x, y
        color = DRAW_COLORS[self.draw_color_idx]
        if self.shape == ShapeType.LINE:
            self.preview = Primitive(ShapeType.LINE, (x0, y0, x1, y1), color)
        elif self.shape == ShapeType.RECT or self.shape == ShapeType.SQUARE:
            if self.shape == ShapeType.SQUARE:
                side = max(abs(x1 - x0), abs(y1 - y0))
                x1 = x0 + (side if x >= x0 else -side)
                y1 = y0 + (side if y >= y0 else -side)
            self.preview = Primitive(self.shape, (min(x0,x1), min(y0,y1), max(x0,x1), max(y0,y1)), color)
        elif self.shape == ShapeType.CIRCLE:
            r = int(((x1 - x0)**2 + (y1 - y0)**2) ** 0.5)
            self.preview = Primitive(ShapeType.CIRCLE, (x0, y0, r), color)
        elif self.shape == ShapeType.ELLIPSE:
            rx = abs(x1 - x0)
            ry = abs(y1 - y0)
            self.preview = Primitive(ShapeType.ELLIPSE, (x0, y0, rx, ry), color)
        glutPostRedisplay()

    def log_shape_properties(self, prim: Primitive):
        with open('../drawing_properties.txt', 'a') as f:
            f.write(f"Shape: {prim.kind}\n")
            f.write(f"Color: {prim.color}\n")
            f.write(f"Parameters: {prim.params}\n")
            if prim.err:
                f.write(f"Error Stats: {prim.err.steps} steps, avg_err={prim.err.avg_abs_err}, max_err={prim.err.max_abs_err}\n")
            f.write("---\n")

# ----------------------- Bootstrap -----------------------
app = App()

def init_glut():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    # Start small; then query screen for fullscreen
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"OpenGL Interactive Drawing Board")

    # Fullscreen that should cover laptop display
    try:
        glutFullScreen()
    except Exception:
        pass

    # Set initial size based on actual window
    app.reshape(glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT))

    glutDisplayFunc(app.display)
    glutReshapeFunc(app.reshape)
    glutKeyboardFunc(app.keyboard)
    glutMouseFunc(app.mouse)
    glutMotionFunc(app.motion)

    glDisable(GL_DEPTH_TEST)
    glShadeModel(GL_FLAT)

if __name__ == '__main__':
    init_glut()
    glutMainLoop()
