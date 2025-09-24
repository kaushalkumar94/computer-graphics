import pygame
import sys
import math

# --- Configuration ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 700
CANVAS_WIDTH, CANVAS_HEIGHT = 800, 600
UI_HEIGHT = SCREEN_HEIGHT - CANVAS_HEIGHT
BG_COLOR = (255, 255, 255)  # White

# Color Palette
COLORS = [
    (0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255),
    (255, 255, 0), (255, 0, 255), (0, 255, 255), (128, 0, 128),
    (255, 165, 0), (165, 42, 42), (128, 128, 128), (211, 211, 211)
]
ANIMATION_BATCH_SIZE = 500  # Pixels per frame during fill animation


# --- Core Algorithms (Generators for Animation) ---

def boundary_fill_iterative(screen, x, y, fill_color, boundary_color, connectivity=4):
    """
    Performs an iterative boundary fill using a stack.
    Yields control to the main loop to create an animation effect.
    """
    stack = [(x, y)]
    pixels_processed = 0

    try:
        initial_color = screen.get_at((x, y))
        if initial_color == boundary_color or initial_color == fill_color:
            print("Seed point is on boundary or already filled.")
            return
    except IndexError:
        print("Seed point is outside the canvas.")
        return

    while stack:
        px, py = stack.pop()

        if not (0 <= px < CANVAS_WIDTH and 0 <= py < CANVAS_HEIGHT):
            continue

        if screen.get_at((px, py)) != boundary_color and screen.get_at((px, py)) != fill_color:
            screen.set_at((px, py), fill_color)
            pixels_processed += 1

            if pixels_processed % ANIMATION_BATCH_SIZE == 0:
                yield

            stack.append((px + 1, py))
            stack.append((px - 1, py))
            stack.append((px, py + 1))
            stack.append((px, py - 1))

            if connectivity == 8:
                stack.append((px + 1, py + 1))
                stack.append((px - 1, py + 1))
                stack.append((px + 1, py - 1))
                stack.append((px - 1, py - 1))
    yield


def flood_fill_iterative(screen, x, y, fill_color, connectivity=4):
    """
    Performs an iterative flood fill using a stack.
    Replaces a target color with the fill color. Yields for animation.
    """
    try:
        target_color = screen.get_at((x, y))
    except IndexError:
        print("Seed point is outside the canvas.")
        return

    if target_color == fill_color:
        print("Target area is already the fill color.")
        return

    stack = [(x, y)]
    pixels_processed = 0

    while stack:
        px, py = stack.pop()

        if not (0 <= px < CANVAS_WIDTH and 0 <= py < CANVAS_HEIGHT):
            continue

        if screen.get_at((px, py)) == target_color:
            screen.set_at((px, py), fill_color)
            pixels_processed += 1

            if pixels_processed % ANIMATION_BATCH_SIZE == 0:
                yield

            stack.append((px + 1, py))
            stack.append((px - 1, py))
            stack.append((px, py + 1))
            stack.append((px, py - 1))

            if connectivity == 8:
                stack.append((px + 1, py + 1))
                stack.append((px - 1, py + 1))
                stack.append((px + 1, py - 1))
                stack.append((px - 1, py - 1))
    yield


# --- Main Application ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Advanced Fill Algorithm Visualizer")

    canvas = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT))
    canvas.fill(BG_COLOR)

    # --- State Variables ---
    drawing = False
    start_pos, last_pos = None, None
    active_tool = 'pencil'
    boundary_color = COLORS[0]
    fill_color = COLORS[1]
    active_filler = None

    font = pygame.font.SysFont('Arial', 14, bold=True)

    # --- UI Layout ---
    tools = ['pencil', 'line', 'rect', 'circle', 'bound_4', 'bound_8', 'flood_4', 'flood_8']
    button_width, button_height, margin = 65, 30, 8
    num_tools = len(tools)
    tool_buttons = {
        tool: pygame.Rect(margin + i * (button_width + margin), CANVAS_HEIGHT + 20, button_width, button_height) for
        i, tool in enumerate(tools)}
    clear_button = pygame.Rect(SCREEN_WIDTH - button_width - margin, CANVAS_HEIGHT + 20, button_width, button_height)

    color_swatch_size = 25
    color_buttons = {color: pygame.Rect(margin + i * (color_swatch_size + 5), CANVAS_HEIGHT + 70, color_swatch_size,
                                        color_swatch_size) for i, color in enumerate(COLORS)}

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # --- Mouse Events ---
            if event.type == pygame.MOUSEBUTTONDOWN:
                if active_filler is None:  # Disable actions during fill
                    # UI clicks
                    clicked_ui = False
                    if clear_button.collidepoint(event.pos):
                        canvas.fill(BG_COLOR)
                        clicked_ui = True

                    for tool, rect in tool_buttons.items():
                        if rect.collidepoint(event.pos):
                            active_tool = tool
                            clicked_ui = True
                            break

                    for color, rect in color_buttons.items():
                        if rect.collidepoint(event.pos):
                            if event.button == 1:  # Left-click sets boundary color
                                boundary_color = color
                            elif event.button == 3:  # Right-click sets fill color
                                fill_color = color
                            clicked_ui = True
                            break

                    # Canvas clicks
                    if not clicked_ui and event.pos[1] < CANVAS_HEIGHT:
                        x, y = event.pos
                        if 'bound' in active_tool:
                            conn = 8 if active_tool == 'bound_8' else 4
                            active_filler = boundary_fill_iterative(canvas, x, y, fill_color, boundary_color, conn)
                        elif 'flood' in active_tool:
                            conn = 8 if active_tool == 'flood_8' else 4
                            active_filler = flood_fill_iterative(canvas, x, y, fill_color, conn)
                        else:
                            drawing = True
                            start_pos = event.pos
                            last_pos = event.pos  # For pencil tool

            elif event.type == pygame.MOUSEMOTION:
                if drawing and active_tool == 'pencil' and event.pos[1] < CANVAS_HEIGHT:
                    pygame.draw.line(canvas, boundary_color, last_pos, event.pos, 2)
                    last_pos = event.pos

            elif event.type == pygame.MOUSEBUTTONUP:
                if drawing:
                    drawing = False
                    end_pos = event.pos
                    if end_pos[1] >= CANVAS_HEIGHT: end_pos = (end_pos[0], CANVAS_HEIGHT - 1)

                    if active_tool == 'line':
                        pygame.draw.line(canvas, boundary_color, start_pos, end_pos, 2)
                    elif active_tool == 'rect':
                        rect = pygame.Rect(start_pos, (end_pos[0] - start_pos[0], end_pos[1] - start_pos[1]))
                        rect.normalize()
                        pygame.draw.rect(canvas, boundary_color, rect, 2)
                    elif active_tool == 'circle':
                        dx = end_pos[0] - start_pos[0]
                        dy = end_pos[1] - start_pos[1]
                        radius = int(math.sqrt(dx * dx + dy * dy))
                        if radius > 0:
                            pygame.draw.circle(canvas, boundary_color, start_pos, radius, 2)

        # --- Animation Step ---
        if active_filler:
            try:
                next(active_filler)
            except StopIteration:
                active_filler = None

        # --- Drawing ---
        screen.fill((50, 50, 60))  # Dark UI background
        screen.blit(canvas, (0, 0))

        # UI Panel
        pygame.draw.rect(screen, (230, 230, 240), (0, CANVAS_HEIGHT, SCREEN_WIDTH, UI_HEIGHT))

        # Draw tool buttons
        for tool, rect in tool_buttons.items():
            is_active = active_tool == tool
            pygame.draw.rect(screen, (180, 190, 220) if is_active else (210, 210, 220), rect, border_radius=5)
            pygame.draw.rect(screen, (60, 70, 100) if is_active else (150, 150, 150), rect, 2, 5)
            label = tool.replace('_', '-').title()
            text = font.render(label, True, (0, 0, 0))
            screen.blit(text, text.get_rect(center=rect.center))

        # Draw clear button
        pygame.draw.rect(screen, (220, 180, 180), clear_button, border_radius=5)
        pygame.draw.rect(screen, (100, 60, 60), clear_button, 2, 5)
        text = font.render("Clear", True, (0, 0, 0))
        screen.blit(text, text.get_rect(center=clear_button.center))

        # Draw color palette and info
        info_text = font.render("Left-click to set Boundary | Right-click to set Fill", True, (50, 50, 50))
        screen.blit(info_text, (margin, CANVAS_HEIGHT + 55))
        for color, rect in color_buttons.items():
            pygame.draw.rect(screen, color, rect, border_radius=4)
            if color == boundary_color:
                pygame.draw.rect(screen, (0, 0, 0), rect, 3, 4)
            if color == fill_color:
                pygame.draw.rect(screen, (0, 0, 0), (rect.x + 2, rect.y + 2, rect.width - 4, rect.height - 4), 2, 4)

        # Draw dynamic preview
        if drawing and start_pos and active_tool in ['line', 'rect', 'circle']:
            current_pos = pygame.mouse.get_pos()
            if current_pos[1] >= CANVAS_HEIGHT: current_pos = (current_pos[0], CANVAS_HEIGHT - 1)

            if active_tool == 'line':
                pygame.draw.line(screen, (100, 100, 100), start_pos, current_pos, 1)
            elif active_tool == 'rect':
                rect = pygame.Rect(start_pos, (current_pos[0] - start_pos[0], current_pos[1] - start_pos[1]))
                rect.normalize()
                pygame.draw.rect(screen, (100, 100, 100), rect, 1)
            elif active_tool == 'circle':
                dx = current_pos[0] - start_pos[0]
                dy = current_pos[1] - start_pos[1]
                radius = int(math.sqrt(dx * dx + dy * dy))
                if radius > 0:
                    pygame.draw.circle(screen, (100, 100, 100), start_pos, radius, 1)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()

