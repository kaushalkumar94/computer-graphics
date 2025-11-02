# Computer Graphics Learning Repository

Welcome to the **Computer Graphics** repository!

This project is created by [@kaushalkumar94](https://github.com/kaushalkumar94) for learning and experimenting with fundamental and advanced computer graphics algorithms. All code is written in **Python** and leverages the **PyOpenGL** and **Pygame** libraries to make the algorithms interactive and visually demonstrative.

## What's Covered in This Repository?

The repository contains hands-on implementations of several classic computer graphics algorithms and concepts. These are accompanied by interactive visualizations, making it an excellent resource for both learning and reference.

### List of Algorithms and Code Samples Included

- **Line Drawing Algorithms**
  - Bresenham's Line Drawing Algorithm (with PyOpenGL visualization)
  - Digital Differential Analyzer (DDA) Line Drawing Algorithm
- **Circle and Ellipse Drawing**
  - Midpoint Circle Algorithm
  - Midpoint Ellipse Algorithm
- **Polygon and Shape Drawing**
  - Drawing of rectangles, squares, triangles, and composite shapes using Bresenham's algorithm
- **Clipping Algorithms**
  - Cohen-Sutherland Line Clipping Algorithm
  - Weiler-Atherton Polygon Clipping Algorithm
- **Filling Algorithms**
  - Flood Fill Algorithm (4-connected and 8-connected, with visual demonstration)
  - Boundary Fill Algorithm (interactive)
  - Scan Line Polygon Fill Algorithm
- **Interactive Drawing Board**
  - A GUI drawing board for experimenting with line, rectangle, circle, ellipse, and triangle drawing and filling
- **Auxiliary Geometry Utilities**
  - Intersection and point-in-polygon checks, error statistics, and pattern-based line rendering

## Technologies and Libraries Used

- **Python** — All code is written in Python for readability and accessibility.
- **PyOpenGL** — Used for low-level graphics rendering and drawing primitives.
- **Pygame** — Provides the interactive GUI, window management, and event handling for drawing and algorithm visualization.

## How Is This Repository Useful?

- **Educational Resource:** The code and visualizations help demystify core graphics concepts, perfect for students, educators, or self-learners.
- **Reference Implementations:** Clean, direct implementations of core algorithms can be reused or adapted for assignments, projects, or research.
- **Interactive Experimentation:** The use of Pygame enables you to tweak parameters, draw your own shapes, and see algorithms in action.
- **Contribution Friendly:** You are welcome to fork the repo, suggest improvements, or add new algorithms.

## How to Use

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/kaushalkumar94/computer-graphics.git
   cd computer-graphics
   ```
2. **Install Dependencies:**
   ```bash
   pip install pygame PyOpenGL PyOpenGL_accelerate
   ```
3. **Run Code Samples:**
   - Each algorithm has its own `.py` file (e.g., `bresanham algo.py`, `line clipping.py`, `flood filling.py`, etc.).
   - Run any file using:
     ```bash
     python filename.py
     ```
   - For interactive exploration, try `drawing board.py`.

4. **Experiment and Learn:**
   - Modify code or parameters as you wish to see how the algorithms behave with different inputs.

## Covered Files and Algorithms (Summary)

- `bresanham algo.py` — Bresenham’s line algorithm (PyOpenGL)
- `simple DDA.py` — DDA line drawing (PyOpenGL)
- `drawing board.py` — Interactive drawing (lines, circles, ellipses, rectangles, triangles)
- `flood filling.py` — Flood and boundary fill algorithms (Pygame)
- `scan line.py` — Scan line polygon filling
- `line clipping.py` — Cohen-Sutherland line clipping (Pygame/OpenGL)
- `Weiler-Atherton.py` — Weiler-Atherton polygon clipping

---

Explore, experiment, and enjoy learning computer graphics!
