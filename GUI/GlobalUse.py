from enum import Enum
from pygame import *
from win32api import GetSystemMetrics
TRANSPARENT = (0, 0, 0, 0)
font.init()
ARIAL_DEFAULT_FONT = font.Font(font.match_font('arial'), 14)
DEFAULT_FONT = 'comicsansms'


def place_center(rect1, rect2):
    if isinstance(rect2, Surface):
        return (rect1.x + rect1.width // 2 - rect2.get_width() // 2,
                rect1.y + rect1.height // 2 - rect2.get_height() // 2)

    if isinstance(rect2, tuple):
        if len(rect2) == 4:
            rect2 = Rect(*rect2)
        elif len(rect2) == 2:
            return (rect1.x + rect1.width // 2 - rect2[0] // 2,
                    rect1.y + rect1.height // 2 - rect2[1] // 2)

    if isinstance(rect2, Rect):
        return (rect1.rect.x + rect1.rect.width // 2 - rect2.width // 2,
                rect1.y + rect1.height // 2 - rect2.height // 2)


class Resolution(Enum):
    width = 1728
    height = 972


class Justification(Enum):
    left_justified = 0
    horizontally_centered = 1
    right_justified = 2


class PlaceType(Enum):
    center = 1
    top_left = 2
    top_right = 3
    bottom_left = 4
    bottom_right = 5


# class TextStyle:
#     def __init__(self, text, color, size, font='comicsansms', justification=Justification.horizontally_centered):
#         self.justification = justification
#         self.size = size
#         self.color = color
#         self.font = font
#         self.text = text


class MouseButtons:
    left = 1
    wheel = 2
    right = 3


class Voice(Enum):
    mute = 1
    unmute = 2


class DisplayMods:
    BASE_WIDTH = 1728
    BASE_HEIGHT = 972

    current_width = BASE_WIDTH
    current_height = BASE_HEIGHT

    MONITOR_WIDTH = GetSystemMetrics(0)
    MONITOR_HEIGHT = GetSystemMetrics(1)
    # MONITOR_WIDTH = 1680
    # MONITOR_HEIGHT = 1080
    MONITOR_RESOLUTION = (MONITOR_WIDTH, MONITOR_HEIGHT)

    @classmethod
    def get_resolution(cls):
        return cls.current_width, cls.current_height

    @classmethod
    def FullScreen(cls):
        return display.set_mode(cls.MONITOR_RESOLUTION, FULLSCREEN)

    @classmethod
    def FullScreenAccelerated(cls):
        return display.set_mode(cls.MONITOR_RESOLUTION, HWSURFACE)

    @classmethod
    def WindowedFullScreen(cls):
        return display.set_mode(cls.MONITOR_RESOLUTION, NOFRAME, display=0)

    @classmethod
    def Windowed(cls, size):
        cls.current_width, cls.current_height = size
        return display.set_mode((cls.current_width, cls.current_height))

    @classmethod
    def Resizable(cls, size):
        cls.current_width, cls.current_height = size
        return display.set_mode((cls.current_width, cls.current_height), RESIZABLE)


def pixels(meter):
    return meter


def meters(pixel):
    ratio = DisplayMods.BASE_WIDTH / DisplayMods.current_width
    return round(pixel * ratio)


def meters_multi(*pixel):
    return tuple(meters(i) for i in pixel)


def closest_number_divisible(n, m):
    # Find the quotient
    q = int(n / m)

    # 1st possible closest number
    n1 = m * q

    # 2nd possible closest number
    if ((n * m) > 0):
        n2 = (m * (q + 1))
    else:
        n2 = (m * (q - 1))
    # if true, then n1 is the required closest number
    if (abs(n - n1) < abs(n - n2)):
        return n1

        # else n2 is the required closest number
    return n2


class TextRectException(Exception):
    def __init__(self, message=None):
            self.message = message

    def __str__(self):
        return self.message


def sub(u, v):
    if isinstance(v, int):
        return [u[i] - v for i in range(len(u))]
    return [u[i] - v[i] for i in range(len(u))]


def add(u, v):
    if isinstance(v, int):
        return [u[i] + v for i in range(len(u))]
    return [u[i] + v[i] for i in range(len(u))]


def mul(u, v):
    if isinstance(v, int):
        return [u[i] * v for i in range(len(u))]
    return [u[i] * v[i] for i in range(len(u))]


def div(u, v):
    if isinstance(v, int):
        return [u[i] // v for i in range(len(u))]
    return [u[i] // v[i] for i in range(len(u))]


def fit_text_to_rect(string, text_font, text_color, justification, rect):
    """Returns a surface containing the passed text string, reformatted
    to fit within the given rect, word-wrapping as necessary. The text
    will be anti-aliased.

    Parameters
    ----------
    string - the text you wish to render. \n begins a new line.
    font - a Font object
    rect - a rect style giving the size of the surface requested.
    fontColour - a three-byte tuple of the rgb value of the
             text color. ex (0, 0, 0) = BLACK
    BGColour - a three-byte tuple of the rgb value of the surface.
    justification - 0 (default) left-justified
                1 horizontally centered
                2 right-justified

    Returns
    -------
    Success - a surface object with the text rendered onto it.
    Failure - raises a TextRectException if the text won't fit onto the surface.
    """
    justification = justification

    finalLines = []
    requestedLines = string.splitlines()
    # Create a series of lines that will fit on the provided
    # rectangle.
    for requestedLine in requestedLines:
        if text_font.size(requestedLine)[0] > rect.width:
            words = requestedLine.split(' ')
            # if any of our words are too long to fit, return.
            for word in words:
                if text_font.size(word)[0] >= rect.width:
                    raise TextRectException("The word " + word + " is too long to fit in the rect passed.")
            # Start a new line
            accumulatedLine = ""
            for word in words:
                testLine = accumulatedLine + word + " "
                # Build the line while the words fit.
                if text_font.size(testLine)[0] < rect.width:
                    accumulatedLine = testLine
                else:
                    finalLines.append(accumulatedLine)
                    accumulatedLine = word + " "
            finalLines.append(accumulatedLine)
        else:
            finalLines.append(requestedLine)

    # Let's try to write the text out on the surface.
    surface = Surface(rect.size, SRCALPHA)
    accumulatedHeight = 0
    for line in finalLines:
        if accumulatedHeight + text_font.size(line)[1] >= rect.height:
            raise TextRectException("Once word-wrapped, the text string was too tall to fit in the rect.")
        if line != "":
            temp_surface = text_font.render(line, 1, text_color)
        else:
            continue
        if justification == 0 or justification == Justification.left_justified:
            surface.blit(temp_surface, (0, accumulatedHeight))
        elif justification == 1 or justification == Justification.horizontally_centered :
            surface.blit(temp_surface, ((rect.width - temp_surface.get_width()) / 2, accumulatedHeight))
        elif justification == 2 or justification == Justification.right_justified:
            surface.blit(temp_surface, (rect.width - temp_surface.get_width(), accumulatedHeight))
        else:
            raise TextRectException("Invalid justification argument: " + str(justification))
        accumulatedHeight += text_font.size(line)[1]
    return surface.subsurface((0, 0, surface.get_width(), accumulatedHeight)).convert_alpha()


def wrap_too_long_words(string: str, font_object: font, rect):

    requested_lines = string.splitlines()
    # Create a series of lines that will fit on the provided
    # rectangle.
    final_line_list = []
    for requestedLine in requested_lines:
        if font_object.size(requestedLine)[0] > rect.width:
            # the line is too long
            words = requestedLine.split(' ')
            new_words = []
            # if any of our words are too long to fit, fit as much as you can,
            # and move the one you can't to the next line.
            for word in words:
                if font_object.size(word)[0] >= rect.width:
                    # the word is too long to fit in the rect passed:
                    maximum_line = ''
                    for index in range(1, len(word) + 1):
                        if font_object.size(word[:index])[0] <= rect.width:
                            maximum_line += word[index-1]
                        else:
                            # now maximum line is the biggest line you can make
                            final_line_list.append(maximum_line)
                            final_line_list.append(word[index - 1:])
                            break
                else:
                    # the word can be fitten in the rect passes
                    try:
                        if font_object.size(final_line_list[-1] + ' ' + word)[0] <= rect.width:
                            # you can add the word to the last line
                            final_line_list[-1] += ' ' + word
                        else:
                            final_line_list.append(word)
                    except IndexError:
                        final_line_list.append(word)

        else:
            final_line_list.append(requestedLine)

    return '\n'.join(final_line_list)


def fit_text_to_rect_if_possible(string, text_font, text_color, justification, rect):
    string = wrap_too_long_words(string, text_font, rect)
    while True:
        try:
            return fit_text_to_rect(string, text_font, text_color, justification, rect), string
        except Exception as e:
            if 'tall' in (str(e)):
                raise e
            string = wrap_too_long_words(string, text_font, rect)


if __name__ == '__main__':
    os.system('python "main debug.py"')  # running the script as main make problems
