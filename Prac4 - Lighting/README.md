# COSC3000 Practical 4:
## Lighting

In this practical session we'll have a look at shader programming, get one light working with Blinn-Phong lighting, then multiple lights, plus a bonus extra.

### One Light
Open the "startPoint" folder and run it, you should see a single spinning cube, we're going to add a light to this scene. To start, let's add a light class:
```python
class Light:


    def __init__(self, position, color, strength):

        self.position = np.array(position, dtype=np.float32)
        self.color = np.array(color, dtype=np.float32)
        self.strength = strength
```

The light object stores parameters which will be useful in lighting the scene, for a single pointlight. Now we can create a light object in our scene:
```python
class Scene:


    def __init__(self):

        self.cubes = [
            Cube(
                position = [6,0,0],
                eulers = [0,0,0]
            ),
        ]

        self.lights = [
            Light(
                position = [4, 0, 0],
                color = [1, 0, 0],
                strength = 8
            ),
        ]

        self.player = Player(
            position = [0,0,2]
        )
```
Now let's set up our shader so that it can use the lighting information. We're going to do our lighting on a per-fragment basis, so most of the lighting code will occur in the fragment shader, however we will need to take in data from the mesh (in the vertex shader). Essentially, to calculate lighting accurately, we'll need the position and normal of fragment we're lighting.
Here's the vertex shader:
```
#version 330 core

layout (location=0) in vec3 vertexPos;
layout (location=1) in vec2 vertexTexCoord;
layout (location=2) in vec3 vertexNormal;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

out vec2 fragmentTexCoord;
out vec3 fragmentPosition;
out vec3 fragmentNormal;

void main()
{
    gl_Position = projection * view * model * vec4(vertexPos, 1.0);
    fragmentTexCoord = vertexTexCoord;
    fragmentPosition = (model * vec4(vertexPos, 1.0)).xyz;
    fragmentNormal = mat3(model) * vertexNormal;
}
```
We take in three attributes per vertex: position, texture coordinate (this will be covered in greater depth in a future lab), and normal. We also take as uniforms (global variables) some transformation matrices, and we output (ie. pass along to the fragment shader) the texture coordinate, position and normal of the fragment we want to draw.
It's worth noting how we take the mat3 version of model to handle the normal vector. Essentially, a full mat4 can describe rotations and translations, whereas a mat3 can just describe rotations. There are more computationally expensive formulas we can use, but so long as we don't apply any non-uniform scaling, this is an acceptable shortcut.

Now let's have a look at the data declarations for our fragment shader:
```
#version 330 core

struct PointLight {
    vec3 position;
    vec3 color;
    float strength;
};

in vec2 fragmentTexCoord;
in vec3 fragmentPosition;
in vec3 fragmentNormal;

uniform sampler2D imageTexture;
uniform PointLight Light;
uniform vec3 cameraPosition;

out vec4 color;

vec3 calculatePointLight(PointLight light, vec3 fragPosition, vec3 fragNormal);
```
PointLight is a composite data type (a struct), more or less a bunch of data bundled together. Here we can see that we're taking in the same data that our vertex shader was passing out. It's possible to output data from a vertex shader and then ignore it in the fragment shader (weird, but legal), however every input for the fragment shader must be provided. The names also (generally) have to match.
We've also declared that our shader will have some sort of function to calculate the effect of a pointlight on a fragment.
With that out of the way we can go on to write our main function:
```
void main()
{
    vec3 temp = vec3(0);

    temp += calculatePointLight(Light, fragmentPosition, fragmentNormal);

    color = vec4(temp, 1);
}
```
And the actual code for the pointlight function:
```
vec3 calculatePointLight(PointLight light, vec3 fragPosition, vec3 fragNormal) {

    vec3 baseTexture = texture(imageTexture, fragmentTexCoord).rgb;
    vec3 result = vec3(0);

    //geometric data
    vec3 fragLight = light.position - fragPosition;
    float distance = length(fragLight);
    fragLight = normalize(fragLight);
    vec3 fragCamera = normalize(cameraPosition - fragPosition);
    vec3 halfVec = normalize(fragLight + fragCamera);

    //ambient
    result += 0.2 * baseTexture;

    //diffuse
    result += light.color * light.strength * max(0.0, dot(fragNormal, fragLight)) / (distance * distance) * baseTexture;

    //specular
    result += light.color * light.strength * pow(max(0.0, dot(fragNormal, halfVec)),32) / (distance * distance);

    return result;
}
```

With that, our shader is done. We now have to set up our GraphicsEngine class to pass the light info from the scene to the shader. In the __init__ function:
```python
class GraphicsEngine:


    def __init__(self):

        #initialise pygame
        ...
        #initialise opengl
        ...
        self.modelMatrixLocation = glGetUniformLocation(self.shader, "model")
        self.viewMatrixLocation = glGetUniformLocation(self.shader, "view")
        self.lightLocation = {
            "position": glGetUniformLocation(self.shader, "Light.position"),
            "color": glGetUniformLocation(self.shader, "Light.color"),
            "strength": glGetUniformLocation(self.shader, "Light.strength")
        }
        self.cameraPosLoc = glGetUniformLocation(self.shader, "cameraPostion")
```

And then in the render function:

```python
def render(self, scene):

    #refresh screen
    ...

    glUniformMatrix4fv(self.viewMatrixLocation, 1, GL_FALSE, scene.player.viewTransform)

    light = scene.lights[0]
    glUniform3fv(self.lightLocation["position"], 1, light.position)
    glUniform3fv(self.lightLocation["color"], 1, light.color)
    glUniform1f(self.lightLocation["strength"], light.strength)

    glUniform3fv(self.cameraPosLoc, 1, scene.player.position)

    for cube in scene.cubes:

        ...

    pg.display.flip()
```
And that's it! Our lighting system should now be working! Run the code to verify it's working. To make the specular lighting more obvious, switch the specular color out:
```
    //specular
    result += vec3(1.0) * light.strength * pow(max(0.0, dot(fragNormal, halfVec)),32) / (distance * distance);
```

### Multiple Lights
Multiple lights are actually surprisingly simple to set up. In the previous section we declared the scene's lights as a list of objects, so let's go ahead and fill it up.
In scene __init__:
```python
def __init__(self):

        self.cubes = [
            Cube(
                position = [6,0,0],
                eulers = [0,0,0]
            ),
        ]

        self.lights = [
            Light(
                position = [
                    np.random.uniform(low=3.0, high=9.0), 
                    np.random.uniform(low=-2.0, high=2.0), 
                    np.random.uniform(low=2.0, high=4.0)
                ],
                color = [
                    np.random.uniform(low=0.1, high=1.0), 
                    np.random.uniform(low=0.1, high=1.0), 
                    np.random.uniform(low=0.1, high=1.0)
                ],
                strength = 3
            )
            for i in range(8)
        ]

        self.player = Player(
            position = [0,0,2]
        )
```
This will create 8 lights around the cube at random positions and colors.

Now let's update the fragment shader:

```
#version 330 core

struct PointLight {
    vec3 position;
    vec3 color;
    float strength;
};

in vec2 fragmentTexCoord;
in vec3 fragmentPosition;
in vec3 fragmentNormal;

uniform sampler2D imageTexture;
uniform PointLight Lights[8];
uniform vec3 cameraPosition;

out vec4 color;

vec3 calculatePointLight(PointLight light, vec3 fragPosition, vec3 fragNormal);

void main()
{
    //ambient
    vec3 temp = 0.2 * texture(imageTexture, fragmentTexCoord).rgb;

    for (int i = 0; i < 8; i++) {
        temp += calculatePointLight(Lights[i], fragmentPosition, fragmentNormal);
    }

    color = vec4(temp, 1);
}

vec3 calculatePointLight(PointLight light, vec3 fragPosition, vec3 fragNormal) {

    vec3 baseTexture = texture(imageTexture, fragmentTexCoord).rgb;
    vec3 result = vec3(0);

    //geometric data
    vec3 fragLight = light.position - fragPosition;
    float distance = length(fragLight);
    fragLight = normalize(fragLight);
    vec3 fragCamera = normalize(cameraPosition - fragPosition);
    vec3 halfVec = normalize(fragLight + fragCamera);

    //diffuse
    result += light.color * light.strength * max(0.0, dot(fragNormal, fragLight)) / (distance * distance) * baseTexture;

    //specular
    result += light.color * light.strength * pow(max(0.0, dot(fragNormal, halfVec)),32) / (distance * distance);

    return result;
}
```
Now in our uniform we're going to take an array of 8 pointlights. Depending on your system you might be able to define more lights, or less.
How could we define more lights? A quick solution is to store the eight closest lights to each model, load them in, render the model, then reset lighting for the next model. Another solution (outside the scope of this course) is to look into a more advanced technique like deferred shading.
We'll now grab the model locations for the lights, in GraphicsEngine __init__:
```python
def __init__(self):

        #initialise pygame
        ...
        #initialise opengl
        ...
        self.viewMatrixLocation = glGetUniformLocation(self.shader, "view")
        self.lightLocation = {
            "position": [
                glGetUniformLocation(self.shader, f"Lights[{i}].position")
                for i in range(8)
            ],
            "color": [
                glGetUniformLocation(self.shader, f"Lights[{i}].color")
                for i in range(8)
            ],
            "strength": [
                glGetUniformLocation(self.shader, f"Lights[{i}].strength")
                for i in range(8)
            ]
        }
        self.cameraPosLoc = glGetUniformLocation(self.shader, "cameraPostion")
```
So the locations are stored in a dictionary, we can modify the render function:
```python
def render(self, scene):

        #refresh screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.shader)

        glUniformMatrix4fv(self.viewMatrixLocation, 1, GL_FALSE, scene.player.viewTransform)

        for i,light in enumerate(scene.lights):
            glUniform3fv(self.lightLocation["position"][i], 1, light.position)
            glUniform3fv(self.lightLocation["color"][i], 1, light.color)
            glUniform1f(self.lightLocation["strength"][i], light.strength)

        glUniform3fv(self.cameraPosLoc, 1, scene.player.position)

        for cube in scene.cubes:

            glUniformMatrix4fv(self.modelMatrixLocation,1,GL_FALSE,cube.modelTransform)
            self.wood_texture.use()
            glBindVertexArray(self.cube_mesh.vao)
            glDrawArrays(GL_TRIANGLES, 0, self.cube_mesh.vertex_count)

        pg.display.flip()
```
Run the program and there we have it! Multiple lights! Of course it's a little hard to make out since we can't really see the lights at their positions.

### Creative Effect: Showing the lights
One approach to visualize the lights is to create a separate shader with no lighting applied (after all, lights don't shine on themselves) and use it to draw lights. Load up the billboards folder to see an example of this in action.