# import tkinter as tk
# from tkinter import filedialog as fd

# open a directory
# tk.Tk().withdraw()
# directory = fd.askdirectory()
# print(directory)

# open a filename (should probably be set to only .dcm)
# tk.Tk().withdraw()
# file = tk.filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("Dicom Files","*.dcm"),("all files","*.*")))
# print(file)

import ctypes


class RECT(ctypes.Structure):
    _fields_ = [
        ('left', ctypes.c_long),
        ('top', ctypes.c_long),
        ('right', ctypes.c_long),
        ('bottom', ctypes.c_long)
    ]


def getWorkArea():
    SPI_GETWORKAREA = 48
    SPI = ctypes.windll.user32.SystemParametersInfoW
    SPI.restype = ctypes.c_bool
    SPI.argtypes = [
        ctypes.c_uint,
        ctypes.c_uint,
        ctypes.POINTER(RECT),
        ctypes.c_uint
    ]

    rect = RECT()

    result = SPI(
        SPI_GETWORKAREA,
        0,
        ctypes.byref(rect),
        0
    )
    if result:
        #print('it worked!')
        # print(rect.left)
        # print(rect.top)
        # print(rect.right)
        # print(rect.bottom)
        return rect
