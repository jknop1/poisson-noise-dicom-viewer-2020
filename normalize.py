# ------------------------------------------------------------------
# File: normalize
# Purpose: contains a function that normalizes data given parameters
# Author: Jacob Knop
# Date: Summer 2020
# ------------------------------------------------------------------

import pydicom
import numpy as np
from pydicom.data import get_testdata_files
from pydicom.tag import Tag


# slightly deprecated as it is no longer in use as functionality was moved within a shader
# ----------------------------------------------------------
# function: normalize_dcm
# purpose: to read in a DICOM FILE using pydicom and
#          normalize the data such that it can be visualized
#          by OpenGL
# parameters: filename
# 1. filename - the file name of a given DICOM file to normalize
# ------------------------------------------------------------
def normalize_dcm(filename):  # this is inefficient and needs to be fixed later
    #filename = "D:/Luna16 Dataset/LIDC-IDRI/LIDC-IDRI-0001/01-01-2000-30178/3000566-03192/000002.dcm"

    ds = pydicom.dcmread(filename)
    data = ds.pixel_array
    print(ds)
    # getting the number of rows and columns in the image
    rows = ds.get("Rows")
    columns = ds.get("Columns")

    # **********************************************
    # equation for normalization:
    #     (x - min(d))(max(n) - min(n))
    # y = ----------------------------- + min(n)
    #           (max(d) - min(d)
    #
    # where d = range of data set being normalized
    # where n = range of normalized data
    # ***********************************************
    # attempting to normalize the data
    # min_d = -1024
    # max_d = 2000
    # min_n = 0
    # max_n = 1

    # creating a float numpy array to store the new normalized values from the Dicom file
    normalized = np.ndarray(shape=(rows, columns), dtype=float)

    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            if data[i][j] >= 2000:
                normalized[i][j] = 1
            else:
                normalized[i][j] = (1/3024)*(data[i][j]) + (1024/3024)  #(((data[i][j] - min_d) * (max_n - min_n)) / (max_d - min_d)) + min_n

    # for debugging purposes only - shows inside of file
    # for i in range(data.shape[0]):
    #     for j in range(data.shape[1]):
    #         print(normalized[i][j])

    return normalized


# --------------------------------------------------------------
# function: normalize_pixel
# purpose: this function will normalize a pixel to screen/window
#          coordinates given a pixel coordinate
# parameters: pix_loc, height, width
# 1. pix_loc - a given pixel location to be normalized
# 2. height  - height of a given glfw window
# 3. width   - width of a given glfw window
# --------------------------------------------------------------
def normalize_pixel(x, y, height, width):
    # normalizing x and y coordinates (times 2 ensures that the correct number of pixels is displayed)
    cx = ((2 / width)*x) - 1
    cy = ((-2 / height) *y) + 1

    # return normalized
    return cx, cy
