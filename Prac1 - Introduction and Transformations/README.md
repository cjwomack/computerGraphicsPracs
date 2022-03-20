# COSC3000 Practical 1:
## Introduction to PyOpenGL, basic drawing and transformations

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

### Hello Window!
Inspect the file window.py, read through each line and try to understand what it does. Add comments to describe any lines which may be hard to remember. Writing your own bits of documentation can be an incredibly useful way of learning code. Run the program and check that it works, try changing the background colour of the window.

### Hello Triangle!
OpenGL takes a bit of work to get things started, but once we have that, later steps get a lot easier. Open the triangle folder and look at the startpoint, there are two major steps we need to take.
#### Making Vertex Data
We'll make a triangle object for our program.
```python
class Triangle:


    def __init__(self, shader):

        
        # x, y, z, r, g, b
        self.vertices = (
            -0.5, -0.5, 0.0, 1.0, 0.0, 0.0,
             0.5, -0.5, 0.0, 0.0, 1.0, 0.0,
             0.0,  0.5, 0.0, 0.0, 0.0, 1.0
        )
        self.vertices = np.array(self.vertices, dtype=np.float32)

        self.vertex_count = 3
```
Note that here each vertex is written on a new line for ease of readability, the numbers are otherwise all packed together. This is optimal as it's more or less the way our graphics card reads data (flat memory layout, cache adjacency and so forth). Each vertex has 6 numbers, of the form (x,y,z,r,g,b). This might seem a little strange if we're used to vertices just being positions in 3D space. Turns out they aren't! Here we can define a vertex as a piece of data. That is, position data, colour data, and possibly other things. Note that we can define the vertices as a list or tuple, then simply convert it to a numpy array. We need to specify the data type as 32 bit float, because numpy uses 64 bit floats by default and if we do that openGL will simply draw nothing, or draw unpredictably, all while giving no error message!

```python
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
```
Next we need to send this data chunk, this vertex buffer, over to the GPU. glGenBuffers() allocates space on the GPU, and returns an unsigned integer which we can use to refer to that location. When we bind that buffer as the current array buffer we're telling openGL "Ok, when I do array buffer work, I want you to work on this particular buffer, index number (who knows, 5?)" If it helps you to understand this better, try printing self.vbo (which stands for Vertex Buffer Object), try running glGenBuffers a few times and printing out the result.

```python
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))
        
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))
```
It's not enough to just send the data over to the GPU, a vertex buffer by itself is just big, dumb data. We need to tell openGL how the information is packed in together and what it means. position and colour are attributes of the data, and we need to create attribute pointers so that openGL knows how to fetch them. The syntax for this is

glVertexAttribPointer(GLuint index, GLint size, GLenum type, GLboolean normalized, GLsizei stride, const void * pointer);

- index (GL unsigned integer): the index of the attribute. Position is attribute 0, colour is attribute 1
- size (GL integer): how many numbers describe the attribute. Attributes can have between 1 and 4 numbers (inclusive). Both position and colour take up three numbers
- type (GL enumeration): the data type, both are floating point data
- normalized (GL boolean): should openGL normalize the data to the range [-1,1]? False for both, and we'll probably never need this.
- stride (GL size, integer): stride is the "period" of the data in bytes. In other words, from the first x coordinate, how far will the program step to find the next x coordinate? Each vertex is 6 numbers, and each number is 32 bits (4 bytes), so the stride is 6 * 4 = 24.
- pointer (const void*): where does the data begin? A bit of bit level hackery is required to express this as a void pointer (a typeless memory offset), but don't be spooked, we're just doing that here, it doesn't come back, and when it does it always works the same way. Position starts at the start of the array, so an offset of 0 bytes. Colour starts after the first (x,y,z), so three numbers in, or an offset of 3 x 4= 12 bytes.

Side note: when you're learning a big library like OpenGL, looking up documentation for functions like this is incredibly important. For instance, I didn't include any notes on the arguments for glBufferData, if you haven't already, look that up and write a quick comment in your code explaining them. Don't worry about understanding everything the first time and commiting it to memory. As you resuse your code for larger projects you'll naturally build an understanding of it.

The vertex array object is created and bound before the vertex buffer object, because the vertex array object will actually remember both the vertex buffer and the attributes.

For completeness, here's the full Triangle class. Note the memory freeing code.
```python
class Triangle:


    def __init__(self, shader):

        # x, y, z, r, g, b
        self.vertices = (
            -0.5, -0.5, 0.0, 1.0, 0.0, 0.0,
             0.5, -0.5, 0.0, 0.0, 1.0, 0.0,
             0.0,  0.5, 0.0, 0.0, 0.0, 1.0
        )
        self.vertices = np.array(self.vertices, dtype=np.float32)

        self.vertex_count = 3

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))
        
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))

    def destroy(self):
        glDeleteVertexArrays(1,(self.vao,))
        glDeleteBuffers(1,(self.vbo,))
```

#### Writing our first shader
Before we can draw anything we need to write two shaders, a vertex and fragment shader. Let's make a new folder called "shaders", and in there make two new files: "vertex.txt" and "fragment.txt":

vertex.txt:
```
#version 330 core

layout (location=0) in vec3 vertexPos;
layout (location=1) in vec3 vertexColor;

out vec3 fragmentColor;

void main()
{
    gl_Position = vec4(vertexPos, 1.0);
    fragmentColor = vertexColor;
}
```
The vertex shader is responsible for determining a poin't position on screen, and generally applying any transformations if necessary. To set the position, we set openGL's inbuilt variable gl_Position. This is a 4 dimensional vector of the form (x,y,z,w), z = 0 corresponds to the triangle being at the screen's depth, w is 1 by default. What does this mean? Try changing the value once the program is complete, and seeing what happens! This will be discussed further in lecture 3, cameras and projection. We then pass the vertex's colour along to the fragment shader. Also note that the position is attribute 0 and the colour is attribute 1, just like we defined in our attribute pointers.

```
#version 330 core

in vec3 fragmentColor;

out vec4 color;

void main()
{
    color = vec4(fragmentColor, 1.0);
}
```
Fragments are pixels, the fragment shader's job is to tell openGL what colour a pixel should be, the color is a 4 dimensional vector of the form (r,g,b,a).

With those files written, we can return to our program and write a function that'll load, compile and link the shaders.

```python
from OpenGL.GL.shaders import compileProgram,compileShader
```

```python
def createShader(self, vertexFilepath, fragmentFilepath):

        with open(vertexFilepath,'r') as f:
            vertex_src = f.readlines()

        with open(fragmentFilepath,'r') as f:
            fragment_src = f.readlines()
        
        shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER),
                                compileShader(fragment_src, GL_FRAGMENT_SHADER))
        
        return shader
```
We can treat this as a black box (or a red box, or any colour, depending on what shader we're using haha I kid.), it is important to note that to be nit-picky, the text files we wrote were called shaders on their own, but together (linked and compiled), they're called a program. It's an unwritten rule to just call everything a shader though.

```python
#initialise opengl
glClearColor(0.1, 0.2, 0.2, 1)
self.shader = self.createShader("shaders/vertex.txt", "shaders/fragment.txt")
glUseProgram(self.shader)
self.triangle = Triangle()
self.mainLoop()
```
This is how we can go ahead and create our shader and triangle. The last part is to actually use them to draw!

```python
glClear(GL_COLOR_BUFFER_BIT)

glUseProgram(self.shader)
glBindVertexArray(self.triangle.vao)
glDrawArrays(GL_TRIANGLES, 0, self.triangle.vertex_count)

pg.display.flip()
```

Because the triangle vao remembers the buffer data and the attributes (ie, the stuff and what it means), it's enough to simply bind it then draw.

It's also good practice to clear any memory that was allocated (python doesn't usually allocate memory, but OpenGL does):
```python
def quit(self):
    self.triangle.destroy()
    glDeleteProgram(self.shader)
    pg.quit()
```

Run your program and observe the beautiful triangle! If your program isn't working, or you want to check your implementation, check the "finished" folder. Also don't forget to play around with that w value! tweak the line:
```
gl_Position = vec4(vertexPos, 1.0);
```
What does that last number seem to be doing?

### Transformed Triangle
So we have a triangle, what if we want to move it? We have two options:

- Change the vertex data on the CPU, then send that updated data to the GPU
- Keep the original data, but send a transformation matrix to the GPU each frame

Let's look at both.

#### Updating Vertex Data
Navigate to the folder "vertex data refresh", now we've been using a triangle, but once we start transforming things around, it's a good idea to separate the object from its representation, for that we'll make a Component class, which will just store a position and rotation and do nothing else.
```python
class Component:


    def __init__(self, position, eulers):

        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)
```
We'll then change our Triangle class to "TriangleMesh", just a personal preference of mine. The two fundamental asset types of a renderer are meshes and materials. Combinations of the two, along with data on where and how to draw them create rendered graphics. So with this convention we could, for example, have "Triangle", "TriangleMesh" and "TriangleMaterial" classes with no issues.
Anyway, let's tweak the TriangleMesh class a little.
```python
class TriangleMesh:


    def __init__(self):

        self.originalPositions = (
            -0.5, -0.5, 0.0, 1.0,
             0.5, -0.5, 0.0, 1.0,
             0.0,  0.5, 0.0, 1.0
        )
        self.originalColors = (
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 1.0
        )
        self.originalPositions = np.array(self.originalPositions, dtype=np.float32)
        self.originalPositions = np.reshape(
            a = self.originalPositions, 
            newshape = (3,4)
        )
        self.originalColors = np.array(self.originalColors, dtype=np.float32)
        self.originalColors = np.reshape(
            a = self.originalColors, 
            newshape = (3,3)
        )
        self.vertex_count = 3

        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)

        self.build_vertices(pyrr.matrix44.create_identity(dtype=np.float32))

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))
        
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(12))
```
The basic idea is we want to represent the fundamental data, unchanged, then have a function that takes a transformation matrix, applies it, and sends a transformed set of the data to the GPU. This function will also have to interweave the position and color data so we have a single array holding all the data.

Here it is:
```python
def build_vertices(self, transform):

    self.vertices = np.array([],dtype=np.float32)

    transformed_positions = pyrr.matrix44.multiply(
        m1 = self.originalPositions, 
        m2 = transform
    )

    for i in range(self.vertex_count):

        self.vertices = np.append(self.vertices, transformed_positions[i][0:3])
        self.vertices = np.append(self.vertices, self.originalColors[i])

    glBindVertexArray(self.vao)
    glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
    glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
```
Something fishy is going on! In the initialization code, the original positions were actually 4 dimensional, with (x,y,z,1) form, this was so that translation transformations could be applied, however when appending position data to the vertex buffer, we only grab elements [0,1,2] of each vector (hence the vector slice [0:3]).

Anyway, since we're transforming on the CPU side then sending over, our shaders don't need to be modified, let's have a look at how this all comes together in the app class:

```python
class App:
    def __init__(self):
        #initialise pygame
        pg.init()
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK,
                                    pg.GL_CONTEXT_PROFILE_CORE)
        pg.display.set_mode((640,480), pg.OPENGL|pg.DOUBLEBUF)
        self.clock = pg.time.Clock()
        #initialise opengl
        glClearColor(0.1, 0.2, 0.2, 1)
        self.shader = self.createShader("shaders/vertex.txt", "shaders/fragment.txt")
        glUseProgram(self.shader)

        self.triangle_mesh = TriangleMesh()

        self.triangle = Component(
            position = [0,0,-3],
            eulers = [0,0,0]
        )

        self.mainLoop()

    def createShader(self, vertexFilepath, fragmentFilepath):

        with open(vertexFilepath,'r') as f:
            vertex_src = f.readlines()

        with open(fragmentFilepath,'r') as f:
            fragment_src = f.readlines()
        
        shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER),
                                compileShader(fragment_src, GL_FRAGMENT_SHADER))
        
        return shader

    def mainLoop(self):
        running = True
        while (running):
            #check events
            for event in pg.event.get():
                if (event.type == pg.QUIT):
                    running = False
            
            #update triangle
            self.triangle.eulers[2] += 0.25
            if self.triangle.eulers[2] > 360:
                self.triangle.eulers[2] -= 360
            
            #refresh screen
            glClear(GL_COLOR_BUFFER_BIT)
            glUseProgram(self.shader)

            model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
            """
                pitch: rotation around x axis
                roll:rotation around z axis
                yaw: rotation around y axis
            """
            model_transform = pyrr.matrix44.multiply(
                m1=model_transform, 
                m2=pyrr.matrix44.create_from_eulers(
                    eulers=np.radians(self.cube.eulers), dtype=np.float32
                )
            )
            model_transform = pyrr.matrix44.multiply(
                m1=model_transform, 
                m2=pyrr.matrix44.create_from_translation(
                    vec=self.triangle.position,dtype=np.float32
                )
            )
            self.triangle_mesh.build_vertices(model_transform)
            glBindVertexArray(self.triangle_mesh.vao)
            glDrawArrays(GL_TRIANGLES, 0, self.triangle_mesh.vertex_count)

            pg.display.flip()

            #timing
            self.clock.tick(60)
        self.quit()

    def quit(self):
        self.triangle_mesh.destroy()
        glDeleteProgram(self.shader)
        pg.quit()
```
We can now run this and verify that it's working. Although this method of transformations is not the most efficient, the idea of updating vertex buffer data may be useful in other cases (eg. animation tweening).


#### Using Uniforms
Open the folder "transformed triangle/uniforms" and go to the startpoint. 

As before, we'll add a class to track the triangle, independent of its appearance:

```python
class Component:


    def __init__(self, position, eulers):

        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)
```

And, as before, we'll create a triangle and update it in the main loop.

```python
self.triangle_mesh = TriangleMesh()

self.triangle = Component(
    position = [0,0,-3],
    eulers = [0,0,0]
)
```

```python
#check events
for event in pg.event.get():
    if (event.type == pg.QUIT):
        running = False
            
#update triangle
self.triangle.eulers[2] += 0.25
if self.triangle.eulers[2] > 360:
    self.triangle.eulers[2] -= 360
```

Now in our shader we need to declare a uniform (a global parameter that can be passed to the shader), here's our code:

vertex.txt:
```
#version 330 core

layout (location=0) in vec3 vertexPos;
layout (location=1) in vec3 vertexColor;

uniform mat4 model;

out vec3 fragmentColor;

void main()
{
    gl_Position = model * vec4(vertexPos, 1.0);
    fragmentColor = vertexColor;
}
```

fragment.txt:
```
#version 330 core

in vec3 fragmentColor;

out vec4 color;

void main()
{
    color = vec4(fragmentColor, 1.0);
}
```
As you can see, very little has changed, just two lines in the vertex shader. Now we need to send the model matrix to the shader, we need to fetch the uniform location from the shader, then send the data in. Since the data will be sent every frame, it makes sense to fetch the location once at initialization and store that in a variable.
```python
glUseProgram(self.shader)

self.triangle_mesh = TriangleMesh()

self.triangle = Component(
    position = [0,0,-3],
    eulers = [0,0,0]
)

self.modelMatrixLocation = glGetUniformLocation(self.shader,"model")
```
The order of calls isn't super important, but we have to have called glUseProgram on a shader before we fetch a location from it. Otherwise OpenGL will give us an "Invalid operation" error.

As before, we'll build our model matrix each frame, but this time instead of using the matrix ourselves, we'll pass it over to the shader
```python
#refresh screen
glClear(GL_COLOR_BUFFER_BIT)
glUseProgram(self.shader)

model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
"""
    pitch: rotation around x axis
    roll:rotation around z axis
    yaw: rotation around y axis
"""
model_transform = pyrr.matrix44.multiply(
    m1=model_transform, 
    m2=pyrr.matrix44.create_from_eulers(
        eulers=np.radians(self.cube.eulers), dtype=np.float32
    )
)
model_transform = pyrr.matrix44.multiply(
    m1=model_transform, 
    m2=pyrr.matrix44.create_from_translation(
        vec=self.triangle.position,dtype=np.float32
    )
)
glUniformMatrix4fv(self.modelMatrixLocation,1,GL_FALSE,model_transform)
glBindVertexArray(self.triangle_mesh.vao)
glDrawArrays(GL_TRIANGLES, 0, self.triangle_mesh.vertex_count)
```
The new function here is glUniformMatrix4fv, what are its arguments? Look it up and write a quick documenting comment.

We can now run the program and check that it works. Which method do you prefer? Trick question, matrix multiplication is always faster on the GPU. Uniforms are best practice for transformations.

### Transformation Hierarchies, Scene Graphs
One interesting use of transformations is that they can be chained together. Load up the Maze Board program and tilt the board around with the arrow keys. The board tilts, and the pieces and ball tilt as well, although they're separate objects!
Let's a make crane, like in the lecture slides, using a similar technique. To save time, this has been coded up already. Open up the "crane" folder and inspect the source code. This includes some extra features not discussed, but it's a great example of a larger program with useful functions.