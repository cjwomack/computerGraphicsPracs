import pygame as pg
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram,compileShader
import numpy as np
import pyrr

################### Model #####################################################

class Component:


    def __init__(self, position, eulers, meshType, color):

        self.position = np.array(position, dtype=np.float32)
        """
            pitch: rotation around x axis
            roll:rotation around z axis
            yaw: rotation around y axis
        """
        self.eulers = np.array(eulers, dtype=np.float32)
        self.modelTransform = pyrr.matrix44.create_identity()
        self.meshType = meshType
        self.color = np.array(color, dtype=np.float32)
    
    def update(self):
        
        self.modelTransform = pyrr.matrix44.create_identity()
        self.modelTransform = pyrr.matrix44.multiply(
            m1 = self.modelTransform,
            m2 = pyrr.matrix44.create_from_eulers(
                eulers = np.radians(self.eulers),
                dtype = np.float32
            )
        )
        self.modelTransform = pyrr.matrix44.multiply(
            m1 = self.modelTransform,
            m2 = pyrr.matrix44.create_from_translation(
                vec = self.position,
                dtype = np.float32
            )
        )

class Camera:


    def __init__(self, position, eulers):

        self.position = position
        self.eulers = eulers

        self.localUp = np.array([0,0,1], dtype=np.float32)
        self.localRight = np.array([0,1,0], dtype=np.float32)
        self.localForwards = np.array([1,0,0], dtype=np.float32)

        #directions after rotation
        self.up = np.array([0,0,1], dtype=np.float32)
        self.right = np.array([0,1,0], dtype=np.float32)
        self.forwards = np.array([1,0,0], dtype=np.float32)

        self.viewTransform = pyrr.matrix44.create_identity(dtype=np.float32)
    
    def update(self):

        self.forwards = np.array(
            [
                np.cos(np.radians(self.eulers[1])) * np.cos(np.radians(self.eulers[2])),
                np.sin(np.radians(self.eulers[1])) * np.cos(np.radians(self.eulers[2])),
                np.sin(np.radians(self.eulers[2]))
            ],
            dtype=np.float32
        )
        self.right = np.cross(self.forwards, self.localUp)
        self.up = np.cross(self.right, self.forwards)
        

        #create camera's view transform
        self.viewTransform = pyrr.matrix44.create_look_at(
            eye = self.position,
            target = self.position + self.forwards,
            up = self.up,
            dtype = np.float32
        )

class Scene:


    def __init__(self):

        self.quads = [
            Component(
                position = [3,0,0],
                eulers = [0,0,90],
                meshType = "quad",
                color = [1,0,0,0.5]
            ),
            Component(
                position = [4,0.1,0],
                eulers = [0,0,90],
                meshType = "quad",
                color = [0,1,0,0.25]
            ),
            Component(
                position = [5,0.2,0],
                eulers = [0,0,90],
                meshType = "quad",
                color = [0,0,1,0.1]
            )
        ]

        self.camera = Camera(
            position = [0,0,0],
            eulers = [0,0,0]
        )
    
    def update(self, rate):

        for quad in self.quads:
            quad.update()
        
        self.camera.update()
    
    def move_camera(self, dPos):

        self.camera.position += dPos
    
    def spin_camera(self, dEulers):

        self.camera.eulers += dEulers

        if self.camera.eulers[1] < 0:
            self.camera.eulers[1] += 360
        elif self.camera.eulers[1] > 360:
            self.camera.eulers[1] -= 360
        
        self.camera.eulers[2] = min(89, max(-89, self.camera.eulers[2]))

################### View  #####################################################

def createShader(vertexFilepath, fragmentFilepath):

        with open(vertexFilepath,'r') as f:
            vertex_src = f.readlines()

        with open(fragmentFilepath,'r') as f:
            fragment_src = f.readlines()
        
        shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER),
                                compileShader(fragment_src, GL_FRAGMENT_SHADER))
        
        return shader

class QuadMesh:


    def __init__(self, L, W):

        # x, y, z
        self.vertices = (
            -L, -W, 0.0,
             L, -W, 0.0,
             L,  W, 0.0,

             L,  W, 0.0,
            -L,  W, 0.0,
            -L, -W, 0.0
        )
        self.vertices = np.array(self.vertices, dtype=np.float32)

        self.vertex_count = 6

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12, ctypes.c_void_p(0))

    def destroy(self):
        
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1,(self.vbo,))

class Renderer:


    def __init__(self, screenWidth, screenHeight):

        #initialise pygame
        pg.init()
        pg.mouse.set_visible(False)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK,
                                    pg.GL_CONTEXT_PROFILE_CORE)
        self.screenWidth = screenWidth
        self.screenHeight = screenHeight
        pg.display.set_mode((self.screenWidth,self.screenHeight), pg.OPENGL|pg.DOUBLEBUF)
        pg.mouse.set_pos((self.screenWidth // 2,self.screenHeight // 2))

        #initialise opengl
        glClearColor(0.0, 0.0, 0.0, 1)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.shader = createShader("shaders/vertex.txt", "shaders/fragment.txt")
        glUseProgram(self.shader)

        self.load_assets()

        self.set_onetime_shader_data()

        self.get_shader_locations()
    
    def set_onetime_shader_data(self):
        """
            Some data is only set once for the program, so its uniform location doesn't
            need to be stored.
        """

        projection_transform = pyrr.matrix44.create_perspective_projection(
            fovy = 45, aspect = 640 / 480, near = 0.1, far = 10, dtype = np.float32
        )
        glUniformMatrix4fv(glGetUniformLocation(self.shader, "projection"), 1, GL_FALSE, projection_transform)

    def get_shader_locations(self):
        """
            Some data is set each frame, there can be a performance benefit in querying
            the uniform locations and saving them for reuse.
        """

        self.modelMatrixLocation = glGetUniformLocation(self.shader,"model")
        self.viewMatrixLocation = glGetUniformLocation(self.shader, "view")
        self.objectColorLocation = glGetUniformLocation(self.shader, "objectColor")

    def load_assets(self):
        """
            Load/Create assets (eg. meshes and materials) that the renderer will use.
        """

        self.meshes = {
            "quad": QuadMesh(0.5,0.5),
        }
    
    def render(self, scene):

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.shader)

        glUniformMatrix4fv(self.viewMatrixLocation, 1, GL_FALSE, scene.camera.viewTransform)

        for quad in scene.quads:
            glUniformMatrix4fv(self.modelMatrixLocation,1,GL_FALSE,quad.modelTransform)
            mesh = self.meshes[quad.meshType]
            glUniform4fv(self.objectColorLocation, 1, quad.color)
            glBindVertexArray(mesh.vao)
            glDrawArrays(GL_TRIANGLES, 0, mesh.vertex_count)

        pg.display.flip()
    
    def destroy(self):
        for (name,mesh) in self.meshes.items():
            mesh.destroy()
        glDeleteProgram(self.shader)
        pg.quit()

################### Control ###################################################

class App:


    def __init__(self):

        self.screenWidth = 640
        self.screenHeight = 480

        self.renderer = Renderer(self.screenWidth, self.screenHeight)
        self.scene = Scene()

        self.make_clock()

        self.mainLoop()
    
    def make_clock(self):

        self.lastTime = pg.time.get_ticks()
        self.currentTime = 0
        self.numFrames = 0
        self.frameTime = 0

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

        keys = pg.key.get_pressed()
        combo = 0
        directionModifier = 0
        rate = self.frameTime / 16
        """
        w: 1 -> 0 degrees
        a: 2 -> 90 degrees
        w & a: 3 -> 45 degrees
        s: 4 -> 180 degrees
        w & s: 5 -> x
        a & s: 6 -> 135 degrees
        w & a & s: 7 -> 90 degrees
        d: 8 -> 270 degrees
        w & d: 9 -> 315 degrees
        a & d: 10 -> x
        w & a & d: 11 -> 0 degrees
        s & d: 12 -> 225 degrees
        w & s & d: 13 -> 270 degrees
        a & s & d: 14 -> 180 degrees
        w & a & s & d: 15 -> x
        """

        if keys[pg.K_w]:
            combo += 1
        if keys[pg.K_a]:
            combo += 2
        if keys[pg.K_s]:
            combo += 4
        if keys[pg.K_d]:
            combo += 8
        
        if combo > 0:
            if combo == 3:
                directionModifier = 45
            elif combo == 2 or combo == 7:
                directionModifier = 90
            elif combo == 6:
                directionModifier = 135
            elif combo == 4 or combo == 14:
                directionModifier = 180
            elif combo == 12:
                directionModifier = 225
            elif combo == 8 or combo == 13:
                directionModifier = 270
            elif combo == 9:
                directionModifier = 315
            
            dPos = rate * 0.1 * np.array(
                [
                    np.cos(np.deg2rad(self.scene.camera.eulers[1] + directionModifier)),
                    np.sin(np.deg2rad(self.scene.camera.eulers[1] + directionModifier)),
                    0
                ],
                dtype = np.float32
            )

            self.scene.move_camera(dPos)

    def handleMouse(self):

        (x,y) = pg.mouse.get_pos()
        rate = self.frameTime / 20.0
        theta_increment = rate * ((self.screenWidth / 2.0) - x)
        phi_increment = rate * ((self.screenHeight / 2.0) - y)
        dTheta = np.array([0, theta_increment, phi_increment], dtype=np.float32)
        self.scene.spin_camera(dTheta)
        pg.mouse.set_pos((self.screenWidth // 2,self.screenHeight // 2))

    def calculateFramerate(self):

        self.currentTime = pg.time.get_ticks()
        delta = self.currentTime - self.lastTime
        if (delta >= 1000):
            framerate = max(1,int(1000.0 * self.numFrames/delta))
            pg.display.set_caption(f"Running at {framerate} fps.")
            self.lastTime = self.currentTime
            self.numFrames = -1
            self.frameTime = float(1000.0 / max(1,framerate))
        self.numFrames += 1
    
    def quit(self):
        self.renderer.destroy()

myApp = App()