# COSC3000 Practical 3:
## Hidden Surface Removal, Transparency, MSAA and LOD
In this practical we'll examine the depth buffer, different drawing orders and how they affect transparency, as well as looking at some more advanced topics like Multisample Antialiasing and Level of Detail.
### Model View Control refactor
Open up the startpoint of the "depth testing" folder, note how the code has been refactored into Model, View and Control sections. This is the sort of design I alluded to in the last prac. The breakdown is:

* model: Game objects (component, camera) and logic/manager (scene)
* view: Renderer (...) and engine assets (just meshes right now, materials will be added later)
* control: High level control of the program, runs the main loop, takes user input and measures framerate

The biggest change has been splitting up the app to extract the rendering code, but the benefit is that now the classes are much cleaner. Here the purpose/function of App is beautiful and clear:

```python
class App:


    def __init__(self):

        self.screenWidth = 640
        self.screenHeight = 480

        self.renderer = Renderer(self.screenWidth, self.screenHeight)
        self.scene = Scene()

        self.make_clock()

        self.mainLoop()
    
    def make_clock(self):

        ...

    def mainLoop(self):
        running = True
        while (running):
            #check events
            for event in pg.event.get():
                if (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    running = False
                if (event.type == pg.QUIT):
                    running = False
            
            self.handleKeys()
            self.handleMouse()
            
            #update scene
            rate = self.frameTime / 16
            self.scene.update(rate)

            #render
            self.renderer.render(self.scene)

            #timing
            self.calculateFramerate()

        self.quit()
    
    def handleKeys(self):

        ...

    def handleMouse(self):

        ...

    def calculateFramerate(self):

        ...
    
    def quit(self):
        self.renderer.destroy()
```

And the purpose of the renderer is similarly clear:

```python
class Renderer:


    def __init__(self, screenWidth, screenHeight):

        #initialise pygame
        ...

        #initialise opengl
        ...

        self.load_assets()

        self.set_onetime_shader_data()

        self.get_shader_locations()
    
    def set_onetime_shader_data(self):
        """
            Some data is only set once for the program, so its uniform location doesn't
            need to be stored.
        """

        ...

    def get_shader_locations(self):
        """
            Some data is set each frame, there can be a performance benefit in querying
            the uniform locations and saving them for reuse.
        """

        ...

    def load_assets(self):
        """
            Load/Create assets (eg. meshes and materials) that the renderer will use.
        """

        self.meshes = {
            "triangle": TriangleMesh(),
        }
    
    def render(self, scene):

        glClear(GL_COLOR_BUFFER_BIT)
        glUseProgram(self.shader)

        glUniformMatrix4fv(self.viewMatrixLocation, 1, GL_FALSE, scene.camera.viewTransform)

        for triangle in scene.triangles:
            glUniformMatrix4fv(self.modelMatrixLocation,1,GL_FALSE,triangle.modelTransform)
            mesh = self.meshes[triangle.meshType]
            glBindVertexArray(mesh.vao)
            glDrawArrays(GL_TRIANGLES, 0, mesh.vertex_count)

        pg.display.flip()
    
    def destroy(self):
        for (name,mesh) in self.meshes.items():
            mesh.destroy()
        glDeleteProgram(self.shader)
        pg.quit()
```

It's also worth noting that the renderer is now storing meshes in a dictionary, and querying them on an individual basis. This is to make the engine more general. It doesn't matter so much if we're just making one project, but if we want to make a general codebase that we can reuse for many projects, general code might be easier. 

You might (quite reasonably) be asking "But why give the scene a list of triangles, and then explicitly specify that each of them is a triangle object? Isn't that implied?" Well, yes, but the scene class might want to have its objects arranged in individual lists for its own purposes (eg. collision checking/interactions/ai). 

Anyway, let's run this program and, well, run around a bit and view the scene from a few angles. Does it look alright? Not quite! The triangles are drawn out of order! Let's address that.

### Depth Culling
By default, OpenGL will literally just draw things in the order that they're called. We do, however, have a framebuffer created for us that we can use. A framebuffer typically has three components:

* Color buffer: 32 bits, stores the RGBA color of each pixel on the screen
* Depth buffer: 24 bits, stores the  depth value of each pixel on the screen, typically the depth and stencil buffer are stored together to make a full 32 bits
* Depth buffer: 8 bits, stores extra info that can be used for custom pixel tests. Stencil buffer effects can get pretty creative, typically the depth and stencil buffer are stored together to make a full 32 bits

So our program is storing depth information for each pixel, we just need to enable a depth test! Before we do that, let's view the contents of the depth buffer. Change the fragment shader temporarily:

```
#version 330 core

in vec3 fragmentColor;

out vec4 color;

void main()
{
    //color = vec4(fragmentColor, 1.0);
    color = vec4(vec3(gl_FragCoord.z), 1.0);
}
```

Now if we run this, we can see that the depth buffer goes from 0 to 1, where 0 is closer and 1 is further, now let's enable depth testing and choose an appropriate depth test.

```python
#initialise opengl
        glClearColor(0.0, 0.0, 0.0, 1)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        ...
```

Think of each pixel like a bin, to draw a pixel, we throw new information in the bin, but before we do that, we can check what's in the bin already. More specifically, we only want to overwrite an existing pixel if we're overwriting it with a pixel with a lesser depth value. There's one thing we need to do as well,

```python
glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
```

We want to clear the color buffer as well as the depth buffer. Here we're using bitwise "or" to specify that we're clearing both buffers. This uses a bitmask pattern, similar to the way we handle key input for walking. If we ctrl+click into the definition we can see that these are special constants for OpenGL:
```python
GL_COLOR_BUFFER_BIT=_C('GL_COLOR_BUFFER_BIT',0x00004000)
GL_DEPTH_BUFFER_BIT=_C('GL_DEPTH_BUFFER_BIT',0x00000100)
```
So in other words, GL_COLOR_BUFFER_BIT, is a special bit pattern which refers just to the color buffer! (When I was learning this stuff for the first time that always confused me. "Yes, but I don't want to clear a bit, I want to clear the whole buffer!"). Anyway, so we can revert the fragment shader to its original and confirm that the program is using depth testing appropriately.

### Transparency

Now let's get transparency working, and see how order affects it. Change the fragment shader to add some transparency.

```
#version 330 core

in vec3 fragmentColor;

out vec4 color;

void main()
{
    color = vec4(fragmentColor, 0.5);
}
```

Here we're just fixing the transparency to 50%, which is acceptable for a simple demo. Save that, and run the program and...
and...

no change! It turns out alpha blending must be enabled, let's go ahead and set that.

```python
#initialise opengl
        ...
        glDepthFunc(GL_LESS)
        glEnable(GL_BLEND)
        ...
```
And now we can run it, and, still nothing. We also need to specify a blend function. The blend function based on the equation:
```
result_color = source_color * source_factor + destination_color * destination_factor
```
Here the result is the final pixel after blending, the source is the incoming pixel and destination is the existing pixel in the framebuffer. This is expressed in OpenGL as:
```
glBlendFunc(GLenum sfactor, GLenum dfactor)
```
So for traditional alpha blending we want
```
result_color = source_color * source_alpha + destination_color * (1 - source_alpha)
```
let's add that.
```python
#initialise opengl
        ...
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        ...
```
And now alpha blending is working! Let's investigate an interesting edge case though.

### Transparency is not order-independent
Open up the finished folder in the transparency section, try reversing the rectangles in the scene, does it affect the appearance of the objects?

### MultiSampling AntiAliasing
Load up the folder for MSAA, run it and note the appearance of the triangle boundary, see how the lines have jagged edges? We can fix that.

The quick solution is to jump into the renderer's create_framebuffer function and change the number of samples. Graphics cards won't let this value go above 16 as the visual improvement isn't that noticeable beyond 16 samples.

You aren't expected to understand how this code is working yet, but you are  encouraged to have a look at it. The basic idea is that while we have a default framebuffer created for us, we can also make some of our own and render to them. We create color buffers (textures) and depth/stencil buffers (renderbuffer objects, basically lightweight versions of textures with less features). We then do our multisample rendering and resolve the colorbuffer to a single sample texture. How do we draw that texture onto the screen? We fake it, by creating a rectangle the same size as the screen and adding the color buffer to it. This might be a little advanced at this early stage, but it is good to be aware of.