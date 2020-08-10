# --------------------
# File: Read_Dicom.py
# Purpose: This file contains classes that eases the reading, information retrieval, and drawing
#          of CT scans derived from Dicom files.
# Author: Jacob Knop
# Date: Summer 2020
# --------------------

# external dependencies
import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import freetype
import glm
import os  # used for searching a file directory in one of the code snippets below

import pydicom
from pydicom.data import get_testdata_files
from pydicom.tag import Tag

# internal dependencies
import normalize
from normalize import normalize_dcm
from normalize import normalize_pixel

import matplotlib.pyplot as plt


# deprecated code --- do not use
# class CTSlice:
#     filename = 0
#     TextureID = 0
#     Size = 0
#     translation = glm.vec3(0, 0, 0)  # used in translating the image
#     zoom = 1  # used for zooming in on the image
#     dcm_shader = 0
#
#     # variables used for texture mapping to the screen
#     vertices = [-1, -1, 1.0, 0.0, 0.0, 0.0, 0.0,
#                 1, -1, 0.0, 1.0, 0.0, 1.0, 0.0,
#                 1, 1, 0.0, 0.0, 1.0, 1.0, 1.0,
#                 -1, 1, 1.0, 1.0, 1.0, 0.0, 1.0]
#
#     indices = [0, 1, 2, 2, 3, 0]
#     vertices = np.array(vertices, dtype=np.float32)
#     indices = np.array(indices, dtype=np.uint32)
#
#     def __init__(self, filename, dcm_shader):
#         self.filename = filename
#         self.load_dcm(filename)
#
#     def load_dcm(self, filename):
#         normal = normalize.normalize_dcm(filename)
#         print(normal.nbytes)
#         texture = glGenTextures(1)
#         glBindTexture(GL_TEXTURE_2D, texture)
#         # Specifying 2D image (DICOM) to be mapped to the screen (Format: Single Channel)
#         glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, normal.shape[0], normal.shape[1], 0, GL_RED, GL_FLOAT, normal)
#
#         # Set the texture wrapping parameters
#         glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
#         glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
#         # Set texture filtering parameters
#         glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
#         glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
#
#         # saving texture ID to be used later for the Draw Function
#         self.TextureID = texture
#         # storing size of the image (likely width by height but not sure)
#         self.Size = glm.vec2(normal.shape[0], normal.shape[1])
#
#         glBindTexture(GL_TEXTURE_2D, 0)
#
#     def draw_dcm(self, VBO, EBO, shader):
#         model_loc = glGetUniformLocation(shader, "model")
#         proj_loc = glGetUniformLocation(shader, "projection")
#         # translating image if necessary
#         model = glm.mat4(1)
#         model = glm.translate(model, self.translation)  # self.translation)
#
#         # used for zooming (need to create panel for button functionality)
#         projection = glm.scale(glm.mat4(1), glm.vec3(-self.zoom, -self.zoom, 1))  # used for zooming in and out
#         glUniformMatrix4fv(model_loc, 1, GL_FALSE, glm.value_ptr(model))
#         glUniformMatrix4fv(proj_loc, 1, GL_FALSE, glm.value_ptr(projection))
#
#         # Binding Vertex Buffer Object
#         glBindBuffer(GL_ARRAY_BUFFER, VBO)
#         glBufferSubData(GL_ARRAY_BUFFER, 0, self.vertices)
#
#         # Binding Element Buffer Object
#         glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
#         glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, self.indices)
#
#         # ------------
#         # Vertices Element
#         glEnableVertexAttribArray(0)
#         glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, self.vertices.itemsize * 7, ctypes.c_void_p(0))
#
#         # Color Element
#         glEnableVertexAttribArray(1)
#         glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, self.vertices.itemsize * 7, ctypes.c_void_p(8))
#
#         # Texture Element
#         glEnableVertexAttribArray(2)
#         glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, self.vertices.itemsize * 7, ctypes.c_void_p(20))
#
#         # binding the texture
#         glBindTexture(GL_TEXTURE_2D, self.TextureID)
#         # ------------
#         # drawing to the screen
#         glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)


class CTScan:
    curr_folder = 0  # the folder the slices are derived from
    curr_slice = 0  # the slice the viewer is currently displaying
    num_slices = 0  # how many slices are loaded
    ct_slices = []  # stores all of the loaded ct slices
    dcm_shader = 0  # shader to visualize a given CT Slice
    translation = glm.vec3(0, 0, 0)  # used in translating the image
    zoom = 1  # used for zooming in on the image
    ff_flag = 0  # open file or folder flag: 0 - open folder, 1 - open file
    exposure = 0

    # these variables will store information about normalizing the CT Scan (mx + b format)
    # when drawing
    max = 0  # maximum pixel value in the current CT Slice
    slope = 0  # slope(m) in the mx+b equation
    x_int = 0  # x-intercept(b) value in the mx+b equation

    # pixel coordinates for placing the scan on the screen
    x1 = 0
    y1 = 0
    x2 = 0
    y2 = 0

    # variables used for texture mapping to the screen
    vertices = [-1, -1, 1.0, 0.0, 0.0, 0.0, 0.0,
                1, -1, 0.0, 1.0, 0.0, 1.0, 0.0,
                1, 1, 0.0, 0.0, 1.0, 1.0, 1.0,
                -1, 1, 1.0, 1.0, 1.0, 0.0, 1.0]

    indices = [0, 1, 2, 2, 3, 0]
    vertices = np.array(vertices, dtype=np.float32)
    indices = np.array(indices, dtype=np.uint32)

    mpr_view = 1
    new_texture_list = []

    def __init__(self, folder, shader, ff_flag):
        print("loading new CT_Scan")
        print(folder)
        self.ct_slices = []
        self.curr_folder = folder
        self.dcm_shader = shader
        self.ff_flag = ff_flag
        self.load()

    def load(self):
        # load folder
        if self.ff_flag == 0:
            self.load_folder()
        # load file:
        if self.ff_flag == 1:
            self.load_file()

    def load_folder(self):

        # the following lines will be used to experiment with finding a list of dicom
        # files within a folder similar to the project of Summer 2019
        # getting directory path name (this will need error checking later)

        dir_path = os.path.dirname(self.curr_folder)
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if file.endswith('.dcm'):
                    self.num_slices = self.num_slices + 1
                    slice = CT_Slice(self.curr_folder + '/' + file)
                    self.ct_slices.append(slice)

        # sorting slices (might want to see about implementing this using numpy functions
        swapped = 1
        while swapped:
            swapped = 0
            for i in range(len(self.ct_slices) - 1):
                if self.ct_slices[i].slice_location < self.ct_slices[i + 1].slice_location:
                    swapped = 1
                    swap_var = self.ct_slices[i]
                    self.ct_slices[i] = self.ct_slices[i + 1]
                    self.ct_slices[i + 1] = swap_var

    def load_file(self):
        slice = CT_Slice(self.curr_folder)
        self.ct_slices.append(slice)
        self.num_slices = 1

    # height and width of screen to align the CT Screen too
    def set_alignment(self, alignment, height, width):
        # aligning the dicom image to the center of the screen
        if alignment == "center":
            print("centering")
            size = 512  # consider changing
            a1 = (width - size) / 2
            a2 = (width + size) / 2
            b1 = (height - size) / 2
            b2 = (height + size) / 2

            self.x1 = a1
            self.y1 = b1
            self.x2 = a2
            self.y2 = b2

            x1, y1 = normalize.normalize_pixel(a1, b1, height, width)
            x2, y2 = normalize.normalize_pixel(a2, b2, height, width)
            self.vertices = [x1, y1, 1.0, 0.0, 0.0, 0.0, 0.0,
                             x2, y1, 0.0, 1.0, 0.0, 1.0, 0.0,
                             x2, y2, 0.0, 0.0, 1.0, 1.0, 1.0,
                             x1, y2, 1.0, 1.0, 1.0, 0.0, 1.0]
            self.vertices = np.array(self.vertices, dtype=np.float32)

    def draw(self, VBO, EBO):
        glUseProgram(self.dcm_shader)
        model_loc = glGetUniformLocation(self.dcm_shader, "model")
        proj_loc = glGetUniformLocation(self.dcm_shader, "projection")
        normalization_val_loc = glGetUniformLocation(self.dcm_shader, "normalization_values")
        slice_loc = glGetUniformLocation(self.dcm_shader, "sliceNumber")
        exposure_loc = glGetUniformLocation(self.dcm_shader, "sliderVal")
        # translating image if necessary
        model = glm.mat4(1)
        model = glm.translate(model, self.translation)  # self.translation)

        # used for zooming (need to create panel for button functionality)
        projection = glm.scale(glm.mat4(1), glm.vec3(-self.zoom, -self.zoom, 1))  # used for zooming in and out
        glUniformMatrix4fv(model_loc, 1, GL_FALSE, glm.value_ptr(model))
        glUniformMatrix4fv(proj_loc, 1, GL_FALSE, glm.value_ptr(projection))

        # calculating max, slope, and x-intercept for normalization of the image
        # pixArray = self.ct_slices[self.curr_slice].pixelarray
        #x1 = np.amin(self.ct_slices[self.curr_slice].pixelarray)
        #x2 = np.amax(self.ct_slices[self.curr_slice].pixelarray)

        #self.slope = (x2 - x1)
        #self.x_int = - float(self.slope) * float(x1)
        # print("max: {}, min: {}, slope: {}, intercept: {}".format(x2, x1, self.slope, self.x_int))
        #normalization_val = glm.vec3(x2, self.slope, self.x_int)
        #glUniform3fv(normalization_val_loc, 1, glm.value_ptr(normalization_val))

        # sending slope to shader
        glUniform1i(slice_loc, self.curr_slice)

        # sending exposure to shader
        glUniform1f(exposure_loc, self.exposure)

        # ------------
        # Binding Vertex Buffer Object
        glBindBuffer(GL_ARRAY_BUFFER, VBO)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.vertices)

        # Binding Element Buffer Object
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
        glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, self.indices)

        # Vertices Element
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, self.vertices.itemsize * 7, ctypes.c_void_p(0))

        # Color Element
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, self.vertices.itemsize * 7, ctypes.c_void_p(8))

        # Texture Element
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, self.vertices.itemsize * 7, ctypes.c_void_p(20))

        # binding the texture

        if self.mpr_view == 1:
            glBindTexture(GL_TEXTURE_2D, self.ct_slices[self.curr_slice].TextureID)
        else:
            glBindTexture(GL_TEXTURE_2D, self.new_texture_list[self.curr_slice])
        # ------------
        # drawing to the screen
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)

    def change_view(self, view=1):
        print("changing view from {} to {}".format(self.mpr_view, view))
        self.mpr_view = view
        arr1 = []

        for k in range(len(self.ct_slices)):
            arr1.append(self.ct_slices[k].pixelarray)
        newarr = np.stack(arr1, axis=0).astype("int16")

        self.num_slices = newarr.shape[view - 1]
        # Axial
        if view == 1:
            z = 0
            y = 2
            x = 1
        # Coronal
        elif view == 2:
            z = 1
            y = 2
            x = 0
            # rotating image by 90 degrees as it is upside down
            newarr = np.rot90(newarr, 2, (0, 1))
        # Sagittal
        elif view == 3:
            z = 2
            y = 1
            x = 0
            # rotating image by 90 degrees as it is upside down
            newarr = np.rot90(newarr, 2, (0, 1))
            newarr = np.flip(newarr, 1)
        print(newarr.shape)
        texture_list = []

        # Usage Instructions----
        #          Z,Y,X
        # Axial:   0,2,1 - newarr[i,:,:]
        # Coronal  1,2,0 - newarr[:, i, :]
        # Sagittal 2,1,0 - newarr[:,:,i]
        for i in range(newarr.shape[z]):
            texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture)

            if view == 1:
                glTexImage2D(GL_TEXTURE_2D, 0, GL_R16F, newarr.shape[y], newarr.shape[x], 0, GL_RED, GL_FLOAT,
                             newarr[i, :, :])
            elif view == 2:
                glTexImage2D(GL_TEXTURE_2D, 0, GL_R16F, newarr.shape[y], newarr.shape[x], 0, GL_RED, GL_FLOAT,
                             newarr[:, i, :])
            elif view == 3:
                glTexImage2D(GL_TEXTURE_2D, 0, GL_R16F, newarr.shape[y], newarr.shape[x], 0, GL_RED, GL_FLOAT,
                             newarr[:, :, i])
            # input('freezing a')
            # Set the texture wrapping parameters
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            # Set texture filtering parameters
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

            # saving texture ID to be used later for the Draw Function
            texture_list.append(texture)

            glBindTexture(GL_TEXTURE_2D, 0)

            self.new_texture_list = texture_list


# this class stores information about individual ct slices
class CT_Slice:
    filename = 0
    TextureID = 0
    slice_location = 0
    patient_id = 0
    study_date = 0
    RescaleSlope = 0
    RescaleIntercept = 0
    pixelarray = 0

    # Size  # I dont know if this is needed?

    def __init__(self, filename):
        self.filename = filename
        self.load_dcm(filename)

    def load_dcm(self, filename):
        # deprecated code -- usable but is very slow
        # normal = normalize.normalize_dcm(filename)
        # print(normal.nbytes)
        # texture = glGenTextures(1)
        # glBindTexture(GL_TEXTURE_2D, texture)
        # # Specifying 2D image (DICOM) to be mapped to the screen (Format: Single Channel)
        # glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, normal.shape[0], normal.shape[1], 0, GL_RED, GL_FLOAT, normal)

        ds = pydicom.dcmread(filename)

        # abc = str(ds)  # to get all of the data tags

        self.slice_location = ds.get("SliceLocation")
        self.patient_id = ds.get("PatientID")
        self.study_date = ds.get("StudyDate")
        self.RescaleSlope = ds.get("RescaleSlope")
        self.RescaleIntercept = ds.get("RescaleIntercept")

        normal = ds.pixel_array

        self.pixelarray = normal
       # print("rows: {}, col: {}".format(normal.shape[0], normal.shape[1]))
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_R16F, normal.shape[0], normal.shape[1], 0, GL_RED, GL_FLOAT, normal)

        # input('freezing a')
        # Set the texture wrapping parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        # Set texture filtering parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        # saving texture ID to be used later for the Draw Function
        self.TextureID = texture

        # come back to me
        # storing size of the image (likely width by height but not sure)
        # self.Size = glm.vec2(normal.shape[0], normal.shape[1])

        glBindTexture(GL_TEXTURE_2D, 0)
