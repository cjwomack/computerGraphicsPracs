import pygame as pg
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram,compileShader
import numpy as np
import pyrr

def createShader(vertexFilepath: str, fragmentFilepath: str) -> int:
    """
        Compile and link a shader program from source.

        Parameters:

            vertexFilepath: filepath to the vertex shader source code (relative to this file)

            fragmentFilepath: filepath to the fragment shader source code (relative to this file)
        
        Returns:

            An integer, being a handle to the shader location on the graphics card
    """

    with open(vertexFilepath,'r') as f:
        vertex_src = f.readlines()

    with open(fragmentFilepath,'r') as f:
        fragment_src = f.readlines()
    
    shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER),
                            compileShader(fragment_src, GL_FRAGMENT_SHADER))
    
    return shader

class Entity:
    """ Represents a general object with a position and rotation applied"""


    def __init__(self, position: list[float], eulers: list[float]):
        """
            Initialize the entity, store its state and update its transform.

            Parameters:

                position: The position of the entity in the world (x,y,z)

                eulers: Angles (in degrees) representing rotations around the x,y,z axes.
        """

        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)
    
    def get_model_transform(self) -> np.ndarray:
        """
            Calculates and returns the entity's transform matrix,
            based on its position and rotation.
        """

        model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
        
        model_transform = pyrr.matrix44.multiply(
            m1=model_transform, 
            m2=pyrr.matrix44.create_from_y_rotation(
                theta = np.radians(self.eulers[2]), 
                dtype=np.float32
            )
        )

        model_transform = pyrr.matrix44.multiply(
            m1=model_transform, 
            m2=pyrr.matrix44.create_from_translation(
                vec=self.position,
                dtype=np.float32
            )
        )

        return model_transform

class Triangle(Entity):
    """ A triangle that spins. """
    
    def update(self) -> None:
        """
            Update the triangle.
        """

        self.eulers[2] += 0.25
        if self.eulers[2] > 360:
            self.eulers[2] -= 360

class Camera(Entity):
    """ A first person camera controller. """


    def __init__(self, position, eulers):

        super().__init__(position, eulers)

        #the camera's three fundamental directions: forwards, up & right
        self.localUp = np.array([0,0,1], dtype=np.float32)
        self.localRight = np.array([0,1,0], dtype=np.float32)
        self.localForwards = np.array([1,0,0], dtype=np.float32)

        #directions after rotation
        self.up = np.array([0,0,1], dtype=np.float32)
        self.right = np.array([0,1,0], dtype=np.float32)
        self.forwards = np.array([1,0,0], dtype=np.float32)
    
    def calculate_vectors_rotation(self) -> None:
        """ 
            Calculate the camera's fundamental vectors.

            There are various ways to do this, this function
            achieves it by building a rotation matrix from the
            camera's euler angles, and transforming the local directions.
        """

        pass
        
        """
            Task: construct a rotation matrix from the camera's
            euler angles, and use it to construct the camera's vectors.
        """

    def calculate_vectors_cross_product(self) -> None:
        """ 
            Calculate the camera's fundamental vectors.

            There are various ways to do this, this function
            achieves it by using cross products to produce
            an orthonormal basis.
        """

        #calculate the forwards vector directly using spherical coordinates
        self.forwards = np.array(
            [
                np.cos(np.radians(self.eulers[2])) * np.cos(np.radians(self.eulers[1])),
                np.sin(np.radians(self.eulers[2])) * np.cos(np.radians(self.eulers[1])),
                np.sin(np.radians(self.eulers[1]))
            ],
            dtype=np.float32
        )
        self.right = pyrr.vector.normalise(np.cross(self.forwards, self.localUp))
        self.up = pyrr.vector.normalise(np.cross(self.right, self.forwards))
    
    def update(self) -> None:
        """ Updates the camera """

        self.calculate_vectors_cross_product()
        
    def get_view_transform(self) -> np.ndarray:
        """ Return's the camera's view transform. """

        pass
        """
            Task: Make a lookat transform
        """
        return None

class Scene:
    """ 
        Manages all logical objects in the game,
        and their interactions.
    """


    def __init__(self):

        self.triangle = Triangle(
            position = [3,0,0],
            eulers = [0,0,0]
        )

        self.camera = Camera(
            position = [0,0,0],
            eulers = [0,0,0]
        )
    
    def update(self) -> None:
        """ 
            Update all objects managed by the scene.
        """

        self.triangle.update()
        self.camera.update()
    
    def move_camera(self, dPos: np.ndarray) -> None:
        """ Moves the camera by the given amount """

        self.camera.position += dPos
    
    def spin_camera(self, dEulers: np.ndarray) -> None:
        """ 
            Change the camera's euler angles by the given amount,
            performing appropriate bounds checks.
        """

        self.camera.eulers += dEulers

        #modular check: camera can spin full revolutions 
        # around z axis.
        if self.camera.eulers[2] < 0:
            self.camera.eulers[2] += 360
        elif self.camera.eulers[2] > 360:
            self.camera.eulers[2] -= 360
        
        #clamping: around the y axis (up and down),
        # we never want the camera to be looking fully up or down.
        self.camera.eulers[1] = min(89, max(-89, self.camera.eulers[1]))

class App:
    """ The main program """


    def __init__(self):
        """ Set up the program """

        self.set_up_pygame()
        
        self.make_assets()

        self.set_onetime_unforms()

        self.get_uniform_locations()

        self.set_up_input_systems()

        self.mainLoop()
    
    def set_up_pygame(self) -> None:
        """ Set up the pygame environment """
        self.screenWidth = 640
        self.screenHeight = 480
        pg.init()
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK,
                                    pg.GL_CONTEXT_PROFILE_CORE)
        pg.display.set_mode(
            (self.screenWidth, self.screenHeight), 
            pg.OPENGL|pg.DOUBLEBUF
        )
        self.clock = pg.time.Clock()

    def make_assets(self) -> None:
        """ Make any assets used by the App"""

        self.scene = Scene()
        self.triangle_mesh = TriangleMesh()
        self.shader = createShader("shaders/vertex.txt", "shaders/fragment.txt")
    
    def set_onetime_unforms(self) -> None:
        """ Set any uniforms which can simply get set once and forgotten """

        glUseProgram(self.shader)

        projection_transform = pyrr.matrix44.create_perspective_projection(
            fovy = 45, 
            aspect = self.screenWidth / self.screenHeight, 
            near = 0.1, far = 10, dtype = np.float32
        )
        glUniformMatrix4fv(
            glGetUniformLocation(self.shader, "projection"), 
            1, GL_FALSE, projection_transform
        )
    
    def get_uniform_locations(self) -> None:
        """ Query and store the locations of any uniforms on the shader """

        glUseProgram(self.shader)
        self.modelMatrixLocation = glGetUniformLocation(self.shader,"model")
        #TODO: get the view uniform location
        self.viewMatrixLocation = None
    
    def set_up_input_systems(self) -> None:
        """ Run any mouse/keyboard configuration here. """

        pg.mouse.set_visible(False)
        pg.mouse.set_pos(
            self.screenWidth // 2, 
            self.screenHeight // 2
        )

        #based on the combination of wasd,
        #an offset is applied to the camera's direction
        # when walking. w = 1, a = 2, s = 4, d = 8
        self.walk_offset_lookup = {
            1: 0,
            2: 90,
            3: 45,
            4: 180,
            6: 135,
            7: 90,
            8: 270,
            9: 315,
            11: 0,
            12: 225,
            13: 270,
            14: 180
        }
    
    def mainLoop(self) -> None:
        """ Run the App """

        glClearColor(0.1, 0.2, 0.2, 1)
        glViewport(0, 0, self.screenWidth, self.screenHeight)
        running = True

        while (running):
            #check events
            for event in pg.event.get():
                if (event.type == pg.QUIT) \
                    or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    running = False
            
            self.handleKeys()
            self.handleMouse()
            
            #update scene
            self.scene.update()
            
            #refresh screen
            glClear(GL_COLOR_BUFFER_BIT)
            glUseProgram(self.shader)

            #TODO: send the camera's view transform to the shader.

            glUniformMatrix4fv(
                self.modelMatrixLocation,
                1,GL_FALSE,
                self.scene.triangle.get_model_transform()
            )
            glBindVertexArray(self.triangle_mesh.vao)
            glDrawArrays(GL_TRIANGLES, 0, self.triangle_mesh.vertex_count)

            pg.display.flip()

            #timing
            self.clock.tick(60)

        self.quit()
    
    def handleKeys(self) -> None:
        """
            Handle keys.
        """

        combo = 0
        directionModifier = 0

        keys = pg.key.get_pressed()

        if keys[pg.K_w]:
            combo += 1
        if keys[pg.K_a]:
            combo += 2
        if keys[pg.K_s]:
            combo += 4
        if keys[pg.K_d]:
            combo += 8
        
        if combo in self.walk_offset_lookup:
            
            directionModifier = self.walk_offset_lookup[combo]
            
            dPos = 0.1 * np.array(
                [
                    np.cos(np.deg2rad(self.scene.camera.eulers[2] + directionModifier)),
                    np.sin(np.deg2rad(self.scene.camera.eulers[2] + directionModifier)),
                    0
                ],
                dtype = np.float32
            )

            self.scene.move_camera(dPos)

    def handleMouse(self) -> None:
        """
            Handle mouse movement.
        """

        (x,y) = pg.mouse.get_pos()
        theta_increment = (self.screenWidth / 2.0) - x
        phi_increment = (self.screenHeight / 2.0) - y
        dEulers = np.array([0, phi_increment, theta_increment], dtype=np.float32)
        self.scene.spin_camera(dEulers)
        pg.mouse.set_pos(self.screenWidth // 2, self.screenHeight // 2)
    
    def quit(self) -> None:
        """ Free any allocated memory """

        self.triangle_mesh.destroy()
        glDeleteProgram(self.shader)
        pg.quit()

class TriangleMesh:


    def __init__(self):

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
        
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1,(self.vbo,))

myApp = App()