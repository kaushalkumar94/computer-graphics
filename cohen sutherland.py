import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
GRAY = (200, 200, 200)
YELLOW = (255, 255, 0)

# Region codes
INSIDE = 0  # 0000
LEFT = 1  # 0001
RIGHT = 2  # 0010
BOTTOM = 4  # 0100
TOP = 8  # 1000

# Clipping window
clip_rect = pygame.Rect(200, 150, 400, 300)

# Screen setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cohen-Sutherland Line Clipping")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 24)

# Line storage
lines = []
current_line_start = None


def compute_outcode(x, y, rect):
    """Compute the region code for a point (x, y) relative to rectangle"""
    code = INSIDE

    if x < rect.left:
        code |= LEFT
    elif x > rect.right:
        code |= RIGHT

    if y < rect.top:
        code |= TOP
    elif y > rect.bottom:
        code |= BOTTOM

    return code


def cohen_sutherland_clip(x1, y1, x2, y2, rect):
    """
    Cohen-Sutherland line clipping algorithm
    Returns clipped line coordinates or None if line is outside
    """
    outcode1 = compute_outcode(x1, y1, rect)
    outcode2 = compute_outcode(x2, y2, rect)
    accept = False

    while True:
        # Both endpoints inside - trivially accept
        if outcode1 == 0 and outcode2 == 0:
            accept = True
            break

        # Both endpoints share an outside region - trivially reject
        elif (outcode1 & outcode2) != 0:
            break

        # Line needs clipping
        else:
            # Pick an endpoint that's outside
            outcode_out = outcode1 if outcode1 != 0 else outcode2

            # Find intersection point
            if outcode_out & TOP:
                x = x1 + (x2 - x1) * (rect.top - y1) / (y2 - y1)
                y = rect.top
            elif outcode_out & BOTTOM:
                x = x1 + (x2 - x1) * (rect.bottom - y1) / (y2 - y1)
                y = rect.bottom
            elif outcode_out & RIGHT:
                y = y1 + (y2 - y1) * (rect.right - x1) / (x2 - x1)
                x = rect.right
            elif outcode_out & LEFT:
                y = y1 + (y2 - y1) * (rect.left - x1) / (x2 - x1)
                x = rect.left

            # Replace outside point with intersection point
            if outcode_out == outcode1:
                x1, y1 = x, y
                outcode1 = compute_outcode(x1, y1, rect)
            else:
                x2, y2 = x, y
                outcode2 = compute_outcode(x2, y2, rect)

    if accept:
        return (x1, y1, x2, y2)
    return None


def draw_grid():
    """Draw background grid"""
    for x in range(0, WIDTH, 50):
        pygame.draw.line(screen, GRAY, (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, 50):
        pygame.draw.line(screen, GRAY, (0, y), (WIDTH, y), 1)


def draw_instructions():
    """Draw instruction text"""
    instructions = [
        "Click and drag to draw lines",
        "Press C to clear all lines",
        "Press R to reset clipping window"
    ]

    y_offset = 10
    for instruction in instructions:
        text = font.render(instruction, True, BLACK)
        screen.blit(text, (10, y_offset))
        y_offset += 30


# Main loop
running = True
while running:
    screen.fill(WHITE)
    draw_grid()

    # Draw clipping rectangle
    pygame.draw.rect(screen, BLUE, clip_rect, 3)

    # Draw label for clipping window
    label = font.render("Clipping Window", True, BLUE)
    screen.blit(label, (clip_rect.centerx - 70, clip_rect.top - 30))

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            current_line_start = event.pos

        elif event.type == pygame.MOUSEBUTTONUP:
            if current_line_start:
                lines.append((current_line_start, event.pos))
                current_line_start = None

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                lines.clear()
            elif event.key == pygame.K_r:
                clip_rect = pygame.Rect(200, 150, 400, 300)

    # Draw current line being created
    if current_line_start:
        mouse_pos = pygame.mouse.get_pos()
        pygame.draw.line(screen, GRAY, current_line_start, mouse_pos, 2)

    # Draw all lines and their clipped versions
    for start, end in lines:
        # Draw original line in red (thin)
        pygame.draw.line(screen, RED, start, end, 1)

        # Draw clipped line in green (thick)
        clipped = cohen_sutherland_clip(
            start[0], start[1], end[0], end[1], clip_rect
        )

        if clipped:
            x1, y1, x2, y2 = clipped
            pygame.draw.line(screen, GREEN, (x1, y1), (x2, y2), 3)

            # Draw clipping points
            pygame.draw.circle(screen, YELLOW, (int(x1), int(y1)), 5)
            pygame.draw.circle(screen, YELLOW, (int(x2), int(y2)), 5)

    # Draw instructions
    draw_instructions()

    # Draw legend
    legend_y = HEIGHT - 80
    pygame.draw.line(screen, RED, (10, legend_y), (40, legend_y), 1)
    screen.blit(font.render("= Original Line", True, BLACK), (50, legend_y - 10))

    pygame.draw.line(screen, GREEN, (10, legend_y + 30), (40, legend_y + 30), 3)
    screen.blit(font.render("= Clipped Line", True, BLACK), (50, legend_y + 20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()