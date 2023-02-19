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
            m2=pyrr.matrix44.create_from_z_rotation(
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

    def __init__(
        self, position: list[float], 
        eulers: list[float], scale: list[float]):
        """ Initialize a triangle with the given scale."""

        super().__init__(position, eulers)
        self.scale = np.array(scale, dtype = np.float32)
    
    def update(self) -> None:
        """
            Update the triangle.
        """

        self.eulers[2] += 0.25
        if self.eulers[2] > 360:
            self.eulers[2] -= 360
    
    def get_model_transform(self) -> np.ndarray:

        return pyrr.matrix44.multiply(
            m1 =  pyrr.matrix44.create_from_scale(
                scale = self.scale,
                dtype = np.float32
            ),
            m2 = super().get_model_transform()
        )

class Player(Triangle):
    """ A player character """


    def __init__(self, position, eulers, scale):
        """ Initialise a player character. """
        
        super().__init__(position, eulers, scale)
        self.camera = None
    
    def update(self, target: Triangle) -> None:
        """
            Update the player.

            Parameters:

                target: the triangle to move towards.
        """

        if target is not None:
            self.move_towards(target.position, 0.1)

    def move_towards(self, targetPosition: np.ndarray, amount: float) -> None:
        """
            Move towards the given point by the given amount.
        """
        directionVector = targetPosition - self.position
        angle = np.arctan2(-directionVector[1],directionVector[0])
        self.move(angle, amount)
    
    def move(self, direction: float, amount: float) -> None:
        """
            Move by the given amount in the given direction (in radians).
        """
        self.position[0] += amount * np.cos(direction, dtype=np.float32)
        self.position[1] -= amount * np.sin(direction, dtype=np.float32)
        self.camera.position[0] += amount * np.cos(direction, dtype=np.float32)
        self.camera.position[1] -= amount * np.sin(direction, dtype=np.float32)
        self.eulers[2] = np.degrees(direction) - 45

class Camera(Entity):
    """ A third person camera controller. """

    def __init__(self, position):

        super().__init__(position, eulers = [0,0,0])

        self.forwards = np.array([0, 0, 0],dtype=np.float32)
        self.right = np.array([0, 0, 0],dtype=np.float32)
        self.up = np.array([0, 0, 0],dtype=np.float32)

        self.localUp = np.array([0, 0, 1], dtype=np.float32)
        self.targetObject: Entity = None

    def update(self) -> None:
        """ Updates the camera """

        self.calculate_vectors_cross_product()
    
    def calculate_vectors_cross_product(self) -> None:
        """ 
            Calculate the camera's fundamental vectors.

            There are various ways to do this, this function
            achieves it by using cross products to produce
            an orthonormal basis.
        """
        
        #TODO: set the camera's forwards vector so it's always looking towards its
        #       target object.
        self.forwards = None
        self.right = pyrr.vector.normalize(pyrr.vector3.cross(self.forwards, self.localUp))
        self.up = pyrr.vector.normalize(pyrr.vector3.cross(self.right, self.forwards))

    def get_view_transform(self) -> np.ndarray:
        """ Return's the camera's view transform. """

        #TODO: return a look_at vector from the camera
        #       towards its target object
        return None

class Scene:
    """ 
        Manages all logical objects in the game,
        and their interactions.
    """

    def __init__(self):

        self.player = Player(
            position = [0,1,0],
            eulers = [0,0,0],
            scale = [1,1,1]
        )
        self.camera = Camera(position = [-3,1,3])
        self.player.camera = self.camera
        self.camera.targetObject = self.player

        self.click_dots: list[Entity] = []

        #make row of triangles
        self.triangles: list[Entity] = []
        for x in range(1,16,3):
            self.triangles.append(
                Triangle(
                    position = [x,1,0.5],
                    eulers = [0,0,0],
                    scale = [0.5, 0.5, 0.5],
                )
            )
    
    def update(self) -> None:
        """ 
            Update all objects managed by the scene.
        """

        for triangle in self.triangles:
            triangle.update()
        for dot in self.click_dots:
            dot.update()
        targetDot = None
        if len(self.click_dots) > 0:
            targetDot = self.click_dots[0]
        self.player.update(targetDot)
        self.camera.update()

        #check if dot can be deleted
        if targetDot is not None:
            if pyrr.vector.length(targetDot.position - self.player.position) < 0.1:
                self.click_dots.pop(self.click_dots.index(targetDot))
    
    def lay_down_dot(self, position: list[float]) -> None:
        """ Drop a dot at the given position """

        self.click_dots.append(
            Triangle(
                position = position,
                eulers = [0,0,0],
                scale = [0.1, 0.1, 0.1],
            )
        )
    
    def move_camera(self, dPos: np.ndarray) -> None:
        """
            Move the camera by the given amount in its fundamental vectors.
        """

        #TODO: shift the camera's position, use the components of dPos
        #       as coefficients for a linear combination of the
        #       camera's direction vectors
        pass

class App:
    """ The main program """


    def __init__(self):
        """ Set up the program """
        
        self.set_up_pygame()
        
        self.make_assets()
        
        self.set_onetime_uniforms()

        self.get_uniform_locations()

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
    
    def set_onetime_uniforms(self) -> None:
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
        self.viewMatrixLocation = glGetUniformLocation(self.shader, "view")
    
    def mainLoop(self):

        glClearColor(0.1, 0.2, 0.2, 1)
        glEnable(GL_DEPTH_TEST)
        running = True

        while (running):

            #check events
            for event in pg.event.get():
                if (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    running = False
                if (event.type == pg.QUIT):
                    running = False
                if (event.type == pg.MOUSEBUTTONDOWN):
                    self.handleMouse()
            
            self.handleKeys()
            
            #update scene
            self.scene.update()
            
            #refresh screen
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glUseProgram(self.shader)

            glUniformMatrix4fv(
                self.viewMatrixLocation, 1, GL_FALSE, 
                self.scene.camera.get_view_transform()
            )

            glUniformMatrix4fv(
                self.modelMatrixLocation,
                1,GL_FALSE,
                self.scene.player.get_model_transform()
            )
            glBindVertexArray(self.triangle_mesh.vao)
            glDrawArrays(GL_TRIANGLES, 0, self.triangle_mesh.vertex_count)

            for triangle in self.scene.triangles:
                glUniformMatrix4fv(
                    self.modelMatrixLocation,
                    1,GL_FALSE,
                    triangle.get_model_transform()
                )
                glDrawArrays(GL_TRIANGLES, 0, self.triangle_mesh.vertex_count)
            
            for dot in self.scene.click_dots:
                glUniformMatrix4fv(
                    self.modelMatrixLocation,
                    1,GL_FALSE,
                    dot.get_model_transform()
                )
                glDrawArrays(GL_TRIANGLES, 0, self.triangle_mesh.vertex_count)

            pg.display.flip()

            #timing
            self.clock.tick(60)
        self.quit()
    
    def handleKeys(self):

        keys = pg.key.get_pressed()
        camera_movement = [0,0,0]

        if keys[pg.K_w]:
            #up
            camera_movement[2] += 1
        if keys[pg.K_a]:
            #left
            camera_movement[1] -= 1
        if keys[pg.K_s]:
            #down
            camera_movement[2] -= 1
        if keys[pg.K_d]:
            #right
            camera_movement[1] += 1
            
        dPos = 0.1 * np.array(
            camera_movement,
            dtype = np.float32
        )

        self.scene.move_camera(dPos)
    
    def handleMouse(self):

        #fetch camera's vectors
        forward = self.scene.camera.forwards
        up = self.scene.camera.up
        right = self.scene.camera.right

        #get mouse's displacement from screen center
        (x,y) = pg.mouse.get_pos()
        rightAmount = (x - self.screenWidth//2)/self.screenWidth
        upAmount = (self.screenHeight//2 - y)/self.screenWidth

        #TODO: get the resultant vector by a linear combination of the camera's vectors.
        resultant = None

        #trace from camera's position until we hit the ground
        if (resultant[2] < 0):
            #TODO: grab a copy of the camera's position
            x = None
            y = None
            z = None
            while (z > 0):
                #TODO: step forward by the resultant vector
                pass
            self.scene.lay_down_dot(
                position = [x,y,0]
            )
    
    def quit(self):
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