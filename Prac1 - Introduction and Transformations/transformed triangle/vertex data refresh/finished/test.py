import numpy as np
import pyrr

originalPositions = (
    -0.5, -0.5, 0.0, 1.0,
    0.5, -0.5, 0.0, 1.0,
    0.0,  0.5, 0.0, 1.0
)

originalPositions = np.array(originalPositions, dtype=np.float32)
originalPositions = np.reshape(
    a = originalPositions, 
    newshape = (3,4)
)

transform = pyrr.matrix44.create_from_scale(scale = np.array([2,3,4]))

transformed_points = pyrr.matrix44.multiply(
    m1 = originalPositions,
    m2 = transform
)

vertices = np.array([],dtype=np.float32)

for i in range(3):

    vertices = np.append(vertices, transformed_points[i][0:3])

print(originalPositions)
print(transformed_points)
print(vertices)