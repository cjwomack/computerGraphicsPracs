# COSC3000 Practical 5:
## Post Processing Effects

So far we've been rendering things in 3D, and it's been going well, but what if we want more control?\
Say for instance we want to render in black and white, simple enough. However if we want to blur an image or apply an edge filter then the fragment will need to know about its neighbours. A simple way to acheive this is to render the whole image to a texture first, and then apply operations on that texture. This is called post processing.\
In this practical we will:
- Render our scene to an intermediate texture
- Apply kernel effects such as blur and edge filters
- Apply UV mapping effects such as warping

### 1: Rendering to a texture
In order to render to a texture, we'll create a framebuffer. A framebuffer is a collection of all the resources used in rendering a frame.\
In our cases this is a color buffer and a depth/stencil buffer.
```python
class Framebuffer:
    """
        A simple framebuffer object, holds a color buffer and depth buffer which
        can be rendered to and read from.
    """

    
    def __init__(self, w: int, h: int):
        """
            Initialise the framebuffer.

            Parameters:
                w: the width of the screen
                h: the height of the screen
        """
        
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        
        self.make_color_buffer(w, h)
        
        self.make_depth_stencil_buffer(w, h)

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
```
The process of making a color buffer is pretty similar to making a regular texture, the most important thing is to declare it as the framebuffer's color attachment.\
In Framebuffer's make_color_buffer function:
```python
def make_color_buffer(self, w: int, h: int) -> None:
        """
            Initialise the framebuffer's color buffer.

            Parameters:
                w: the width of the screen
                h: the height of the screen
        """

        #create and bind the color buffer
        self.colorBuffer = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.colorBuffer)
        #preallocate space
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGB, 
            w, h,
            0, GL_RGB, GL_UNSIGNED_BYTE, None
        )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)
        #declare the framebuffer as color attachment 0 of the framebuffer
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, 
                                GL_TEXTURE_2D, self.colorBuffer, 0)
```
The depth/stencil buffer uses a renderbuffer object, which is essentially a storage image, a texture which isn't sampled.\
In Framebuffer's make_depth_stencil_buffer function:
```python
def make_depth_stencil_buffer(self, w: int, h: int) -> None:
        """
            Initialise the framebuffer's depth & stencil buffer.

            Parameters:
                w: the width of the screen
                h: the height of the screen
        """

        #create and bind, a render buffer is like a texture which can
        # be written to and read from, but not sampled (ie. not smooth)
        self.depthStencilBuffer = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self.depthStencilBuffer)
        #preallocate space, we'll use 24 bits for depth and 8 for stencil
        glRenderbufferStorage(
            GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, w, h
        )
        glBindRenderbuffer(GL_RENDERBUFFER,0)
        #specify this as the depth/stencil attachment of the framebuffer.
        # every framebuffer can have at most one of these.
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, 
                                    GL_RENDERBUFFER, self.depthStencilBuffer)
```
With the framebuffer constructed we can turn our attention to the shader. The purpose of this shader is to draw a two dimensional quadritateral, as such it's very simple.\
vertex_post.txt:
```
#version 330 core

layout (location=0) in vec2 vertexPos;
layout (location=1) in vec2 vertexTexCoord;

out vec2 fragmentTexCoord;

void main()
{
    gl_Position = vec4(vertexPos, 0.0, 1.0);
    fragmentTexCoord = vertexTexCoord;
}
```
fragment_post.txt:
```
#version 330 core

in vec2 fragmentTexCoord;

uniform sampler2D colorbuffer;

out vec4 color;

void main()
{
    color = vec4(vec3(texture(colorbuffer, fragmentTexCoord).r), 1.0);
}
```
Rendering everything is done in two passes:
```python
def render(
        self, camera: Player, 
        renderables: dict[int, list[Entity]]) -> None:
        """
            Render a frame.

            Parameters:

                camera: the camera to render from

                renderables: a dictionary of entities to draw, keys are the
                            entity types, for each of these there is a list
                            of entities.
        """

        #regular 3D rendering to our custom framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer.fbo)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        #draw sky
        glUseProgram(self.shaders[PIPELINE_SKY])
        # ...
        
        #Everything else
        glUseProgram(self.shaders[PIPELINE_3D])
        # ...
        
        #2D rendering from our custom framebuffer to the screen's framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_DEPTH_TEST)

        glUseProgram(self.shaders[PIPELINE_POST])
        #bind the texture we just rendered to as the texture we're now going to read from
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.framebuffer.colorBuffer)
        #draw a screen-sized quad
        glBindVertexArray(self.screenQuad.vao)
        glDrawArrays(GL_TRIANGLES, 0, self.screenQuad.vertex_count)

        glFlush()
```
And that's it! Our scene should now be showing in black and white.
### 2: Kernel Effects
Now that the whole screen is available to us as a texture, we can do a little more than just change its colors.
A kernel is defined as a matrix of coefficients, used to compute a weighted sum around a central fragment.
For examples of popular kernels, see [wikipedia](https://en.wikipedia.org/wiki/Kernel_(image_processing))

Open up the fragment post shader and try implementing a blur image kernel!

### 3: Heat Wave!
Another thing we can do, having access to the whole texture, is warp it somewhat.\
Let's say our character swims underwater or looks through a looking glass, some regions of the screen will be magnified and warped. this could be an interesting effect to look into for a project. \
\
For now the simplest thing we can do is add an offset to our screen coordinates:\
In fragment_post.txt:
```
#version 330 core
...
uniform float t;
...
//Function declarations
vec4 Edge();
vec4 Blur();
float Luminosity_Grayscale(vec3 color);
vec2 Warp();

//Function definitions
vec4 Edge() {

    vec2 texCoord = Warp();

    //apply kernel effect as usual
    ...
}

vec4 Blur() {

    vec2 texCoord = Warp();

    //apply kernel effect as usual
    ...
}

vec2 Warp() {
    const float amplitude = 0.01;
    return fragmentTexCoord + vec2(amplitude * sin(fragmentTexCoord.y * 20 + t), 0);
}

...
```
Here the offset depends on the y coordinate of the screen, but is also animated through time by the t uniform which the engine sends to the shader. Pretty cool! Next week we'll constrain this to just a portion of the world.