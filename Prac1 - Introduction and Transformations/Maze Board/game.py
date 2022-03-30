import pygame as pg
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram,compileShader
import numpy as np
import pyrr
import math

class Board:


    def __init__(self, position, eulers):

        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)

        self.layout = [
            [1,1,1,1,1,1,1,1,1,1],
            [1,0,1,0,1,0,1,0,0,1],
            [1,0,1,0,0,0,1,0,1,1],
            [1,0,0,0,1,1,1,2,0,1],
            [1,0,1,0,0,0,0,0,1,1],
            [1,0,1,0,1,1,1,0,1,1],
            [1,0,1,0,1,0,0,0,1,1],
            [1,0,1,0,1,1,1,0,1,1],
            [1,0,0,0,0,0,0,0,0,1],
            [1,1,1,1,1,1,1,1,1,1]
        ]

        self.maxTilt = 30
    
    def tilt(self, amount):

        (dx, dy) = amount

        self.eulers[0] = min(self.maxTilt,max(-self.maxTilt, self.eulers[0] + dx))
        self.eulers[2] = min(self.maxTilt,max(-self.maxTilt, self.eulers[2] + dy))

class Ball:


    def __init__(self, position, color):

        self.position = position
        self.velocity = [0,0]
        self.color = np.array(color, dtype=np.float32)
    
    def update(self, environmentLayout):
        testRow = math.floor(self.position[0] + 0.5 + 0.375*np.sign(self.velocity[0]) + self.velocity[0])
        testColumn = math.floor(self.position[1] + 0.5 + 0.375*np.sign(self.velocity[1]) + self.velocity[1])
        #check row
        if testRow > 9 \
            or testRow < 0 \
            or environmentLayout[testRow][math.floor(self.position[1] + 0.5)] == 1:
            self.velocity[0] *= -0.25
        #check column
        if testColumn > 9 \
            or testColumn < 0 \
            or environmentLayout[math.floor(self.position[0] + 0.5)][testColumn] == 1:
            self.velocity[1] *= -0.25
        self.position[0] = min(9, max(0, self.position[0] + self.velocity[0]))
        self.position[1] = min(9, max(0, self.position[1] + self.velocity[1]))

class App:


    def __init__(self):
        #initialise pygame
        pg.init()
        pg.display.set_mode((640,480), pg.OPENGL|pg.DOUBLEBUF)
        self.clock = pg.time.Clock()
        #initialise opengl
        glClearColor(0, 0, 0, 1)
        self.shader = self.createShader("shaders/vertex.txt", "shaders/fragment.txt")
        self.coloredShader = self.createShader("shaders/vertexColored.txt", 
            "shaders/fragmentColored.txt")
        glUseProgram(self.shader)
        
        glEnable(GL_DEPTH_TEST)

        self.makeObjects()

        self.configureShaders()

        self.mainLoop()

    def makeObjects(self):

        self.board_texture = Material("gfx/dark_marble.jpg")
        self.piece_texture = Material("gfx/red.jpg")
        self.board_mesh = Mesh("models/board.obj")
        self.piece_mesh = Mesh("models/piece.obj")
        self.ball_mesh = Mesh("models/ball.obj")

        self.board = Board(
            position = [0,0,0],
            eulers = [0,0,0]
        )
        glUseProgram(self.coloredShader)
        self.ball = Ball(
            position = [1,1],
            color = [1,1,1]
        )
    
    def configureShaders(self):

        viewProjection_transform = pyrr.matrix44.multiply(
            m1 = pyrr.matrix44.create_look_at(
                eye = np.array([0, -10, 30]),
                target = np.array([1, 1, 0]),
                up = pyrr.vector.normalize(np.array([0, 1, 2/3])),
                dtype = np.float32
            ),
            m2 = pyrr.matrix44.create_perspective_projection(
                fovy = 45, aspect = 640/480, 
                near = 0.1, far = 80, dtype=np.float32
            )
        )

        sunColor = np.array([1,1,1], dtype=np.float32)
        sunDirection = pyrr.vector.normalize(np.array([1,0,-1], dtype=np.float32))
        glUseProgram(self.shader)
        glUniform1i(glGetUniformLocation(self.shader, "imageTexture"), 0)
        glUniformMatrix4fv(
            glGetUniformLocation(self.shader,"viewProjection"),
            1, GL_FALSE, viewProjection_transform
        )
        glUniform3fv(glGetUniformLocation(self.shader,"sunColor"), 1, sunColor)
        glUniform3fv(glGetUniformLocation(self.shader,"sunDirection"), 1, sunDirection)
        glUseProgram(self.coloredShader)
        glUniformMatrix4fv(
            glGetUniformLocation(self.coloredShader,"viewProjection"),
            1, GL_FALSE, viewProjection_transform
        )
        glUniform3fv(glGetUniformLocation(self.coloredShader,"sunColor"), 1, sunColor)
        glUniform3fv(glGetUniformLocation(self.coloredShader,"sunDirection"), 1, sunDirection)
        self.modelMatrixLocation = glGetUniformLocation(self.shader,"model")
        self.modelMatrixLocationColored = glGetUniformLocation(self.coloredShader,"model")
        self.colorLocation = glGetUniformLocation(self.coloredShader,"objectColor")

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
            
            #update board
            tiltAmount = [0,0]
            keys = pg.key.get_pressed()
            if keys[pg.K_LEFT]:
                tiltAmount[1] = 0.4
            if keys[pg.K_RIGHT]:
                tiltAmount[1] = -0.4
            if keys[pg.K_UP]:
                tiltAmount[0] = 0.4
            if keys[pg.K_DOWN]:
                tiltAmount[0] = -0.4
            self.board.tilt(tiltAmount)

            #update ball
            self.ball.velocity[1] += -0.01*np.sin(np.radians(self.board.eulers[2]))
            self.ball.velocity[0] += 0.01*np.sin(np.radians(self.board.eulers[0]))
            self.ball.update(self.board.layout)
            
            #refresh screen
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
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
                    eulers=np.radians(self.board.eulers), dtype=np.float32
                )
            )
            model_transform = pyrr.matrix44.multiply(
                m1=model_transform, 
                m2=pyrr.matrix44.create_from_translation(
                    vec=np.array(self.board.position),dtype=np.float32
                )
            )
            glUniformMatrix4fv(self.modelMatrixLocation,1,GL_FALSE,model_transform)
            self.board_texture.use()
            glBindVertexArray(self.board_mesh.vao)
            glDrawArrays(GL_TRIANGLES, 0, self.board_mesh.vertex_count)

            self.piece_texture.use()
            glBindVertexArray(self.piece_mesh.vao)
            for row in range(10):
                for column in range(10):
                    if self.board.layout[row][column] == 1:
                        model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
                        model_transform = pyrr.matrix44.multiply(
                            m1=model_transform, 
                            m2=pyrr.matrix44.create_from_translation(
                                vec=np.array([2*column - 9, 2*row - 9, 2]),dtype=np.float32
                            )
                        )
                        model_transform = pyrr.matrix44.multiply(
                            m1=model_transform, 
                            m2=pyrr.matrix44.create_from_eulers(
                                eulers=np.radians(self.board.eulers), dtype=np.float32
                            )
                        )
                        glUniformMatrix4fv(self.modelMatrixLocation,1,GL_FALSE,model_transform)
                        glDrawArrays(GL_TRIANGLES, 0, self.piece_mesh.vertex_count)
            
            glUseProgram(self.coloredShader)
            glBindVertexArray(self.ball_mesh.vao)
            model_transform = pyrr.matrix44.create_identity(dtype=np.float32)
            
            model_transform = pyrr.matrix44.multiply(
                m1=model_transform, 
                m2=pyrr.matrix44.create_from_translation(
                    vec=np.array([2*self.ball.position[1] - 9, 2*self.ball.position[0] - 9, 1.75]),dtype=np.float32
                )
            )
            
            model_transform = pyrr.matrix44.multiply(
                m1=model_transform, 
                m2=pyrr.matrix44.create_from_eulers(
                    eulers=np.radians(self.board.eulers), dtype=np.float32
                )
            )
            glUniformMatrix4fv(self.modelMatrixLocationColored,1,GL_FALSE,model_transform)
            glUniform3fv(self.colorLocation, 1, self.ball.color)
            glDrawArrays(GL_TRIANGLES, 0, self.ball_mesh.vertex_count)

            pg.display.flip()

            #timing
            self.clock.tick(60)
        self.quit()

    def quit(self):
        self.board_mesh.destroy()
        self.piece_mesh.destroy()
        self.ball_mesh.destroy()
        self.board_texture.destroy()
        self.piece_texture.destroy()
        glDeleteProgram(self.shader)
        glDeleteProgram(self.coloredShader)
        pg.quit()

class Mesh:


    def __init__(self, filename):
        # x, y, z, s, t, nx, ny, nz
        self.vertices = self.loadMesh(filename)
        self.vertex_count = len(self.vertices)//8
        self.vertices = np.array(self.vertices, dtype=np.float32)

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        #position
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(0))
        #texture
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(12))
        #normal
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(20))
    
    def loadMesh(self, filename):

        #raw, unassembled data
        v = []
        vt = []
        vn = []
        
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
                elif flag=="vt":
                    #texture coordinate
                    line = line.replace("vt ","")
                    line = line.split(" ")
                    l = [float(x) for x in line]
                    vt.append(l)
                elif flag=="vn":
                    #normal
                    line = line.replace("vn ","")
                    line = line.split(" ")
                    l = [float(x) for x in line]
                    vn.append(l)
                elif flag=="f":
                    #face, three or more vertices in v/vt/vn form
                    line = line.replace("f ","")
                    line = line.replace("\n","")
                    #get the individual vertices for each line
                    line = line.split(" ")
                    faceVertices = []
                    faceTextures = []
                    faceNormals = []
                    for vertex in line:
                        #break out into [v,vt,vn],
                        #correct for 0 based indexing.
                        l = vertex.split("/")
                        position = int(l[0]) - 1
                        faceVertices.append(v[position])
                        texture = int(l[1]) - 1
                        faceTextures.append(vt[texture])
                        normal = int(l[2]) - 1
                        faceNormals.append(vn[normal])
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
                        for x in faceTextures[i]:
                            vertices.append(x)
                        for x in faceNormals[i]:
                            vertices.append(x)
                line = f.readline()
        return vertices
    
    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1,(self.vbo,))

class Material:

    
    def __init__(self, filepath):
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        image = pg.image.load(filepath).convert()
        image_width,image_height = image.get_rect().size
        img_data = pg.image.tostring(image,'RGBA')
        glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,image_width,image_height,0,GL_RGBA,GL_UNSIGNED_BYTE,img_data)
        glGenerateMipmap(GL_TEXTURE_2D)

    def use(self):
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D,self.texture)

    def destroy(self):
        glDeleteTextures(1, (self.texture,))

myApp = App()