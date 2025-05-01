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


def create_transparent_square(image, size_ratio=0.9, opacity=0.3):
    """Vytvoří průhledný čtverec na obrázku"""
    width, height = image.size
    square_size = int(min(width, height) * size_ratio)

    alpha = int(255 * opacity)
    square = Image.new('RGBA', (square_size, square_size), (255, 255, 255, alpha))

    pos = ((width - square_size) // 2, (height - square_size) // 2)
    image.paste(square, pos, square)

    return pos[0], pos[1], square_size


def load_montserrat_fonts():
    """Načte fonty Montserrat s fallback na výchozí font"""
    try:
        return {
            'day': ImageFont.truetype(MONT_FONT_PATHS['bold'], 72),
            'date': ImageFont.truetype(MONT_FONT_PATHS['medium'], 48),
            'name': ImageFont.truetype(MONT_FONT_PATHS['bold'], 84),
            'footer': ImageFont.truetype(MONT_FONT_PATHS['regular'], 36),
        }
    except Exception as e:
        print(f"Chyba při načítání fontu Montserrat: {e}. Používám výchozí fonty.")
        default_font = ImageFont.load_default()
        return {k: default_font for k in ['day', 'date', 'name', 'footer']}
