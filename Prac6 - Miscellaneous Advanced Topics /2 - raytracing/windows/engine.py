from config import *
import sphere
import scene

class Engine:
    """
        Responsible for drawing scenes
    """

    def __init__(self, width: int, height: int):
        """
            Initialize a flat raytracing context
            
                Parameters:
                    width (int): width of screen
                    height (int): height of screen
        """
        self.screenWidth = width
        self.screenHeight = height

        #general OpenGL configuration
        self.createQuad()
        self.createColorBuffer()
        self.createResourceMemory()
        
        self.shader = self.createShader("shaders/frameBufferVertex.txt",
                                        "shaders/frameBufferFragment.txt")
        
        self.rayTracerShader = self.createComputeShader("shaders/rayTracer.txt")

        self.queryUniformLocations()
    
    def createQuad(self) -> None:
        """
            Create a screen-sized quad, later this can be used to draw
            the result of the compute shader.
        """

        # x, y, z, s, t
        self.vertices = np.array(
            ( 1.0,  1.0, 0.0, 1.0, 1.0, #top-right
             -1.0,  1.0, 0.0, 0.0, 1.0, #top-left
             -1.0, -1.0, 0.0, 0.0, 0.0, #bottom-left
             -1.0, -1.0, 0.0, 0.0, 0.0, #bottom-left
              1.0, -1.0, 0.0, 1.0, 0.0, #bottom-right
              1.0,  1.0, 0.0, 1.0, 1.0), #top-right
             dtype=np.float32
        )

        self.vertex_count = 6

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(12))
    
    def createColorBuffer(self) -> None:
        """
            Create the texture onto which the compute shader will draw
            the rendered image.
        """

        #Make a texture and bind it.
        self.colorBuffer = glGenTextures(1)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.colorBuffer)

        #Set sampling parameters.
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        #Allocate space.
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA32F, 
            self.screenWidth, self.screenHeight, 
            0, GL_RGBA, GL_FLOAT, None)
    
    def createResourceMemory(self) -> None:
        """
            A handy way to pass a large chunk of data is to
            encode it in a texture. 
            There are other ways, eg. Shader Storage Buffer Objects,
            but those seem to be less reliable in python.
        """

        spheres_max = 1024
        blocks_per_sphere = 2
        # Spheres will be encoded in the following layout:
        # (cx cy cz radius) (r g b _)
        # and hence require two pixels each.
        self.sphereData = np.zeros(spheres_max * 4 * blocks_per_sphere, dtype=np.float32)
        # The texture layout in memory will be:
        # row = sphere, column = block within sphere

        # Make texture and bind it.
        self.sphereDataTexture = glGenTextures(1)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.sphereDataTexture)

        # Set sampling parameters (not used, but still, why not?)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    
        # Allocate space.
        glTexImage2D(
            GL_TEXTURE_2D,0,
            GL_RGBA32F,2,1024,
            0,GL_RGBA,GL_FLOAT,bytes(self.sphereData)
        )
    
    def createShader(self, vertexFilepath: str, fragmentFilepath: str) -> int:
        """
            Read source code, compile and link shaders.
            Returns the compiled and linked program.
        """

        with open(vertexFilepath,'r') as f:
            vertex_src = f.readlines()

        with open(fragmentFilepath,'r') as f:
            fragment_src = f.readlines()
        
        shader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER),
                                compileShader(fragment_src, GL_FRAGMENT_SHADER))
        
        return shader
    
    def createComputeShader(self, filepath: str) -> int:
        """
            Read source code, compile and link shaders.
            Returns the compiled and linked program.
        """

        with open(filepath,'r') as f:
            compute_src = f.readlines()
        
        shader = compileProgram(compileShader(compute_src, GL_COMPUTE_SHADER))
        
        return shader

    def queryUniformLocations(self) -> None:
        """
            Get uniform locations from shader for reuse.
        """
        glUseProgram(self.rayTracerShader)
        self.viewPosLocation = glGetUniformLocation(
            self.rayTracerShader, 
            "viewer.position"
        )
        self.viewForwardsLocation = glGetUniformLocation(
            self.rayTracerShader, 
            "viewer.forwards"
        )
        self.viewRightLocation = glGetUniformLocation(
            self.rayTracerShader, 
            "viewer.right"
        )
        self.viewUpLocation = glGetUniformLocation(
            self.rayTracerShader, 
            "viewer.up"
        )
        self.sphereCountLocation = glGetUniformLocation(
            self.rayTracerShader, 
            "sphereCount"
        )
    
    def recordSphere(self, i: int, _sphere: sphere.Sphere) -> None:
        """
            Encode a representation of the given sphere at index i in the
            sphere texture.
        """
        baseIndex: int = 8*i

        self.sphereData[baseIndex:baseIndex + 3] = _sphere.center[:]

        self.sphereData[baseIndex + 3] = _sphere.radius

        self.sphereData[baseIndex + 4:baseIndex + 7] = _sphere.color[:]
    
    def prepareScene(self, _scene: scene.Scene) -> None:
        """
            Send scene data to the shader.
        """

        glUseProgram(self.rayTracerShader)

        #Camera Parameters
        glUniform3fv(self.viewPosLocation, 1, _scene.camera.position)
        glUniform3fv(self.viewForwardsLocation, 1, _scene.camera.forwards)
        glUniform3fv(self.viewRightLocation, 1, _scene.camera.right)
        glUniform3fv(self.viewUpLocation, 1, _scene.camera.up)

        #Sphere Count
        glUniform1f(self.sphereCountLocation, len(_scene.spheres))

        #Record the data for all the spheres in the scene
        for i,_sphere in enumerate(_scene.spheres):
            self.recordSphere(i, _sphere)
        
        #Send the recorded sphere data to the sphere texture,
        #   then bind that texture so the compute shader can read it.
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.sphereDataTexture)
        glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA32F,2,1024,0,GL_RGBA,GL_FLOAT,bytes(self.sphereData))
        glBindImageTexture(1, self.sphereDataTexture, 0, GL_FALSE, 0, GL_READ_ONLY, GL_RGBA32F)
        
    def renderScene(self, _scene: scene.Scene) -> None:
        """
            Draw all objects in the scene
        """
        
        glUseProgram(self.rayTracerShader)

        self.prepareScene(_scene)

        #Bind the color buffer so the compute shader can write to it.
        glActiveTexture(GL_TEXTURE0)
        glBindImageTexture(0, self.colorBuffer, 0, GL_FALSE, 0, GL_WRITE_ONLY, GL_RGBA32F)
        
        #Despatch the compute shader: let it do its thing!
        #Note that this is based on a subgroup size of 64, which seems to be
        #ideal for most GPUs.
        glDispatchCompute(int(self.screenWidth / 8), int(self.screenHeight / 8), 1)
  
        # barrier will pause the pipeline until the compute shader has finished.
        glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)
        glBindImageTexture(0, 0, 0, GL_FALSE, 0, GL_WRITE_ONLY, GL_RGBA32F)
        self.drawScreen()

    def drawScreen(self):
        glUseProgram(self.shader)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.colorBuffer)
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)
        pg.display.flip()
    
    def destroy(self):
        """
            Free any allocated memory
        """
        glUseProgram(self.rayTracerShader)
        glMemoryBarrier(GL_ALL_BARRIER_BITS)
        glDeleteProgram(self.rayTracerShader)
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1, (self.vbo,))
        glDeleteTextures(1, (self.colorBuffer,))
        glDeleteProgram(self.shader)