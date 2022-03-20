import pygame as pg
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram,compileShader
import numpy as np
import pyrr

class ConnectedComponent:


    def __init__(self, position, eulers):

        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)
        self.parent = None
        self.child = None
        self.modelTransform = pyrr.matrix44.create_identity()
    
    def updateTransform(self):

        self.modelTransform = pyrr.matrix44.create_identity()

        #first apply local transformations, gets object into position on parent etc
        
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

        #now apply the parent's transformation
        if self.parent is not None:
            self.modelTransform = pyrr.matrix44.multiply(
                m1 = self.modelTransform,
                m2 = self.parent.modelTransform
            )
        
        #then trigger the child object to update its transform
        if self.child is not None:
            self.child.updateTransform()

class Crane:


    def __init__(self, position, eulers):

        self.position = np.array(position, dtype = np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)
        
        self.base = ConnectedComponent(
            position = [position[0], position[1], position[2]], 
            eulers = [eulers[0], eulers[1], eulers[2]]
        )
        self.stem = ConnectedComponent(
            position = [0, 0, 2.0], 
            eulers = [eulers[0], eulers[1], eulers[2]]
        )
        self.console = ConnectedComponent(
            position = [0, 0, 12],
            eulers = [eulers[0], eulers[1], eulers[2]]
        )
        self.arm = ConnectedComponent(
            position = [12, 0, 0], 
            eulers = [eulers[0], eulers[1], eulers[2] + 90]
        )
        self.ball = ConnectedComponent(
            position = [-8, 0, -8], 
            eulers = [eulers[0], eulers[1], eulers[2]]
        )

        self.base.child = self.stem

        self.stem.parent = self.base
        self.stem.child = self.console

        self.console.parent = self.stem
        self.console.child = self.arm

        self.arm.parent = self.console
        self.arm.child = self.ball

        self.ball.parent = self.arm
 
    def update(self):

        self.base.eulers = self.eulers

        self.base.updateTransform()
        
class App:


    def __init__(self, screenWidth, screenHeight):

        self.screenWidth = screenWidth
        self.screenHeight = screenHeight

        self.renderer = GraphicsEngine()

        self.crane = Crane(
            position = [0,0,0],
            eulers = [0,0,0]
        )

        self.lastTime = pg.time.get_ticks()
        self.currentTime = 0
        self.numFrames = 0
        self.frameTime = 0
        self.lightCount = 0

        self.mainLoop()

    def mainLoop(self):
        running = True
        while (running):
            #check events
            for event in pg.event.get():
                if (event.type == pg.QUIT):
                    running = False
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        running = False
            
            self.handleKeys()

            self.crane.update()
            
            self.renderer.render(self.crane)

            #timing
            self.calculateFramerate()
        self.quit()

    def handleKeys(self):

        keys = pg.key.get_pressed()

        rate = self.frameTime / 16

        if keys[pg.K_LEFT]:
            self.crane.eulers[1] -= rate
            if self.crane.eulers[1] < 0:
                self.crane.eulers[1] += 360
        elif keys[pg.K_RIGHT]:
            self.crane.eulers[1] += rate
            if self.crane.eulers[1] > 360:
                self.crane.eulers[1] -= 360

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

class GraphicsEngine:


    def __init__(self):

        self.palette = {
            "Navy": np.array([0,13/255,107/255], dtype = np.float32),
            "Purple": np.array([156/255,25/255,224/255], dtype = np.float32),
            "Pink": np.array([255/255,93/255,162/255], dtype = np.float32),
            "Orange": np.array([255/255,162/255,93/255], dtype = np.float32),
            "Teal": np.array([153/255,221/255,204/255], dtype = np.float32),
            "Red": np.array([255/255,93/255,93/255], dtype = np.float32),
            "Green": np.array([93/255,255/255,93/255], dtype = np.float32),
        }

        #initialise pygame
        pg.init()
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
        pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK,
                                    pg.GL_CONTEXT_PROFILE_CORE)
        pg.display.set_mode((640,480), pg.OPENGL|pg.DOUBLEBUF)

        #initialise opengl
        glClearColor(self.palette["Navy"][0], self.palette["Navy"][1], self.palette["Navy"][2], 1)
        glEnable(GL_DEPTH_TEST)

        #create renderpasses and resources
        shader = self.createShader("shaders/vertex.txt", "shaders/fragment.txt")
        self.renderPass = RenderPass(shader)
        self.groundMesh = Mesh("models/ground.obj")
        self.cubeMesh = Mesh("models/cube.obj")
        self.stemMesh = Mesh("models/stem.obj")
        self.ballMesh = Mesh("models/ball.obj")
    
    def createShader(self, vertexFilepath, fragmentFilepath):

        with open(vertexFilepath,'r') as f:
            vertex_src = f.readlines()

        with open(fragmentFilepath,'r') as f:
            fragment_src = f.readlines()
        
        shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER),
                                compileShader(fragment_src, GL_FRAGMENT_SHADER))
        
        return shader

    def render(self, scene):

        #refresh screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.renderPass.render(scene, self)

        pg.display.flip()

    def destroy(self):
        self.groundMesh.destroy()
        self.cubeMesh.destroy()
        self.stemMesh.destroy()
        self.ballMesh.destroy()
        self.renderPass.destroy()
        pg.quit()

class RenderPass:


    def __init__(self, shader):

        #initialise opengl
        self.shader = shader
        glUseProgram(self.shader)

        projection_transform = pyrr.matrix44.create_perspective_projection(
            fovy = 45, aspect = 800/600, 
            near = 0.1, far = 100, dtype=np.float32
        )
        glUniformMatrix4fv(
            glGetUniformLocation(self.shader,"projection"),
            1, GL_FALSE, projection_transform
        )
        self.modelMatrixLocation = glGetUniformLocation(self.shader, "model")
        self.viewMatrixLocation = glGetUniformLocation(self.shader, "view")
        self.colorLoc = glGetUniformLocation(self.shader, "object_color")

    def render(self, scene, engine):

        glUseProgram(self.shader)

        view_transform = pyrr.matrix44.create_look_at(
            eye = np.array([32,-32,32], dtype = np.float32),
            target = np.array([8,0,8], dtype = np.float32),
            up = np.array([0,0,1], dtype = np.float32), dtype = np.float32
        )
        glUniformMatrix4fv(self.viewMatrixLocation, 1, GL_FALSE, view_transform)

        #ground
        glUniform3fv(self.colorLoc, 1, engine.palette["Teal"])
        modelTransform = pyrr.matrix44.create_identity(dtype=np.float32)
        glUniformMatrix4fv(self.modelMatrixLocation, 1, GL_FALSE, modelTransform)
        glBindVertexArray(engine.groundMesh.vao)
        glDrawArrays(GL_TRIANGLES, 0, engine.groundMesh.vertex_count)

        #base
        glUniform3fv(self.colorLoc, 1, engine.palette["Orange"])
        glUniformMatrix4fv(self.modelMatrixLocation, 1, GL_FALSE, scene.base.modelTransform)
        glBindVertexArray(engine.cubeMesh.vao)
        glDrawArrays(GL_TRIANGLES, 0, engine.cubeMesh.vertex_count)

        #stem
        glUniform3fv(self.colorLoc, 1, engine.palette["Red"])
        glUniformMatrix4fv(self.modelMatrixLocation, 1, GL_FALSE, scene.stem.modelTransform)
        glBindVertexArray(engine.stemMesh.vao)
        glDrawArrays(GL_TRIANGLES, 0, engine.stemMesh.vertex_count)

        #console
        glUniform3fv(self.colorLoc, 1, engine.palette["Pink"])
        glUniformMatrix4fv(self.modelMatrixLocation, 1, GL_FALSE, scene.console.modelTransform)
        glBindVertexArray(engine.cubeMesh.vao)
        glDrawArrays(GL_TRIANGLES, 0, engine.cubeMesh.vertex_count)

        #arm
        glUniform3fv(self.colorLoc, 1, engine.palette["Orange"])
        glUniformMatrix4fv(self.modelMatrixLocation, 1, GL_FALSE, scene.arm.modelTransform)
        glBindVertexArray(engine.stemMesh.vao)
        glDrawArrays(GL_TRIANGLES, 0, engine.stemMesh.vertex_count)

        #ball
        glUniform3fv(self.colorLoc, 1, engine.palette["Green"])
        glUniformMatrix4fv(self.modelMatrixLocation, 1, GL_FALSE, scene.ball.modelTransform)
        glBindVertexArray(engine.ballMesh.vao)
        glDrawArrays(GL_TRIANGLES, 0, engine.ballMesh.vertex_count)

    def destroy(self):

        glDeleteProgram(self.shader)

class Mesh:


    def __init__(self, filename):
        # x, y, z
        self.vertices = self.loadMesh(filename)
        self.vertex_count = len(self.vertices)//3
        self.vertices = np.array(self.vertices, dtype=np.float32)

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        #position
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12, ctypes.c_void_p(0))
    
    def loadMesh(self, filename):

        #raw, unassembled data
        v = []
        
        #final, assembled and packed result
        vertices = []

        #open the obj file and read the data
        with open(filename,'r') as f:
            line = f.readline()
            while line:
                firstSpace = line.find(" ")
                flag = line[0:firstSpace]
                if flag=="v":
                    #vertex
                    line = line.replace("v ","")
                    line = line.split(" ")
                    l = [float(x) for x in line]
                    v.append(l)
                elif flag=="f":
                    #face, three or more vertices in v/vt/vn form
                    line = line.replace("f ","")
                    line = line.replace("\n","")
                    #get the individual vertices for each line
                    line = line.split(" ")
                    faceVertices = []
                    for vertex in line:
                        #break out into [v,vt,vn],
                        #correct for 0 based indexing.
                        l = vertex.split("/")
                        position = int(l[0]) - 1
                        faceVertices.append(v[position])
                    # obj file uses triangle fan format for each face individually.
                    # unpack each face
                    triangles_in_face = len(line) - 2

                    vertex_order = []
                    """
                        eg. 0,1,2,3 unpacks to vertices: [0,1,2,0,2,3]
                    """
                    for i in range(triangles_in_face):
                        vertex_order.append(0)
                        vertex_order.append(i+1)
                        vertex_order.append(i+2)
                    for i in vertex_order:
                        for x in faceVertices[i]:
                            vertices.append(x)
                line = f.readline()
        return vertices
    
    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1,(self.vbo,))
    
myApp = App(800,600)