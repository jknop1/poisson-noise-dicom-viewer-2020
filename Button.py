# --------------------------------------------------------------------------------------
# File: Button.py
# Purpose: Allows the drawing of visual artifacts to the screen. Currently includes
#          the ability to draw solid and hollow rectangles
# Author: Jacob Knop
# Date: Summer 2020
# ---------------------------------------------------------------------------------------

# external dependencies
import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import freetype
import glm

# internal dependencies
import normalize
from normalize import normalize_pixel


# -----------------------------------------------------------------------
# Class: Panel
# Purpose: Manages buttons given to it and displays a banner of buttons
# -----------------------------------------------------------------------
class Panel:
    # variables that store where on the screen that a button is
    vertices = 0
    indices = np.array([0, 1, 2, 2, 3, 1], dtype=np.uint32)
    x1 = 0
    y1 = 0
    buttons = []

    # (x1, y1) upper left corner
    def __init__(self, x1, y1, height, width):
        self.x1 = x1
        self.y1 = y1
        # for i in range(0, num_buttons):
        #     button = Button(x1, y1, x1 + 40, y1 + 20, height, width)
        #     x1 = x1 + 40
        #     self.buttons.append(button)

    # given a button, the object will add it to its list of buttons in the button[] array
    def add_button(self, button):
        self.buttons.append(button)

    # the panel will draw all of the button objects it is managing
    def draw(self, VBO, EBO):
        for i in range(len(self.buttons)):
            self.buttons[i].draw(VBO, EBO)

    # the panel will check whether any of the buttons it is managing has been clicked
    def check_click(self, mouse_cx, mouse_cy):
        clicked = 0
        for i in range(len(self.buttons)):

            if self.buttons[i].check_click(mouse_cx, mouse_cy):
                clicked = clicked + 1
        if clicked > 0:
            return 1

    # when the mouse is unclicked, check if any of the buttons have events that are triggered
    # by it
    def check_unclick(self, mouse_cx, mouse_cy):
        for i in range(len(self.buttons)):
            self.buttons[i].check_unclick(mouse_cx, mouse_cy)

    # the panel will resize all of the buttons it is managing in the case that the window changes sizes
    def resize(self, width, height):
        for i in range(len(self.buttons)):
            self.buttons[i].resize(height, width)
            # self.buttons[i].set_vertices(height, width)

    # checking whether a button is being hovered over by the mouse
    def is_hovering(self, mouse_cx, mouse_cy):
        for i in range(len(self.buttons)):
            self.buttons[i].is_hovering(mouse_cx, mouse_cy)


# -----------------------------------------------------------------------
# Class: Button
# Purpose: Creates and allows the drawing of square button that can be
#          clicked and hovered over (for a darkening effect).
# -----------------------------------------------------------------------
class Button:
    # variables that store where on the screen that a button is
    vertices = 0
    indices = np.array([0, 1, 2, 2, 3, 1], dtype=np.uint32)
    x1 = 0
    x2 = 0
    y1 = 0
    y2 = 0
    function = 0
    btn_shader = 0
    color = [0.82, .82, 0.82]

    # (x1, y1) upper left corner
    # (x2, y2) lower right corner
    def __init__(self, x1, y1, height, width, window_height, window_width, btn_shader):
        print("window height: " + str(window_height))
        self.x1 = x1
        self.y1 = y1
        self.x2 = x1 + width
        self.y2 = y1 + height
        self.set_vertices(window_height, window_width)

        self.btn_shader = btn_shader

    # the vertices and indices array do not need to stored and can be calculated?
    def set_vertices(self, window_height, window_width):
        # calculating screen coordinates to place the button on
        x1, y1 = normalize.normalize_pixel(self.x1, self.y1, window_height, window_width)
        x2, y2 = normalize.normalize_pixel(self.x2, self.y2, window_height, window_width)

        # DEPRECATED -- for setting an unchanging colored button
        # self.vertices = [x1, y1, 0.0, 0.5, 0.8,
        #                  x2, y1, 0.0, 0.5, 0.8,
        #                  x1, y2, 1.0, 1.0, 1.0,
        #                  x2, y2, 1.0, 1.0, 1.0]

        # generating a set of vertices to map the button to the screen with a given
        # color
        self.vertices = [x1, y1, self.color[0], self.color[1], self.color[2],
                         x2, y1, self.color[0], self.color[1], self.color[2],
                         x1, y2, self.color[0], self.color[1], self.color[2],
                         x2, y2, self.color[0], self.color[1], self.color[2]]
        self.vertices = np.array(self.vertices, dtype=np.float32)

    # ------------------------------------------------------------------
    # Function: check_click
    # Purpose: given the coordinates on the screen, this function checks
    #          whether the button was clicked
    # -------------------------------------------------------------------
    def check_click(self, mouse_cx, mouse_cy):
        if self.x1 <= mouse_cx <= self.x2 and self.y1 <= mouse_cy <= self.y2:
            print("button pressed")
            # whether a button has a function assigned to it. If it it doesnt, do nothing
            if self.function:
                # if button has function attributes, call the function with those attributes
                if self.attr:
                    self.function(self.attr)

                # if a function has no attributes, just call the function
                else:
                    self.function()
                return 1

    # checks whether the button was unclicked
    def check_unclick(self, mouse_cx, mouse_cy):
        pass

    # will set a specific function to a button (not sure how to do this)
    def set_function(self, func_=None, attributes=None):
        if func_:
            self.function = func_
            self.attr = attributes
            print("attributes: {}".format(self.attr))

    # resizes the button based on window size changes
    def resize(self, height, width):
        self.set_vertices(height, width)

    # changes the buttons color when the button is hovered over
    def is_hovering(self, mouse_cx, mouse_cy):
        if self.x1 <= mouse_cx <= self.x2 and self.y1 <= mouse_cy <= self.y2:
            self.color = [0.72, .72, 0.72]
        else:
            self.color = [0.82, .82, 0.82]
        for i in range(4):
            self.vertices[5 * i + 2] = self.color[0]
            self.vertices[5 * i + 3] = self.color[1]
            self.vertices[5 * i + 4] = self.color[2]

    # this function draws the button to the screen
    def draw(self, VBO, EBO):
        # binding shader for drawing
        glUseProgram(self.btn_shader)

        # binding buffers to overwrite for drawing to the screen
        glBindBuffer(GL_ARRAY_BUFFER, VBO)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.vertices)

        # Element Buffer Object
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
        glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, self.indices)

        # writing to vertex variable in shader
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(0))

        # writing to color variable in shader
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(8))

        # telling opengl to draw to the screen
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)


# -----------------------------------------------------------------------
# Class: TextButton
# Purpose: Creates and allows the drawing of square button with text on it
#          that can be clicked and hovered over (for a darkening effect).
# -----------------------------------------------------------------------
class TextButton(Button):
    text_shader = 0
    text = 0
    font = 0
    alignx = 0
    aligny = 0

    # (x1, y1) upper left corner
    # (x2, y2) lower right corner
    def __init__(self, x1, y1, height, width, window_height, window_width, font, btn_shader, text_shader):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x1 + width
        self.y2 = y1 + height
        self.set_vertices(window_height, window_width)

        self.btn_shader = btn_shader
        self.text_shader = text_shader
        self.font = font

    # sets the text that will be drawn to the screen on top of the button
    def set_text(self, text, alignment=0):
        self.text = text
        self.set_alignment(alignment)

    # draws the text button to the screen
    def draw(self, VBO, EBO):
        glUseProgram(self.btn_shader)
        glBindBuffer(GL_ARRAY_BUFFER, VBO)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.vertices)

        # Element Buffer Object
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
        glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, self.indices)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(0))

        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(8))

        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)

        glUseProgram(self.text_shader)

        self.font.render_text(self.text, self.x1 + self.alignx, self.y1 + self.aligny, VBO, EBO)

    # sets the alignment of the text on the button (default is set to the left edge of the button)
    def set_alignment(self, alignment):
        if alignment == 'center':
            # centering text along button y-axis
            self.aligny = - self.font.text_array[ord(self.text[0])].Size.y / 2 + ((self.y2 - self.y1) / 2)
            # centering text to along button x-axis
            advance = 0
            for i in range(len(self.text)):
                advance = advance + self.font.text_array[ord(self.text[i])].Advance / 64
                # lengthb = lengthb + self.font.text_array[ord(self.text[i])].Size.x
                # print("char: {}, length: {}".format(self.text[i], self.font.text_array[ord(self.text[i])].Size.x))
            self.alignx = (1 / 2) * (self.x2 - self.x1 - advance)

# useless function used for filler
def do_nothing():
    pass


# has buttons not really is one
class PullDownMenu:
    menu_open = 0  # if 0 - pull down menu not showing, if 1 - pull down menu showing
    function = 0
    attr = 0  # attributes for the function
    btn_shader = 0
    window_height = 0
    window_width = 0
    btn_number = 0

    #
    def __init__(self, x1, y1, height, width, window_height, window_width, font, btn_shader, txt_shader):
        self.btn_shader = btn_shader
        self.window_height = window_height
        self.window_width = window_width

        self.buttons = []
        # generating main button
        self.buttons.append(
            TextButton(x1, y1, height, width, window_height, window_width, font, btn_shader, txt_shader))

        offset = x1 + width + 1

        # generating button to function as pull down button
        self.buttons.append(Button(offset, y1, height, 10, window_height, window_width, btn_shader))
        self.buttons[1].set_function(do_nothing)

    # draw main button and pull down button
    def draw(self, VBO, EBO):
        if not self.menu_open:
            self.buttons[0].draw(VBO, EBO)  # main button
            self.buttons[1].draw(VBO, EBO)  # pull down button

        # if the menu is open then continue drawing it else don't draw the menu
        if self.menu_open:
            for i in range(len(self.buttons)):
                self.buttons[i].draw(VBO, EBO)

        # draw arrow for the pull down button
        # visual of button (coordinates as points)
        #  (s_x1, s_y1)----(s_x2, s_y1)
        #  \                          /
        #       \               /
        #           \      /
        #           (mid, s_y2)
        size_x = (self.buttons[1].x2 - self.buttons[1].x1)
        size_y = (self.buttons[1].y2 - self.buttons[1].y1)
        # print("x1: {}, x2: {}".format(self.buttons[1].x1, self.buttons[1].x2))

        s_x1, s_y1 = normalize.normalize_pixel(self.buttons[1].x1 + size_x * .10, self.buttons[1].y1 + size_y * 0.45
                                               , self.window_height, self.window_width)
        s_x2, s_y2 = normalize.normalize_pixel(self.buttons[1].x2 - size_x * 0.10, self.buttons[1].y2 - size_y * 0.25,
                                               self.window_height, self.window_width)

        mid = (s_x1 + s_x2) / 2

        verts = [s_x1, s_y1, 0, 0, 0,
                 s_x2, s_y1, 0, 0, 0,
                 mid, s_y2, 0, 0, 0]

        verts = np.array(verts, dtype=np.float32)
        indices = np.array([0, 1, 2], dtype=np.uint32)

        # binding shader to draw and binding VBO's and EBO's to overwrite shader/gpu memory
        # to write to the screen
        glUseProgram(self.btn_shader)
        glBindBuffer(GL_ARRAY_BUFFER, VBO)
        glBufferSubData(GL_ARRAY_BUFFER, 0, verts)

        # Element Buffer Object
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
        glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, indices)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(0))

        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(8))

        # draw arrow
        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, None)

    def check_click(self, mouse_cx, mouse_cy):
        # checking whether to only check if the main button
        # and pull down should be checked or if all of the buttons
        # need to be checked
        if self.menu_open:
            end = len(self.buttons)
        else:
            end = 2

        # checking whether buttons were clicked
        for start in range(end):
            if self.buttons[start].function:
                # check if the pulldown button or the main button was clicked
                if self.buttons[start].x1 <= mouse_cx <= self.buttons[start].x2 and self.buttons[
                    start].y1 <= mouse_cy <= self.buttons[start].y2:
                    # if the pull down button was pressed set the flag to draw the pull down menu
                    if start == 1:
                        self.menu_open = not self.menu_open
                    if self.buttons[start].function:

                        # if button has function attributes, call the function with those attributes
                        if self.buttons[start].attr:
                            print("calling function")
                            self.buttons[start].function(self.buttons[start].attr)

                        # if the pull down menu is open then check if any of the pull down buttons were
                        else:
                            self.buttons[start].function()

    def check_unclick(self, mouse_cx, mouse_cy):
        count = 0

        # checking whether any area outside of all of the buttons was pressed if the menu is being displayed
        # if it was then stop displaying the menu
        if self.menu_open:
            for i in range(len(self.buttons)):
                if self.buttons[i].x1 <= mouse_cx <= self.buttons[i].x2 and self.buttons[i].y1 <= mouse_cy <= \
                        self.buttons[i].y2:
                    count = 1
            if not count:
                self.menu_open = 0

    def set_function(self, func_=None, attributes=None):
        # setting the function for the main button
        if func_:
            self.buttons[0].function = func_
            self.buttons[0].attr = attributes

    def set_text(self, text):
        self.buttons[0].set_text(text)
        self.buttons[0].set_alignment("center")

    def resize(self, height, width):
        self.window_height = height
        self.window_width = width
        for i in range(len(self.buttons)):
            self.buttons[i].resize(height, width)

    def is_hovering(self, mouse_cx, mouse_cy):
        for i in range(len(self.buttons)):
            self.buttons[i].is_hovering(mouse_cx, mouse_cy)

    def add_pull_down_button(self, button):
        self.buttons.append(button)


# (outdated  -- DO NOT USE)
# creates a rectangular border object (will likely be used with my image editing toolkit
# class Border:
#     # variables that store where on the screen that a button is
#     vertices = 0
#     indices = np.array([1, 3, 2, 0, 1], dtype=np.uint32)
#     x1 = 0
#     x2 = 0
#     y1 = 0
#     y2 = 0
#
#     # (x1, y1) upper left corner
#     # (x2, y2) lower right corner
#     def __init__(self, x1, y1, x2, y2, height, width):
#         self.set_vertices(x1, y1, x2, y2, height, width)
#         self.x1 = x1
#         self.y1 = y1
#         self.x2 = x2
#         self.y2 = y2
#
#     # sets the vertice array used in drawing the border to the screen
#     def set_vertices(self, px1, py1, px2, py2, height, width):
#         xy1 = normalize.normalize_pixel(px1, py1, height, width)
#         xy2 = normalize.normalize_pixel(px2, py2, height, width)
#         self.vertices = [xy1[0][0], xy1[0][1], 1.0, 1.0, 1.0,
#                          xy2[0][0], xy1[0][1], 0.0, 0.0, 1.0,
#                          xy1[0][0], xy2[0][1], 0.0, 0.0, 1.0,
#                          xy2[0][0], xy2[0][1], 1.0, 1.0, 1.0]
#         self.vertices = np.array(self.vertices, dtype=np.float32)


# -------------------------------------------------------------------------------------
# Class: Character
# Purpose: Stores all relevant information about loading a character bitmap to
#          the screen
# Elements:
#    TextureID - holds the ID to grab the texture from memory
#    Size - holds the height and width of the bitmap
#    Bearing - holds information relevant to aligning characters correctly
#    Advance - holds the amount of between the current character and where the next one
#              should be placed
# --------------------------------------------------------------------------------------
class Character:
    TextureID = 0
    Size = glm.vec2(0, 0)
    Bearing = glm.vec2(0, 0)
    Advance = 0

    def __init__(self, TextureID, Size, Bearing, Advance):
        self.TextureID = TextureID
        self.Size = Size
        self.Bearing = Bearing
        self.Advance = Advance


# ------------------------------------------------------------------------------------------
# Class: Text
# Purpose: Allows the creation of text objects that can load a font (specified by the user),
#          reads in the first 128 characters of the font, and draws a string of text to
#          the screen
# Elements:
#    text_array - used for storing the first 128 characters of the font
#    indices - generic element for visualizing a character
# -------------------------------------------------------------------------------------------
class Text:
    text_array = []
    indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)
    height = 0
    width = 0
    txt_shader = 0

    def __init__(self, height, width, txt_shader):
        self.height = height
        self.width = width
        self.txt_shader = txt_shader

    # loading a font and reading in the first 128 characters (currently only supports Arial
    # because it is hardcoded in - only requires a slight change to fix this)
    def load_font(self):
        # loading font
        face = freetype.Face('C:/Windows/Fonts/Arial.ttf', 0)
        # setting font size
        face.set_pixel_sizes(0, 18)

        # loading first 128 characters of the Font into memory with relevant information
        # to display to the screen later
        for i in range(0, 128):
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            face.load_char(chr(i), freetype.FT_LOAD_RENDER)
            # print("letter: {}, i: {}".format(chr(i), i))
            # creating the texture binding and reading the bitmap in an OpenGL Friendly way
            texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture)
            glTexImage2D(GL_TEXTURE_2D,
                         0,
                         GL_RED,
                         face.glyph.bitmap.width,
                         face.glyph.bitmap.rows,
                         0,
                         GL_RED,
                         GL_UNSIGNED_BYTE,
                         face.glyph.bitmap.buffer)
            # Set the texture wrapping parameters
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            # Set texture filtering parameters
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

            # creating character and storing it in the text array full of the first
            # 128 characters of the font
            ch = Character(texture,
                           glm.vec2(face.glyph.bitmap.width, face.glyph.bitmap.rows),
                           glm.vec2(face.glyph.bitmap_left, face.glyph.bitmap_top),
                           face.glyph.advance.x)
            self.text_array.append(ch)

            glBindTexture(GL_TEXTURE_2D, 0)  # unbinding the texture
        face = 0  # not sure if this is right - documentation was bad

    # add scaling later
    # renders a string of text to the screen
    def render_text(self, text, x, y, VBO, EBO, color_choice=None):
        glUseProgram(self.txt_shader)
        glEnable(GL_BLEND)
        max_ = 0
        # alignment for top (has issues with aligning to bottom might need more code for this)
        # for i in range(len(text)):
        #    if self.text_array[ord(text[i])].Size.y > max_:
        max_ = self.text_array[65].Size.y
        # print("word: {}, max: {}".format(text, max_))
        y = self.height - y - max_  # + self.text_array[ord('A')].Size.y / 2

        scale = 1.0  # must be between 0 and 1 - changes the size of the text

        # default color is black
        color = [0, 0, 0]
        if color_choice == 'r':
            color = [1, 0, 0]
        elif color_choice == 'y':
            color = [1, 1, 0]

        vertices = [0, 0, color[0], color[1], color[2], 0.0, 0.0,
                    0, 0, color[0], color[1], color[2], 1.0, 0.0,
                    0, 0, color[0], color[1], color[2], 1.0, 1.0,
                    0, 0, color[0], color[1], color[2], 0.0, 1.0]

        vertices = np.array(vertices, dtype=np.float32)
        # rendering the given string 'text' to the screen
        for i in range(len(text)):
            # ord: char -> int
            # chr: int -> char
            letter = self.text_array[ord(text[i])]
            # glyph 1
            w = letter.Size.x * scale
            h = letter.Size.y * scale

            xpos = (x + letter.Bearing.x) * scale
            ypos = (y - letter.Size.y + letter.Bearing.y) * scale
            # vertices = [xpos, ypos,         1.0, 0.0, 0.0,  0.0, 0.0,
            #             xpos + w, ypos,     1.0, 0.0, 0.0,  1.0, 0.0,
            #             xpos + w, ypos + h, 1.0, 0.0, 0.0,  1.0, 1.0,
            #             xpos, ypos + h,     1.0, 0.0, 0.0,  0.0, 1.0]
            #
            # vertices = np.array(vertices, dtype=np.float32)
            # setting the vertices manually (this is probably bad?)
            vertices[0] = xpos
            vertices[1] = ypos
            vertices[7] = xpos + w
            vertices[8] = ypos
            vertices[14] = xpos + w
            vertices[15] = ypos + h
            vertices[21] = xpos
            vertices[22] = ypos + h

            # binding texture
            glBindTexture(GL_TEXTURE_2D, letter.TextureID)

            # binding buffer and updating buffer array with new information from vertices
            glBindBuffer(GL_ARRAY_BUFFER, VBO)
            glBufferSubData(GL_ARRAY_BUFFER, 0, vertices.nbytes, vertices)

            # binding buffer and updating buffer array with information from vertices
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
            glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, self.indices.nbytes, self.indices)

            # Vertices Element
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, vertices.itemsize * 7, ctypes.c_void_p(0))

            # Color Element
            glEnableVertexAttribArray(1)
            glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, vertices.itemsize * 7, ctypes.c_void_p(8))

            # Texture Element
            glEnableVertexAttribArray(2)
            glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, vertices.itemsize * 7, ctypes.c_void_p(20))

            glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
            x = x + letter.Advance / 64
        glDisable(GL_BLEND)

    # set/change the height and width (for use when the window changes sizes)
    def set_hw(self, height, width):
        self.height = height
        self.width = width


class InfoBanner:
    text = 0
    params = 0
    rt = 0  # rendered text
    x1 = 0
    y1 = 0
    text_shader = 0

    def __init__(self, x1, y1, size_x, size_y, height, width, text, rt, txt_shader):
        self.text = text
        self.rt = rt
        self.x1 = x1
        self.y1 = y1
        self.text_shader = txt_shader
        print("initializing info banner")

    def update_info(self, params):
        self.params = params

    def draw(self, VBO, EBO):
        yoffset = 0
        for i in range(len(self.text)):
            if self.text[i]:
                self.rt.render_text(self.text[i] + self.params[i], self.x1, self.y1 + yoffset, VBO, EBO, 'y')
                yoffset = yoffset + self.rt.text_array[ord(self.text[i][0])].Bearing.y + self.rt.text_array[65].Size.y

    def check_unclick(self, mouse_cx, mouse_cy):
        pass

    def is_hovering(self, mouse_cx, mouse_cy):
        pass


class SlideBar:
    # informational banner variables
    slider_value = 0
    value_label = 0  # will be an informational banner that displays what value the banner is at

    thumb = 0  # will hold the object that slides (not sure if will be an actual object)
    thumb_translate = glm.vec3(0, 0, 0)
    # width and height of the slider base
    sliderbase_height = 0
    sliderbase_width = 0

    window_height = 0
    # top/bottom coordinates of the thumb slider
    y1 = 0
    y2 = 0
    x1 = 0
    x2 = 0

    # current location of the thumb slider
    currx1 = 0
    currx2 = 0

    # upper left and lower right corner of the slider (in pixel coords)
    sx1 = 0
    sy1 = 0
    sx2 = 0
    sy2 = 0

    # used for drawing
    rt = 0  # rendered text
    indices = np.array([0, 1, 2, 2, 3, 1], dtype=np.uint32)
    thumb_vertices = 0  # corner vertices for drawing the thumb
    base_vertices = 0  # corner vertices for drawing the slider base
    slider_shader = 0  # will store the reference to the shader used for drawing

    # initializing the object
    def __init__(self, x1, y1, s_height, s_width, window_height, window_width, rt, slider_shader):
        # setting information about the slider base
        self.sx1 = x1
        self.sy1 = y1
        self.sx2 = x1 + s_width
        self.sy2 = y1 + s_height
        self.sliderbase_height = s_height
        self.sliderbase_width = s_width

        # thumb will be 75% the height and 2.5% the width of the slider base
        self.y1 = y1 + (s_height / 8)
        self.y2 = y1 + (s_height * 7 / 8)
        self.x1 = x1 + s_width * 0.025
        self.x2 = x1 + s_width * 0.05
        self.currx1 = self.x1
        self.currx2 = self.x2
        self.set_vertices(window_height, window_width)

        self.window_height = window_height
        # setting the shader used for drawing
        self.rt = rt
        self.slider_shader = slider_shader

    def set_vertices(self, window_height, window_width):
        # setting vertices for the slider base
        x1, y1 = normalize.normalize_pixel(self.sx1, self.sy1, window_height, window_width)
        x2, y2 = normalize.normalize_pixel(self.sx2, self.sy2,
                                           window_height, window_width)
        self.base_vertices = [x1, y1, 0.6, 0.6, 0.6,
                              x2, y1, 0.6, 0.6, 0.6,
                              x1, y2, 1.0, 1.0, 1.0,
                              x2, y2, 1.0, 1.0, 1.0]
        self.base_vertices = np.array(self.base_vertices, dtype=np.float32)

        # setting vertices for the thumb (slider thing)
        x1, y1 = normalize.normalize_pixel(self.x1,
                                           self.y1,
                                           window_height, window_width)
        x2, y2 = normalize.normalize_pixel(self.x2,
                                           self.y2,
                                           window_height, window_width)
        self.thumb_vertices = [x1, y1, 0.0, 0.0, 0.0,
                               x2, y1, 0.0, 0.0, 0.0,
                               x1, y2, 0.0, 0.0, 0.0,
                               x2, y2, 0.0, 0.0, 0.0]
        self.thumb_vertices = np.array(self.thumb_vertices, dtype=np.float32)

    def check_click(self, mouse_cx, mouse_cy):
        if self.currx1 <= mouse_cx <= self.currx2 and self.y1 <= mouse_cy <= self.y2:
            if self.function:
                # if button has function attributes, call the function with those attributes
                if self.attr:
                    self.function(self.attr)

                # if a function has no attributes, just call the function
                else:
                    self.function()
                return 1

    def check_unclick(self, mouse_cx, mouse_cy):
        pass

    # sets function that is called in check_click()
    def set_function(self, func_=None, attributes=None):
        if func_:
            self.function = func_
            self.attr = attributes

    # draws the object to the screen
    def draw(self, VBO, EBO):
        # drawing will consist of:
        #   drawing a rectangle as the slider base
        #   drawing the thumb
        #   drawing text that shows the slider value
        #   a shader component that draws the track in a white color and to the left of the
        #       thumb will be drawn green

        # loading shader for drawing
        glUseProgram(self.slider_shader)

        # setting the model matrix and sending to the shader for drawing
        model = glm.mat4(1)
        model_loc = glGetUniformLocation(self.slider_shader, "model")
        glUniformMatrix4fv(model_loc, 1, GL_FALSE, glm.value_ptr(model))

        # sending coordinate information about the thumb to the shader so that it
        # can draw the track green to the left of it and gray to the right of it
        coordx_loc = glGetUniformLocation(self.slider_shader, "coordx")
        # print("length: {}, currx2: {}, x1: {}, sl_width: {}".format(self.currx2 - self.sliderbase_width * .025,
        #                                                             self.currx2, self.x1,
        #                                                             self.sx1 + self.sliderbase_width))
        coord = glm.vec4(self.currx2 - self.sliderbase_width * .025, self.currx2, self.x1,
                         self.sx1 + self.sliderbase_width * 0.975)
        glUniform4fv(coordx_loc, 1, glm.value_ptr(coord))

        # sending coordinate information about the top and bottom of the thumb
        # to the shader so that it can draw the track
        coordy_loc = glGetUniformLocation(self.slider_shader, "coordy")
        # print("y1: {}".format(self.window_height - self.y1))
        coord = glm.vec2(self.window_height - self.y1, self.window_height - self.y2)
        glUniform2fv(coordy_loc, 1, glm.value_ptr(coord))

        # DRAWING SLIDER BASE -----
        glBindBuffer(GL_ARRAY_BUFFER, VBO)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.base_vertices)

        # Element Buffer Object
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
        glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, self.indices)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(0))

        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(8))

        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)

        model = glm.translate(model, self.thumb_translate)
        glUniformMatrix4fv(model_loc, 1, GL_FALSE, glm.value_ptr(model))

        # DRAWING THUMB ------
        glBindBuffer(GL_ARRAY_BUFFER, VBO)
        glBufferSubData(GL_ARRAY_BUFFER, 0, self.thumb_vertices)

        # Element Buffer Object
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
        glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, self.indices)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(0))

        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(8))

        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)

        # calculating slider value based off starting pixel and where the left edge of the thumb is
        self.slider_value = self.currx2 - self.x2
        # DRAWING SLIDER VALUE
        self.rt.render_text("val: " + str(int(self.slider_value)), self.sx1 + self.sliderbase_width,
                            self.y1 + ((self.y2 - self.y1 - self.rt.text_array[65].Size.y) / 2), VBO, EBO, 'y')

    def resize(self, height, width):
        self.window_height = height
        self.set_vertices(height, width)

    def is_hovering(self, mouse_cx, mouse_cy):
        pass
