"""Module with useful functions to image processing"""

import colorsys
from xtermcolor import colorize

CHARS_LIGHT = [' ', ' ', '.', ':', '!', '+', '*', 'e', '$', '@', '8']
CHARS_COLOR = ['.', '*', 'e', 's', '◍']
CHARS_FILLED = ['░', '▒', '▓', '█']
CHARS_DETAILED = [' ', '.', '·', ':', ';', '\'', '`', '"', '^', ',', '-', '~', '+', '<', '>', 'i', '!', 'I', '/', '\\', '|', '(', ')', '1', '{', '}', '[', ']', 'r', 'c', 'v', '?', 'L', 'T', 'J', '7', 'F', 'z', 's', 'S', 'Z', 'Y', 'x', 'X', 'V', 'K', 'n', 'N', 'k', 'K', 'H', 'A', 'G', 'E', '8', '&', '%', '@', '#']

DENSITY = [CHARS_LIGHT, CHARS_COLOR, CHARS_FILLED, CHARS_DETAILED]

def brightness_to_ascii(i, density=0):
    """
    Get an appropriate char of brightness from a rgb color
    """
    chars_collection = DENSITY[density]
    size = len(chars_collection) - 1
    index = int(size * i / 255)
    return chars_collection[index]

def colorize_char(char, ansi_color):
    """
    Get an appropriate char of brightness from a rgb color
    """
    str_colorized = colorize(char, ansi=ansi_color)
    return str_colorized

def pixel_to_ascii(pixel, colored=True, density=0):
    """
    Convert a pixel to char
    """
    bgr = tuple(float(x) for x in pixel[:3])
    rgb = tuple(reversed(bgr))
    char = ''
    if colored:
        bright = rgb_to_brightness(*rgb)
        rgb = increase_saturation(*rgb)
        char = brightness_to_ascii(bright, density)
        ansi_color = rgb_to_ansi(*rgb)
        char = colorize(char*2, ansi=ansi_color)
    else:
        bright = rgb_to_brightness(*rgb, grayscale=True)
        char = brightness_to_ascii(bright, density)
        char = char*2
    return char

def increase_saturation(r, g, b):
    """
    Increase the saturation from rgb and return the new value as rgb tuple
    """
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    s = min(s+0.3, 1.0)
    v = min(v+0.1, 1.0)  # Slightly increase brightness too
    
    r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v)
    return r2*255, g2*255, b2*255

def rgb_to_brightness(r, g, b, grayscale=False):
    """
    Calc a brightness factor according to rgb color
    """
    if grayscale:
        return 0.2126*r + 0.7152*g + 0.0722*b
    else:
        return 0.267*r + 0.642*g + 0.091*b

def rgb_to_ansi(r, g, b):
    """
    Convert an rgb color to ansi color
    """
    (r, g, b) = int(r), int(g), int(b)
    if r == g & g == b:
        if r < 8:
            return int(16)
        if r > 248:
            return int(230)
        return int(round(((r - 8) / 247) * 24) + 232)

    to_ansi_range = lambda a: int(round(a / 51.0))
    r_in_range = to_ansi_range(r)
    g_in_range = to_ansi_range(g)
    b_in_range = to_ansi_range(b)
    ansi = 16 + (36 * r_in_range) + (6 * g_in_range) + b_in_range
    return int(ansi)
