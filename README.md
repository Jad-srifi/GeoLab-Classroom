# GeoLab Classroom

GeoLab Classroom is an interactive geometry and graphing app made for students to learn by seeing, dragging, changing, and testing ideas in real time.

This project started development when I was in 10th grade. I first made it because I wanted to help my calssmates undersatnd geometry in a more visual way instead of just memorizig formulas from the board. After some time it started getting used in my school to help teach new gen students too, and it still keeps being updated little by little.

Now, and only now, I am open sourcing it so people across the world can use it, improve it, and keep updateing it with me.

## Why This Project Exists

- To help students understand geometry more intuatively
- To make formulas feel connected to movement and visuals
- To give teachers a simple classroom tool for showing concepts live
- To let students explore math instead of only memorizing steps

## What The App Can Do

- Create points, segments, triangles, rectangles, circles, and polygons
- Drag shapes and watch measurements and formulas update live
- Show graph presets and custom equations
- Use sliders for `a`, `b`, `c`, and `t`
- Show intersections between active graphs
- Add constraints like parallel, perpendicular, equal-length, and midpoint lock
- Run guided lesson flows
- Save and load scenes
- Translate, rotate, scale, and mirror shapes

## Install

This project uses `pygame-ce`.

```bash
python -m pip install -r requirements.txt
```

## Run The App

```bash
python Main.py
```

## How To Use The App

1. Open the app.
2. Use the left toolbar to choose a tool like `Select`, `Point`, or `Segment`.
3. Click on the main graph area to build shapes.
4. Switch back to `Select` with `V` to move objects or drag handles.
5. Use the right side panels:
   `DETAILS` shows measurements, formulas, constraints, and transform notes.
   `GRAPHS` shows sliders, starter graphs, and custom graph controls.
   `LEARN` shows lesson info, project goals, and improvement ideas.
6. Click the `>` button on the right panel if you want to close it and give more space to the graph.
7. Open a panel again by clicking its name in the right side rail.

## Main Commands

- `V`: Select mode
- `A`: Point tool
- `L`: Segment tool
- `T`: Triangle tool
- `R`: Rectangle tool
- `C`: Circle tool
- `P`: Polygon tool
- `Enter`: Finish a polygon
- `Delete`: Delete selected shape
- `G`: Toggle snap to grid
- `H`: Toggle help
- `I`: Toggle graph intersections
- `0`: Reset camera
- `Space`: Load demo scene
- `Esc`: Open pause menu
- `/`: Open commands screen
- `J`: Open guided lessons
- `F`: Open function builder
- `Tab`: Animate slider `t`
- `1`: Toggle Linear graph
- `2`: Toggle Parabola graph
- `3`: Toggle Sine graph
- `4`: Toggle Quadratic Lab graph
- `Ctrl+S`: Save scene
- `Ctrl+O`: Load scene
- `Shift+Click`: Pick comparison shape
- `Ctrl+1`: Parallel constraint
- `Ctrl+2`: Perpendicular constraint
- `Ctrl+3`: Equal-length constraint
- `Ctrl+4`: Midpoint lock
- `Arrow Keys`: Move selected shape
- `Q` / `E`: Rotate selected shape
- `-` / `=`: Scale selected shape
- `X`: Mirror across x-axis
- `Y`: Mirror across y-axis
- `O`: Mirror across origin
- `N`: Cycle next improvement ideas

## Student Notes

The main idea of this project is simple: if a student can drag the math and see it react, then the formula starts making more sense by itself.

I didnt want this to feel like a calculator only. I wanted it to feel like a classroom lab where students can test what happens, make mistakes, and then understand why the math works.

## Open Source Note

This is the first public open source version of GeoLab Classroom.

If you want to use it in a school, improve the code, add lessons, or make the UI better, you are welcome to do that. I want this project to keep growing and helping more students from different places.

## Project Structure

- `Main.py`: Starts the app
- `scripts/app/`: App state, layout, rendering, theme, lessons, sliders, persistence, and UI helpers
- `scripts/geometry/`: Geometry models, graph presets, formulas, and math utilities
- `requirements.txt`: Project dependencies
