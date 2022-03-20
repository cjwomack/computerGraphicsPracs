import pygame as pg
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram,compileShader
import numpy as np
import pyrr

class Component:


    def __init__(self, position, eulers):

        self.position = np.array(position, dtype=np.float32)
        self.eulers = np.array(eulers, dtype=np.float32)

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
            position = [0.5,0,0],
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
                    eulers=np.radians(self.triangle.eulers), dtype=np.float32
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

    def destroy(self):
        
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1,(self.vbo,))

myApp = App()