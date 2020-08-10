# --------------------------------------------------------------------------------------
# File: Dicom_Program
# Purpose: Draws CT scans (via DICOM files), buttons, and visual artifacts to the screen
#          to attempt to model a typical DICOM Viewer.
# Author: Jacob Knop
# Date: Summer 2020
# ---------------------------------------------------------------------------------------


# External File Dependencies
import glfw
import numpy as np
import sys  # used to terminate the program early
import glm
import pydicom  # used in reading dicom files
import freetype  # used in text rendering

# file dialog opening (seems to be included with Python)
import tkinter as tk
from tkinter import filedialog as fd

# Standard Library Dependencies
import time

# Internal File Dependencies
import normalize
from normalize import normalize_dcm

import Button  # used for generating buttons
from Button import *

import Read_Dicom  # used for reading and displaying dicom images
from Read_Dicom import CTScan

import windowsWorkArea  # used for getting information about displaying to the screen
from windowsWorkArea import *

# START: global variables-----
# mouse coordinates (mouse_x, mouse_y)
mouse_x = 0
mouse_y = 0
mouse_left_press = 0
start_mouse_x = 0
start_mouse_y = 0
act = 0

# image translation variables (x_sh, y_sh, z_sh)
ct_slice = 0
slicenum = 0  # which slice the ct scan is on
setting = 0  # 0 - do nothing, 1 - zoom, 2 - translate, 3 - use slider
ff_flag = 0

# used for scene manipulation (need a better solution for this)
zoom = 1
mod = glm.vec2(0, 0)
trans = glm.vec2(0, 0)

# for the slider
slider_t = 0
slider_mod = 0

# FOR TESTING
start_time = time.time()

# height and width of the glfw window - determined at run-time
width = 0
height = 0

# shader global variables
shader = 0
generalshader = 0
text_shader = 0
slider_shader = 0
VBO = 0
EBO = 0

# for generating text
rnd = 0

buttoni = 0  # button variable holder
infobanner = 0  # used to test my info banner
slidebar = 0

# shader configuration (for Dicom)
vertex_dcm_src = """
# version 420

layout(location = 0) in vec2 a_position;
layout(location = 1) in vec3 a_color;
layout(location = 2) in vec2 a_texture;
uniform mat4 model;
uniform mat4 projection;

out vec3 v_color; //not useful in this shader
out vec2 v_texture;

uniform sampler2D s_texture;

void main()
{
    
    gl_Position = projection * model * vec4(a_position, 0, 1.0);
    
    //flipping texture (not sure if it should be flipped though)
    v_texture = vec2(1 - a_texture.x, a_texture.y);
}
"""

fragment_dcm_src = """
# version 330

in vec3 v_color; //not useful in this shader
in vec2 v_texture;
out vec4 out_color;

uniform int sliceNumber;
uniform float sliderVal;
uniform sampler2D s_texture;


// hash table
uint S[256] = { 0x29, 0x2E, 0x43, 0xC9, 0xA2, 0xD8, 0x7C, 0x01, 0x3D, 0x36, 0x54, 0xA1, 0xEC, 0xF0, 0x06, 0x13, 
  0x62, 0xA7, 0x05, 0xF3, 0xC0, 0xC7, 0x73, 0x8C, 0x98, 0x93, 0x2B, 0xD9, 0xBC, 0x4C, 0x82, 0xCA, 
  0x1E, 0x9B, 0x57, 0x3C, 0xFD, 0xD4, 0xE0, 0x16, 0x67, 0x42, 0x6F, 0x18, 0x8A, 0x17, 0xE5, 0x12, 
  0xBE, 0x4E, 0xC4, 0xD6, 0xDA, 0x9E, 0xDE, 0x49, 0xA0, 0xFB, 0xF5, 0x8E, 0xBB, 0x2F, 0xEE, 0x7A, 
  0xA9, 0x68, 0x79, 0x91, 0x15, 0xB2, 0x07, 0x3F, 0x94, 0xC2, 0x10, 0x89, 0x0B, 0x22, 0x5F, 0x21,
  0x80, 0x7F, 0x5D, 0x9A, 0x5A, 0x90, 0x32, 0x27, 0x35, 0x3E, 0xCC, 0xE7, 0xBF, 0xF7, 0x97, 0x03, 
  0xFF, 0x19, 0x30, 0xB3, 0x48, 0xA5, 0xB5, 0xD1, 0xD7, 0x5E, 0x92, 0x2A, 0xAC, 0x56, 0xAA, 0xC6, 
  0x4F, 0xB8, 0x38, 0xD2, 0x96, 0xA4, 0x7D, 0xB6, 0x76, 0xFC, 0x6B, 0xE2, 0x9C, 0x74, 0x04, 0xF1, 
  0x45, 0x9D, 0x70, 0x59, 0x64, 0x71, 0x87, 0x20, 0x86, 0x5B, 0xCF, 0x65, 0xE6, 0x2D, 0xA8, 0x02, 
  0x1B, 0x60, 0x25, 0xAD, 0xAE, 0xB0, 0xB9, 0xF6, 0x1C, 0x46, 0x61, 0x69, 0x34, 0x40, 0x7E, 0x0F, 
  0x55, 0x47, 0xA3, 0x23, 0xDD, 0x51, 0xAF, 0x3A, 0xC3, 0x5C, 0xF9, 0xCE, 0xBA, 0xC5, 0xEA, 0x26, 
  0x2C, 0x53, 0x0D, 0x6E, 0x85, 0x28, 0x84, 0x09, 0xD3, 0xDF, 0xCD, 0xF4, 0x41, 0x81, 0x4D, 0x52, 
  0x6A, 0xDC, 0x37, 0xC8, 0x6C, 0xC1, 0xAB, 0xFA, 0x24, 0xE1, 0x7B, 0x08, 0x0C, 0xBD, 0xB1, 0x4A, 
  0x78, 0x88, 0x95, 0x8B, 0xE3, 0x63, 0xE8, 0x6D, 0xE9, 0xCB, 0xD5, 0xFE, 0x3B, 0x00, 0x1D, 0x39, 
  0xF2, 0xEF, 0xB7, 0x0E, 0x66, 0x58, 0xD0, 0xE4, 0xA6, 0x77, 0x72, 0xF8, 0xEB, 0x75, 0x4B, 0x0A, 
  0x31, 0x44, 0x50, 0xB4, 0x8F, 0xED, 0x1F, 0x1A, 0xDB, 0x99, 0x8D, 0x33, 0x9F, 0x11, 0x83, 0x14 };
  
const float PI = 3.1415926535897932384626433832795;

uniform vec3 normalization_values;
/* information needed to dynamically implement normalization based on individual slices
//  for reference
//  normalization_values.x will equal the maximum value
//  normalization_values.y will equal the slope
//  normalization_values.z will equal the intercept
*/

// 2D Random

float random (vec2 st) {
    return fract(sin(dot(st.xy,
                         vec2(12.9898,78.233)))*
        43758.5453123);
}

int factorial(int val){
    int fact = 1;
    while(val > 1){
        fact *= val;
        val--;
    }
    return fact;
}

void main()
{
    //swizzling to get a single color channel to be in type: Monochrome
    float a = texture(s_texture, v_texture).r; // getting color at a given texture coordinate
    
    //normalizing pixel values between 0 and 1
    if(a <= 6000/*normalization_values.x*/){
        //mx+b equation split up because glsl wouldnt allow addition and division on the same line for some reason
        a = (a + 1024);
        a = a / 5119; //a / normalization_values.y;
    
    }
    else{
        a = 1;
    }
    
    // Calculate randum number
    uint ix = uint(v_texture.x * 512.0);
    uint iy = uint(v_texture.y * 512.0);
    uint iz = uint(sliceNumber);
    uint pos = ix + (iy<<9) + (iz<<18);
    
    uint ia = pos & uint(0xff);
    uint ib = (pos>>8)  & uint(0xff);
    uint ic = (pos>>16) & uint(0xff);
    uint id = (pos>>24) & uint(0xff);
    
    //uint ran1 = S[S[S[S[ia]^ib]^ic]^id];
    uint ran =  S[S[S[S[S[0] ^ ia]^ib]^ic]^id];
    uint ran1 = S[S[S[S[S[1] ^ ia]^ib]^ic]^id];
    uint ran2 = S[S[S[S[S[2] ^ ia]^ib]^ic]^id];
    uint ran3 = S[S[S[S[S[3] ^ ia]^ib]^ic]^id];
    
    float U1 = (ran + (ran1 << 8)) /  65536.0;
    float U2 = (ran2 + (ran3 << 8)) / 65536.0;
    
    float lambda = a * (sliderVal);
    // to sample a poisson distribution from a normal distribution, do Z0 * sqrt(LAMBDA) + LAMBDA
    float Z0 = sqrt(-2 * log(U1)) * cos(2 * PI * U2);
    Z0 = Z0 * sqrt(lambda) + lambda;
   
   
    // test for noise
    /*
    vec2 st = gl_FragCoord.xy/512;
    float b = random(st);
    b = pow(b, 3) + b;
    a *= b;
    */
    
    // add horizontal lines across image
    /*
    vec2 st = gl_FragCoord.xy/512;
    st = st * 10;
    vec2 b = a * fract(st);
    a = b.y;
    */
        
    //a = Z0 / sliderVal; // uncomment me for noise
    // setting the color to display
    vec4 col_ = vec4(a, a, a, 1);
    out_color = col_;
   
    // DEPRECATED CODE BUT KEPT HERE FOR REFERENCE
    //out_color = vec4(texture(s_texture, v_texture).r ); // * vec4(v_color, 1); 
    //out_color = texture(s_texture, v_texture); // * vec4(v_color, 1.0f);
    
}
"""

# shader configuration (for general OpenGL Plotting)
vertex_src = """
# version 330

layout(location = 0) in vec3 a_position;
layout(location = 1) in vec3 a_color;
uniform mat4 projection;

out vec3 v_color;

void main()
{
    gl_Position = vec4(a_position, 1.0);
    v_color = a_color;
}
"""

fragment_src = """
# version 330

in vec3 v_color;
out vec4 out_color;

void main()
{
    vec2 pos = vec2(gl_FragCoord.x, gl_FragCoord.y);
    //if (pos.x > 0){
    //    out_color = vec4(0,1,1,1);
    //}
    //else{
    //    out_color = vec4(v_color, 1.0);
    //}
    out_color = vec4(v_color, 1.0);
}
"""

text_vs = """
# version 330

layout(location = 0) in vec2 a_position;
layout(location = 1) in vec3 a_color;
layout(location = 2) in vec2 a_texture;

out vec3 v_color;
out vec2 v_texture;
uniform mat4 projection;
void main()
{

    gl_Position = projection * vec4(a_position.x, a_position.y, 0, 1.0);
    v_color = a_color;
    v_texture = vec2(a_texture.x, 1 - a_texture.y);
}
"""

text_fs = """
# version 330

in vec3 v_color;
in vec2 v_texture;

out vec4 out_color;

uniform sampler2D s_texture;

void main()
{
    //swizzling to get a single color channel to be in type: Monochrome
    vec4 sampled = vec4(v_color, texture(s_texture, v_texture).r);
    out_color = vec4(texture(s_texture, v_texture).r)*sampled;
}
"""

# shader configuration (for general OpenGL Plotting)
slider_vertex_src = """
# version 330

layout(location = 0) in vec3 a_position;
layout(location = 1) in vec3 a_color;
uniform mat4 model;


out vec3 v_color;

void main()
{

    gl_Position = model * vec4(a_position, 1.0);
    v_color = a_color;
}
"""

slider_fragment_src = """
# version 330

in vec3 v_color;
out vec4 out_color;

uniform vec4 coordx;
/*
coordx.x - starting position of the track 
coordx.y - current right edge of the thumb
coordx.z - original left edge of the thumb
coordx.w - ending position of the track
*/

uniform vec2 coordy;
/*
coordy.x - top y-position of the slider
coordy.y - bottom y-position of the slider
*/
void main()
{
    vec2 pos = vec2(gl_FragCoord.x, gl_FragCoord.y);
        
    // draws the track that the thumb can slide on 
    if (pos.y >= coordy.y && pos.y <= coordy.x && pos.x > coordx.y && pos.x < coordx.w){
        out_color = vec4(.4,.4,.4,1);
    }
    
    // draws green behind the thumb as it slides
    else if(pos.y >= coordy.y && pos.y <= coordy.x && pos.x >= coordx.z && pos.x < coordx.x)
    {
        out_color = vec4(0,1,0,1);
    }
    
    // draws colors based on what OpenGL send to the shader program
    else{
        out_color = vec4(v_color, 1.0);
    }
    //out_color = vec4(v_color, 1.0);
}
"""


# END: global variables-----


# START: Button functions --------------------------------------------------------------/
# sets a flag to start the ability to zoom
def zoom_in():
    global setting
    print('zooming')
    setting = 1


# sets a flag to start the ability to translate
def translate():
    print('translate')
    global setting
    setting = 2


def slide():
    global setting
    print("i can slide now")
    setting = 3


def set_mpr(view):
    print("view: {}".format(view))
    global ct_slice
    if ct_slice:
        ct_slice.change_view(view)
        #ct_slice.mpr_view = view


# open a file of type Dicom (.dcm) - Currently not in use
# def switch():
#     global ff_flag, ct_slice
#     ff_flag = not ff_flag
#     if ct_slice:
#         ct_slice.ff_flag = ff_flag
#         # param.ff_flag = not param.ff_flag
#     print(ff_flag)

def open_folder():
    global ct_slice, height, width
    tk.Tk().withdraw()
    # checking whether the user opened a file/folder. If they did, then load a CT Scan and center it - Else do nothing
    # opened = 0
    # while not opened:
    #     name_ = fd.askdirectory()
    #     if name_:
    #         del ct_slice
    #         # ct_slice = 0
    #         ct_slice = CTScan(name_, shader, ff_flag)
    #         ct_slice.set_alignment("center", height, width)
    #         opened = 1
    #
    #         # checking to see if a file/folder was opened - if no folder/file was opened
    #         # open file dialog again until they choose a valid option
    #         if ct_slice.num_slices == 0:
    #             opened = 0

    name_ = fd.askdirectory()
    if name_:
        del ct_slice
        ct_slice = CTScan(name_, shader, 0)
        ct_slice.set_alignment("center", height, width)

        # checking to see if a file/folder was opened - if no folder/file was opened then delete the object
        # so the program does not attempt to draw it
        if ct_slice.num_slices == 0:
            del ct_slice
            ct_slice = 0


def open_file():
    global ct_slice, height, width
    tk.Tk().withdraw()
    name_ = tk.filedialog.askopenfilename(initialdir="/", title="Select file",
                                          filetypes=(("Dicom Files", "*.dcm"), ("all files", "*.*")))
    # checking whether the user opened a file/folder. If they did, then load a CT Scan and center it - Else do nothing
    if name_:
        del ct_slice
        ct_slice = CTScan(name_, shader, 1)
        ct_slice.set_alignment("center", height, width)


# used to open a folder
def open_ff():
    global ff_flag, ct_slice, height, width
    tk.Tk().withdraw()
    name_ = 0
    opened = 0
    # while not opened:
    if ff_flag == 0:  # open a folder
        name_ = fd.askdirectory()
    else:  # open a file
        name_ = tk.filedialog.askopenfilename(initialdir="/", title="Select file",
                                              filetypes=(("Dicom Files", "*.dcm"), ("all files", "*.*")))
    # checking whether the user opened a file/folder. If they did, then load a CT Scan and center it - Else do nothing
    if name_:
        del ct_slice
        # ct_slice = 0
        ct_slice = CTScan(name_, shader, ff_flag)
        ct_slice.set_alignment("center", height, width)
        opened = 1

        # checking to see if a file/folder was opened - if no folder/file was opened
        # open file dialog again until they choose a valid option
        if ct_slice.num_slices == 0:
            opened = 0


def do_nothing():
    pass


# END: Button functions ---------------------------------------------------------------*

# START---------------------------------------------------------------------------------------/
# **************************************
# functions for GLFW Callback functions*
# **************************************

# resizes the opengl context allowing for the image on the window to change sizes as well
def window_resize(window, width, height):
    # prevents crashing when minimizing the window
    print("width: {}, height: {}".format(width, height))
    if width == 0 or height == 0:
        return 0

    # setting the viewport for the functions that use it to draw to the screen
    glViewport(0, 0, width, height)

    # resize buttons based on new window size
    global buttoni
    buttoni.resize(width, height)

    # passing parameters to the text object and text_shader to ensure that the size remains correct with window resizing
    global rnd
    glUseProgram(text_shader)
    proj_loc = glGetUniformLocation(text_shader, "projection")
    projection = glm.ortho(0, width, 0, height)
    glUniformMatrix4fv(proj_loc, 1, GL_FALSE, glm.value_ptr(projection))
    rnd.set_hw(height, width)

    print("width: {}, height: {}".format(width, height))  # remove me at some point

    # re-centering the ct-slice on the screen
    global ct_slice
    if ct_slice:
        ct_slice.set_alignment('center', height, width)


# setting the function for glfw to call when the mouses cursor position changes
def cursor_position_callback(window, xpos, ypos):
    global mouse_x, mouse_y, setting, ct_slice, mouse_left_press
    global start_mouse_x, start_mouse_y, height, width, act
    global buttoni
    print("({}, {})".format(xpos, ypos))

    # setting global mouse coordinates
    mouse_x = xpos
    mouse_y = ypos

    buttoni.is_hovering(mouse_x, mouse_y)
    # if the mouse is clicked down and it was not a button click check to see whether
    # the user is panning around the image or zooming in
    if mouse_left_press and act:  # should try to put this in an on_click() function or something

        # zoom setting - zooming on the scene with the mouse (vertical only)
        global zoom
        if setting == 1 and ct_slice:
            print('zoom: {}'.format(zoom))
            # zooming in based on how far the mouse has moved from the original clicked area
            modifier = (mouse_y - start_mouse_y) * (2 / height)
            if zoom + modifier >= 1:
                ct_slice.zoom = zoom + modifier  # abs(mouse_y - start_mouse_y)
            print("zoom: {}".format(ct_slice.zoom))
        # panning/translation setting - translating scene with the mouse
        elif setting == 2 and ct_slice:
            global mod, trans
            print("x: {}, y: {}".format(ct_slice.translation.x, ct_slice.translation.y))

            # moving image based on how far the mouse has moved from the original clicked area
            # 2 / (width or height) / zoom is pixel normalization to ensure translation occurs properly
            mod.x = (mouse_x - start_mouse_x) * (2 / width) / zoom
            mod.y = (mouse_y - start_mouse_y) * (2 / height) / zoom
            ct_slice.translation.x = -mod.x + trans.x
            ct_slice.translation.y = mod.y + trans.y

        # slider setting
        elif setting == 3:
            global slider_t, slider_mod
            btn_num = 4  # which panel button to grab information from
            shift = (mouse_x - start_mouse_x)
            edge_left = buttoni.buttons[btn_num].x1
            left_threshold = buttoni.buttons[btn_num].x1 - buttoni.buttons[btn_num].currx1
            right_threshold = (buttoni.buttons[btn_num].sx2 - (buttoni.buttons[btn_num].sliderbase_width * .05)) - \
                              buttoni.buttons[btn_num].currx1
            # print("shift: {}, threshold: {}".format(shift, left_threshold))
            if left_threshold <= shift <= right_threshold:
                # sliding horizontally based on how far the mouse has moved from the original clicked area
                # 2 / width normalizes to screen coordinates - width / 2 pushes screen coordinates
                #   back to pixel coordinates

                # setting modifier for how far the thumb slider has moved
                slider_mod = shift * (2 / width)

                # translating based off current translation modifier + previous location from sliding
                buttoni.buttons[btn_num].thumb_translate.x = slider_mod + slider_t

                # settomg right edge current location for slider track shading
                buttoni.buttons[btn_num].currx2 = buttoni.buttons[btn_num].x2 + (slider_t + slider_mod) * width / 2


# setting the function to receive mouse button presses
def mouse_button_callback(window, button, action, mods):
    global mouse_x, mouse_y, mouse_left_press, buttoni, act, setting, start_mouse_x, start_mouse_y
    if action == glfw.PRESS:
        if button == glfw.MOUSE_BUTTON_LEFT:
            if buttoni.check_click(mouse_x, mouse_y):
                if setting == 3:
                    act = 1
                    mouse_left_press = 1
                    start_mouse_x = mouse_x
                    start_mouse_y = mouse_y
                else:
                    act = 0
            else:
                act = 1

                # sets starting point to do calculations for panning around the CT scan
                mouse_left_press = 1
                start_mouse_x = mouse_x
                start_mouse_y = mouse_y
                print("left button")
                # print("cursor location: ({}, {})".format(mouse_x, mouse_y))

        elif button == glfw.MOUSE_BUTTON_RIGHT:
            print("right button")
        elif button == glfw.MOUSE_BUTTON_MIDDLE:
            print("middle button")

    elif action == glfw.RELEASE:
        mouse_left_press = 0
        buttoni.check_unclick(mouse_x, mouse_y)
        print("Released")
        if act:
            # this is really tacky and should hopefully have a better solution
            global ct_slice, zoom, trans, mod
            if ct_slice:
                if setting == 1:
                    zoom = ct_slice.zoom
                elif setting == 2:
                    trans.xy = glm.vec2(trans.x - mod.x, trans.y + mod.y)
            if setting == 3:
                global slider_t, slider_mod
                slider_t = slider_t + slider_mod
                btn_num = 4
                buttoni.buttons[btn_num].currx1 = buttoni.buttons[btn_num].x1 + slider_t * width / 2
                buttoni.buttons[btn_num].currx2 = buttoni.buttons[btn_num].x2 + slider_t * width / 2
                setting = 0
                slider_mod = 0
        act = 0
    else:
        print(mouse_x, mouse_y)


def key_callback(window, key, scancode, action, mods):
    # reset scene to how it was at the beginning
    if key == glfw.KEY_R:
        global ct_slice, zoom, mod, trans
        if ct_slice:
            ct_slice.zoom = 1
            zoom = 1
            ct_slice.translation = glm.vec3(0, 0, 0)
            mod = glm.vec2(0, 0)
            trans = glm.vec2(0, 0)

    # close the program
    if key == glfw.KEY_ESCAPE:
        glfw.terminate()
        sys.exit("Program Exited on Escape")


# callback for the scrollwheel
def scroll_callback(window, xoffset, yoffset):
    global slicenum, ct_slice

    # scrolling between slice 1 and slice N --> N = ct_slice.num_slices - 1
    if ct_slice:
        # if scrolling down and slice num is greater than 0 don't go to previous slice
        if yoffset < 0 and slicenum > 0:
            slicenum = slicenum - 1
        # if scrolling up and slicenum is less than the maximum slice, proceed to the next slice
        elif yoffset > 0 and slicenum < ct_slice.num_slices - 1:
            slicenum = slicenum + 1
        # if attempting to go to previous slice on slice 0 go to last slice
        # and if attempting to go to next slice on max slice go to first slice
        else:
            slicenum = abs(slicenum + 1 - ct_slice.num_slices)

        ct_slice.curr_slice = slicenum
        print(slicenum)


# END--------------------------------------------------------------------------------------*


# init: initializes variables for (this) OpenGL program
def init():
    # setting blend function for text rendering
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # Compiling shader's to allow manipulation of the graphical pipeline --------------
    global shader, generalshader, text_shader, slider_shader, VBO, EBO
    shader = compileProgram(compileShader(vertex_dcm_src, GL_VERTEX_SHADER),
                            compileShader(fragment_dcm_src, GL_FRAGMENT_SHADER))
    # plots generic things like rectangles
    generalshader = compileProgram(compileShader(vertex_src, GL_VERTEX_SHADER),
                                   compileShader(fragment_src, GL_FRAGMENT_SHADER))
    # allows for generation of text on screen
    text_shader = compileProgram(compileShader(text_vs, GL_VERTEX_SHADER),
                                 compileShader(text_fs, GL_FRAGMENT_SHADER))

    slider_shader = compileProgram(compileShader(slider_vertex_src, GL_VERTEX_SHADER),
                                   compileShader(slider_fragment_src, GL_FRAGMENT_SHADER))
    # ----------------------------------------------------------------------------------

    # vertex + element buffer object + texture object ----------------------------------
    VBO = glGenBuffers(1)
    EBO = glGenBuffers(1)
    # pre-allocating buffer's as the size remains the same over the entire draw period
    glBindBuffer(GL_ARRAY_BUFFER, VBO)
    # 4 * 7 * 4 = bytes x elements per row x number of rows
    glBufferData(GL_ARRAY_BUFFER, 4 * 7 * 4, None, GL_DYNAMIC_DRAW)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, 4 * 6, None, GL_DYNAMIC_DRAW)
    # ----------------------------------------------------------------------------------

    # grabbing height and width
    global height, width

    # Creating a Text Object and loading the Arial Font (initializing some other formatting stuff)
    global rnd
    rnd = Text(height, width, text_shader)
    rnd.load_font()

    # creating buttons to pass to a panel for handling ---------------------------
    global buttoni

    # load button for file opening
    button = PullDownMenu(0, 0, 25, 50, height, width, rnd, generalshader, shader)
    button.set_text("Load")
    button.set_function(open_folder)

    # drop down menu buttons for the load button
    button1 = TextButton(0, 25, 25, 100, height, width, rnd, generalshader, shader)
    button1.set_text("Load Folder", "center")
    button1.set_function(open_folder)
    button.add_pull_down_button(button1)
    button1 = TextButton(0, 50, 25, 100, height, width, rnd, generalshader, shader)
    button1.set_text("Load File", "center")
    button1.set_function(open_file)
    button.add_pull_down_button(button1)

    # load button for file opening
    # button = TextButton(0, 0, 25, 50, height, width, rnd, generalshader, shader)
    # button.set_function(open_ff)
    # button.set_text("Load")
    # button.set_alignment('center')
    #
    # # allows the user to switch between opening a file or opening a folder.
    # button_select = Button(51, 0, 25, 10, height, width, generalshader)
    # button_select.set_function(switch)

    button_zoom = TextButton(62, 0, 25, 50, height, width, rnd, generalshader, shader)
    button_zoom.set_text("Zoom", "center")
    button_zoom.set_function(zoom_in)

    button_translate = TextButton(113, 0, 25, 50, height, width, rnd, generalshader, shader)
    button_translate.set_text("Pan", "center")
    button_translate.set_function(translate)

    button_threshold = PullDownMenu(164, 0, 25, 50, height, width, rnd, generalshader, shader)
    button_threshold.set_text("MPR")
    threshold_set1 = TextButton(164, 25, 25, 100, height, width, rnd, generalshader, shader)
    threshold_set1.set_text("Axial", "center")
    threshold_set1.set_function(set_mpr, 1)

    threshold_set2 = TextButton(164, 50, 25, 100, height, width, rnd, generalshader, shader)
    threshold_set2.set_text("Coronal", "center")
    threshold_set2.set_function(set_mpr, 2)

    threshold_set3 = TextButton(164, 75, 25, 100, height, width, rnd, generalshader, shader)
    threshold_set3.set_text("Sagittal", "center")
    threshold_set3.set_function(set_mpr, 3)
    button_threshold.add_pull_down_button(threshold_set1)
    button_threshold.add_pull_down_button(threshold_set2)
    button_threshold.add_pull_down_button(threshold_set3)
    # slider button
    global slidebar
    slidebar = SlideBar(226, 0, 25, 1600, height, width, rnd, slider_shader)
    slidebar.set_function(slide)

    # making a Panel and attaching buttons
    buttoni = Panel(0, 0, height, width)
    buttoni.add_button(button)
    buttoni.add_button(button_zoom)
    buttoni.add_button(button_translate)
    buttoni.add_button(button_threshold)
    buttoni.add_button(slidebar)
    # ----------------------------------------------------------------------------

    # info panel (location should be dynamic later on)
    global infobanner
    txt = ['X: ', 'Im: ', 'Date Taken: ', 'HU: ', 'Patient ID: ']
    infobanner = InfoBanner(0, 850, 100, 100, height, width, txt, rnd, text_shader)

    # used to map window size to pixels (1:1)
    glUseProgram(text_shader)
    proj_loc = glGetUniformLocation(text_shader, "projection")
    projection = glm.ortho(0, width, 0, height)
    glUniformMatrix4fv(proj_loc, 1, GL_FALSE, glm.value_ptr(projection))


# draw function: used to draw to the screen every frame
def draw():
    #global start_time
    #new_time = time.time()
    #print("Time Elapsed: {}".format(new_time - start_time))

    # Setting Background Color to Black (Medical Standard) for Drawing
    glClearColor(0, 0, 0, 1)

    # LOADING CT SCAN --
    global ct_slice, VBO, EBO
    global buttoni
    if ct_slice:
        ct_slice.exposure = buttoni.buttons[4].slider_value
        ct_slice.draw(VBO, EBO)

    # LOADING PANEL OF BUTTONS --
    global height, width
    buttoni.draw(VBO, EBO)

    # DEPRECATED CODE - KEPT AS REFERENCE **************************
    # ATTEMPTING TO DRAW TEXT OVER A BUTTON
    # custom_text = "LOAD"
    # rnd.render_text(custom_text, buttoni.x1, buttoni.y1, VBO, EBO)
    # **************************************************************

    # ATTEMPTING TO DRAW AN INFORMATION BANNER
    global infobanner, mouse_x, mouse_y, slicenum
    if ct_slice:
        info = 0
        mx = 0
        my = 0

        # checking whether the mouse location is within the area of the ct-slice area and then converting
        # the pixel found at that location to Hounsfield units
        if ct_slice.mpr_view == 1 and ct_slice.x1 <= mouse_x < ct_slice.x2 and ct_slice.y1 <= mouse_y <= ct_slice.y2:
            # getting pixel data at point row: mouse_y - ct_slice.y1, column: mouse_x - ct_slice.x1
            info = ct_slice.ct_slices[slicenum].pixelarray[int(mouse_y - ct_slice.y1)][
                int(mouse_x - ct_slice.x1)]

            # converting grabbed pixel to Hounsfield units: formula = slope * pixel + rescale_intercept
            info = info * ct_slice.ct_slices[slicenum].RescaleSlope + ct_slice.ct_slices[slicenum].RescaleIntercept

            # setting mouse info to print
            mx = int(mouse_x - ct_slice.x1)
            my = int(mouse_y - ct_slice.y1)

        # if the mouse coordinates are outside the range of the image do not display coordinates
        else:
            mx = 'x'
            my = 'x'

        # Displaying Information: (X,Y, SLICE NUMBER, DATE TAKEN, HOUNSFIELD UNITS, PATIENT ID)
        params = [str(mx) + ", Y:" + str(my),  # x and y mouse coordinates
                  str(slicenum + 1) + '/' + str(ct_slice.num_slices),  # current slice number being displayed
                  str(ct_slice.ct_slices[0].study_date[4:6] + '/' + ct_slice.ct_slices[0].study_date[6:8]
                      + '/' + ct_slice.ct_slices[0].study_date[0:4]),
                  str(info),  # HOUNSFIELD UNITS
                  str(ct_slice.ct_slices[0].patient_id)]  # patient id
        infobanner.update_info(params)
        infobanner.draw(VBO, EBO)

    # global ch_view
    # if ct_slice and not ch_view:
    #     ct_slice.change_view(1)
    #     ch_view = 1
    # if ct_slice and ch_view:
    #     ct_slice.draw_new_view(VBO, EBO)


# initializing glfw library
if not glfw.init():
    raise Exception("glfw can not be initialized!")

workArea = getWorkArea()
print("right: {}, bottom: {}".format(workArea.right, workArea.bottom))
# creating the window
# doing roundabout thing to get title bar size because Windows 10 is stupid and decorations
# are not accounted for

# setting a garbage window size as the window is required to get the title bar size
window = glfw.create_window(workArea.right, workArea.bottom, "Dicom Viewer", None, None)
# getting title bar size
frameSize = glfw.get_window_frame_size(window)  # frameSize[1] is the height of the title bar

# getting actual height and width of the window

height = workArea.bottom - frameSize[1]
width = workArea.right

# setting correct window size
glfw.set_window_size(window, width, height)  # causes issues if the original set size isn't set

glfw.window_hint(glfw.SCALE_TO_MONITOR, glfw.TRUE)

# check if window was created
if not window:
    glfw.terminate()
    raise Exception("glfw window can not be created!")

# set window's position (should probably be dynamic)
glfw.set_window_pos(window, 0, frameSize[1])

# setting callback functions to get mouse button, cursor, and keyboard information in real time
glfw.set_window_size_callback(window, window_resize)  # set the callback function for window resize
glfw.set_cursor_pos_callback(window, cursor_position_callback)  # setting cursor callback to get mouse information
glfw.set_mouse_button_callback(window, mouse_button_callback)
glfw.set_key_callback(window, key_callback)
glfw.set_scroll_callback(window, scroll_callback)
# make the context current
glfw.make_context_current(window)

# initialize variables for the start of the program
init()
# fixing gl size after doing roundabout things to set the right window size
glViewport(0, 0, width, height)

# the main application loop
while not glfw.window_should_close(window):
    glfw.poll_events()

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    draw()
    glfw.swap_buffers(window)

# terminate glfw, free up allocated resources
glfw.terminate()
