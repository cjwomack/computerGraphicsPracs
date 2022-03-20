# COSC3000 Practicals:

### Introduction
Welcome to the COSC3000 pracs! In these sessions we'll be going though the practical details of graphics programming. We'll be using PyOpenGL for instructing, but don't fear, the same concepts will apply in C++, Unity, Blender, or whatever tool you want to use.

OpenGL is pretty large, in my own opinion this is the sort of progression that is typical in learning it:

- Beginner (How does this thing even work?):
    - Importing libraries, getting a feel for the environment, drawing a window with a filled background colour
    - Storing vertices in memory, writing a first shader and drawing a triangle
    - Loading in textures
    - Using linear algebra to apply transformations
    - Loading Obj models (even if it's just a cube, writing vertex lists by hand is not fun)
- Intermediate (This is fun! Now how do I...):
    - Lighting (including multiple lights)
    - Billboards
    - Getting multiple shaders running at the same time
    - Framebuffers/Simple Post Processing effects
    - Text
    - Materials (composite textures consisting of Diffuse maps, Normal maps, specular maps, heightmaps etc)
- Advanced (Cool effects, and starting to render in more Advanced ways):
    - Bloom
    - Shadows
    - Stencil Buffer
    - Instanced Rendering
    - Deferred Shading
    - Screen Space Ambient Occlusion

These practical sessions will mostly be focusing on the Beginner and Intermediate topics.

### Overview of Libraries:
In our sessions we'll be using a few libaries, they can all be pip installed.
- [pyOpenGL](http://pyopengl.sourceforge.net/): handles OpenGL up to 4.4, including extensions. The standard install includes PyOpenGL accelerate, which, it seems, is just designed to spit out an error message every time the program runs. All jokes aside, it seems to be built for an older version of numpy, and hasn't been updated. I've heard that rolling back numpy to some previous version fixes the issue, but that's never really worked in my experience. Also, it doesn't really break the program besides the error message.
- [numpy](https://numpy.org/): Two major use cases here,
    1. Standard lists and tuples in python don't work in pyOpenGL. Long story short, it's because Python has composite data types, even a floating point number isn't a float, it's float class. Numpy converts and stores these weird frankenstein types into arrays of simple numbers, just the way our graphics card likes it.
    1. Linear algebra, vectors and matrices for transformations.
- [pyrr](https://pyrr.readthedocs.io/en/latest/): Numpy is great for making matrices, but if there's no single function to create, for example, a rotation transformation. Pyrr is a wrapper around numpy which is extremely useful for making all sorts of transformations. The library is also very readable, so you can navigate into the source code and see exactly how they use numpy to build transformations.
- [pygame](https://www.pygame.org/news): The last thing we need is a windowing library, to make a window we can draw to, and handle key and mouse input. The two major options are GLFW or SDL, they are essentially equivalent, although in my experience I find GLFW is a little easier to use with C++ and Pygame/SDL is a little easier to use with Python. Pygame is a Python wrapper around SDL (simple direct media layer). Side note, Unreal engine also uses SDL.

To start with, let's install all of these, run the following commands in your Python development environment:
```python
pip install PyOpenGL PyOpenGL_accelerate
```
```python
pip install numpy
```
```python
pip install pyrr
```
```python
pip install pygame
```
With that out of the way, we should be ready for the prac exercises!