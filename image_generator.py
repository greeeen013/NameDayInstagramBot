from PIL import Image, ImageDraw, ImageFont
import random
import os
import textwrap
from datetime import datetime
from api_handler import get_today_data

# Cesty k fontům - upravte podle potřeby
MONT_FONT_PATHS = {
    'regular': 'Montserrat-Regular.ttf',
    'bold': 'Montserrat-Bold.ttf',
    'medium': 'Montserrat-Medium.ttf'
}


def generate_gradient_background(width, height):
    """Generuje diagonální gradientní pozadí z náhodných barev"""
    image = Image.new('RGB', (width, height))

    # Náhodné barvy pro gradient
    color1 = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    color2 = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    # Diagonální gradient
    for y in range(height):
        for x in range(width):
            ratio = (x + y) / (width + height)
            r = int(color1[0] + (color2[0] - color1[0]) * ratio)
            g = int(color1[1] + (color2[1] - color1[1]) * ratio)
            b = int(color1[2] + (color2[2] - color1[2]) * ratio)
            image.putpixel((x, y), (r, g, b))

    return image.convert('RGBA')


