import pygame as pg
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram,compileShader
import numpy as np
import pyrr

class Component:


    def __init__(self, position, eulers, scale):

        self.position = np.array(position, dtype=np.float32)
        """
            pitch: rotation around x axis
            roll:rotation around z axis
            yaw: rotation around y axis
        """
        self.eulers = np.array(eulers, dtype=np.float32)
        self.scale = np.array(scale, dtype=np.float32)
        self.modelTransform = pyrr.matrix44.create_identity()
    
    def update(self, rate):

        self.eulers[2] += 0.25 * rate
        if self.eulers[2] > 360:
            self.eulers[2] -= 360
        
        self.modelTransform = pyrr.matrix44.create_identity()
        self.modelTransform = pyrr.matrix44.multiply(
            m1 = self.modelTransform,
            m2 =  pyrr.matrix44.create_from_scale(
                scale = self.scale,
                dtype = np.float32
            ) 
        )
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

class Player:


    def __init__(self, position, eulers, scale):
        self.position = np.array(position,dtype=np.float32)
        self.eulers = np.array(eulers,dtype=np.float32)
        self.scale = np.array(scale,dtype=np.float32)
        self.camera = None
    
    def update(self, rate, target):

        if target is not None:
            self.move_towards(target.position, 0.1 * rate)
        
        self.modelTransform = pyrr.matrix44.create_identity()
        self.modelTransform = pyrr.matrix44.multiply(
            m1 = self.modelTransform,
            m2 =  pyrr.matrix44.create_from_scale(
                scale = self.scale,
                dtype = np.float32
            ) 
        )
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

    def move(self, direction, amount):
        self.position[0] += amount * np.cos(np.radians(direction),dtype=np.float32)
        self.position[1] -= amount * np.sin(np.radians(direction),dtype=np.float32)
        self.camera.position[0] += amount * np.cos(np.radians(direction),dtype=np.float32)
        self.camera.position[1] -= amount * np.sin(np.radians(direction),dtype=np.float32)
        self.eulers[1] = direction

    def move_towards(self, targetPosition, amount):
        directionVector = targetPosition - self.position
        angle = np.arctan2(-directionVector[1],directionVector[0])
        self.move(np.degrees(angle), amount)

class Camera:

    def __init__(self, position):

        self.position = np.array(position,dtype=np.float32)
        self.forward = np.array([0, 0, 0],dtype=np.float32)
        self.right = np.array([0, 0, 0],dtype=np.float32)
        self.up = np.array([0, 0, 0],dtype=np.float32)
        self.localUp = np.array([0, 0, 1], dtype=np.float32)
        self.targetObject = None
        self.viewTransform = pyrr.matrix44.create_identity(dtype=np.float32)

    def update(self):
        self.forward = pyrr.vector.normalize(self.targetObject.position - self.position)
        self.right = pyrr.vector.normalize(pyrr.vector3.cross(self.forward, self.localUp))
        self.up = pyrr.vector.normalize(pyrr.vector3.cross(self.right, self.forward))

        self.viewTransform = pyrr.matrix44.create_look_at(self.position, self.targetObject.position, self.up,dtype=np.float32)

class Scene:


    def __init__(self):

        self.player = Player(
            position = [0,1,0],
            eulers = [0,0,0],
            scale = [1,1,1]
        )
        self.camera = Camera(position = [-3,1,3])
        self.player.camera = self.camera
        self.camera.targetObject = self.player

        self.click_dots = []

        #make row of triangles
        self.triangles = []
        for x in range(1,16,3):
            self.triangles.append(
                Component(
                    position = [x,1,0.5],
                    eulers = [0,0,0],
                    scale = [0.5, 0.5, 0.5],
                )
            )
    
    def update(self, rate):

        for triangle in self.triangles:
            triangle.update(rate)
        for dot in self.click_dots:
            dot.update(rate)
        targetDot = None
        if len(self.click_dots) > 0:
            targetDot = self.click_dots[0]
        self.player.update(rate, targetDot)
        self.camera.update()

        #check if dot can be deleted
        if targetDot is not None:
            if pyrr.vector.length(targetDot.position - self.player.position) < 0.01:
                self.click_dots.pop(self.click_dots.index(targetDot))
    
    def lay_down_dot(self, position):
        self.click_dots.append(
            Component(
                position = position,
                eulers = [0,0,0],
                scale = [0.1, 0.1, 0.1],
            )
        )
    
    def move_camera(self, dPos):

        self.camera.position += dPos[0] * self.camera.forward \
            + dPos[1] * self.camera.right \
            + dPos[2] * self.camera.up

class App:


    def __init__(self):
        #initialise pygame
        pg.init()
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK,
                                    pg.GL_CONTEXT_PROFILE_CORE)
        self.screenWidth = 640
        self.screenHeight = 480
        pg.display.set_mode((self.screenWidth,self.screenHeight), pg.OPENGL|pg.DOUBLEBUF)
        pg.mouse.set_pos((self.screenWidth//2,self.screenHeight//2))
        self.clock = pg.time.Clock()
        #initialise opengl
        glClearColor(0.1, 0.2, 0.2, 1)
        self.shader = self.createShader("shaders/vertex.txt", "shaders/fragment.txt")
        glUseProgram(self.shader)
        glEnable(GL_DEPTH_TEST)

        self.scene = Scene()
        self.triangle_mesh = TriangleMesh()

        projection_transform = pyrr.matrix44.create_perspective_projection(
            fovy = 45, aspect = 640 / 480, near = 0.1, far = 50, dtype = np.float32
        )
        glUniformMatrix4fv(glGetUniformLocation(self.shader, "projection"), 1, GL_FALSE, projection_transform)

        self.modelMatrixLocation = glGetUniformLocation(self.shader,"model")
        self.viewMatrixLocation = glGetUniformLocation(self.shader, "view")

        self.lastTime = pg.time.get_ticks()
        self.currentTime = 0
        self.numFrames = 0
        self.frameTime = 0
        self.lightCount = 0

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
                if (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    running = False
                if (event.type == pg.QUIT):
                    running = False
                if (event.type == pg.MOUSEBUTTONDOWN):
                    self.handleMouse()
            
            self.handleKeys()
            
            #update scene
            rate = self.frameTime / 16
            self.scene.update(rate)
            
            #refresh screen
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glUseProgram(self.shader)

            glUniformMatrix4fv(self.viewMatrixLocation, 1, GL_FALSE, self.scene.camera.viewTransform)

            glUniformMatrix4fv(self.modelMatrixLocation,1,GL_FALSE,self.scene.player.modelTransform)
            glBindVertexArray(self.triangle_mesh.vao)
            glDrawArrays(GL_TRIANGLES, 0, self.triangle_mesh.vertex_count)

            for triangle in self.scene.triangles:
                glUniformMatrix4fv(self.modelMatrixLocation,1,GL_FALSE,triangle.modelTransform)
                glBindVertexArray(self.triangle_mesh.vao)
                glDrawArrays(GL_TRIANGLES, 0, self.triangle_mesh.vertex_count)
            
            for dot in self.scene.click_dots:
                glUniformMatrix4fv(self.modelMatrixLocation,1,GL_FALSE,dot.modelTransform)
                glBindVertexArray(self.triangle_mesh.vao)
                glDrawArrays(GL_TRIANGLES, 0, self.triangle_mesh.vertex_count)

            pg.display.flip()

            #timing
            self.calculateFramerate()
        self.quit()
    
    def handleKeys(self):

        keys = pg.key.get_pressed()
        rate = self.frameTime / 16
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
            
        dPos = rate * 0.1 * np.array(
            camera_movement,
            dtype = np.float32
        )

        self.scene.move_camera(dPos)
    
    def handleMouse(self):

        #fetch camera's vectors
        forward = self.scene.camera.forward
        up = self.scene.camera.up
        right = self.scene.camera.right

        #get mouse's displacement from screen center
        (x,y) = pg.mouse.get_pos()
        rightAmount = (x - self.screenWidth//2)/self.screenWidth
        upAmount = (self.screenHeight//2 - y)/self.screenWidth

        #get resultant direction (from camera eye, through point on screen)
        resultant = pyrr.vector.normalize(forward + rightAmount * right + upAmount * up)

        #trace from camera's position until we hit the ground
        if (resultant[2] < 0):
            x = self.scene.camera.position[0]
            y = self.scene.camera.position[1]
            z = self.scene.camera.position[2]
            while (z > 0):
                x += resultant[0]
                y += resultant[1]
                z += resultant[2]
            self.scene.lay_down_dot(
                position = [x,y,0]
            )

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