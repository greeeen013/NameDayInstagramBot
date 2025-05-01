from PIL import Image, ImageDraw, ImageFont
import random
import os
import textwrap
from datetime import datetime
from api_handler import get_today_data
from name_info import get_name_info

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
            'info': ImageFont.truetype(MONT_FONT_PATHS['regular'], 32)  # Přidán font pro informace
        }
    except Exception as e:
        print(f"Chyba při načítání fontu Montserrat: {e}. Používám výchozí fonty.")
        default_font = ImageFont.load_default()
        return {k: default_font for k in ['day', 'date', 'name', 'footer', 'info']}


def draw_wrapped_text(draw, text, font, image_width, y_pos, square_size):
    """Zalamuje dlouhý text a vykreslí ho na více řádků"""
    max_width = square_size * 0.9
    avg_char_width = font.getlength("x")
    max_chars = int(max_width / avg_char_width)

    if len(text) > max_chars:
        wrapped_text = textwrap.fill(text, width=max_chars)
        lines = wrapped_text.split('\n')
    else:
        lines = [text]

    line_height = font.getbbox(text)[3] - font.getbbox(text)[1]
    for line in lines:
        line_width = font.getlength(line)
        line_x = (image_width - line_width) // 2
        draw.text((line_x, y_pos), line, fill="black", font=font)
        y_pos += line_height + 10

    return y_pos


def draw_texts(image, data, square_area):
    """Vykreslí texty na obrázek s použitím Montserrat fontu"""
    draw = ImageDraw.Draw(image)
    fonts = load_montserrat_fonts()
    square_x, square_y, square_size = square_area

    # 1. "Dnes je čtvrtek" - úplně nahoře
    day_text = f"Dnes je {data['dayInWeek']}"
    day_y = square_y + 20
    text_width = fonts['day'].getlength(day_text)
    draw.text(((image.width - text_width) // 2, day_y), day_text, fill="black", font=fonts['day'])

    # 2. Datum - pod prvním textem
    date_text = f"{data['dayNumber']}. {data['month']['genitive']} {data['year']}"
    date_y = day_y + fonts['day'].getbbox(day_text)[3] + 20
    text_width = fonts['date'].getlength(date_text)
    draw.text(((image.width - text_width) // 2, date_y), date_text, fill="black", font=fonts['date'])

    # 3. Název svátku - velká mezera a pak velký text
    name_text = "Zikmund"

    name_y = date_y + fonts['date'].getbbox(date_text)[3] + 250
    name_y = draw_wrapped_text(draw, name_text, fonts['name'], image.width, name_y, square_size)

    # 4. Informace o jméně (pokud jsou dostupné)
    name_info = get_name_info(name_text)
    if name_info:
        # Vytvoříme layout s velkými čísly a popisky pod nimi
        info_y = name_y + 60

        # Nastavení fontů
        number_font = ImageFont.truetype(MONT_FONT_PATHS['bold'], 48)
        label_font = ImageFont.truetype(MONT_FONT_PATHS['regular'], 32)

        # Rozložení do 3 sloupců
        col_width = square_size // 3
        center_x = image.width // 2
        start_x = center_x - col_width

        # 1. sloupec - pořadí
        rank_text = f"{name_info['rank']}."
        rank_width = number_font.getlength(rank_text)
        draw.text((start_x + (col_width - rank_width) // 2, info_y), rank_text, fill="black", font=number_font)

        label_text = "nejčastější"
        label_width = label_font.getlength(label_text)
        draw.text((start_x + (col_width - label_width) // 2, info_y + 60), label_text, fill="black", font=label_font)

        # 2. sloupec - počet nositelů
        count_text = str(name_info['count'])
        count_width = number_font.getlength(count_text)
        draw.text((start_x + col_width + (col_width - count_width) // 2, info_y), count_text, fill="black",
                  font=number_font)

        label_text = "nositelů"
        label_width = label_font.getlength(label_text)
        draw.text((start_x + col_width + (col_width - label_width) // 2, info_y + 60), label_text, fill="black",
                  font=label_font)

        # 3. sloupec - průměrný věk
        age_text = str(name_info['avg_age'])
        age_width = number_font.getlength(age_text)
        draw.text((start_x + 2 * col_width + (col_width - age_width) // 2, info_y), age_text, fill="black",
                  font=number_font)

        label_text = "průměrný věk"
        label_width = label_font.getlength(label_text)
        draw.text((start_x + 2 * col_width + (col_width - label_width) // 2, info_y + 60), label_text, fill="black",
                  font=label_font)
    else:
        print(f"ℹ️ Pro jméno {name_text} nebyly nalezeny žádné informace")

    # 5. "@test" - úplně dole
    footer_text = "@test"
    footer_y = square_y + square_size - 100
    text_width = fonts['footer'].getlength(footer_text)
    draw.text(((image.width - text_width) // 2, footer_y), footer_text, fill="black", font=fonts['footer'])


def generate_image():
    """Hlavní funkce pro generování obrázku"""
    width, height = 1080, 1080
    data = get_today_data()

    image = generate_gradient_background(width, height)
    square_area = create_transparent_square(image, opacity=0.3)
    draw_texts(image, data, square_area)

    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{today}.png"
    image.save(filename, "PNG")

    print(f"Obrázek uložen jako {filename}")
    return filename


if __name__ == "__main__":
    generate_image()