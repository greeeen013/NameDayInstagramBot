import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps
import os

from api_handler import get_nasa_apod
# import funkcí pro získání dnešních jmen a informací o jménu
from name_info import get_todays_names, get_name_info

from pathlib import Path
import requests
from io import BytesIO

# Zjistí cestu k adresáři, kde je tento skript
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Cesty k fontům Montserrat
MONT_FONT_PATHS = {
    'regular': os.path.join(BASE_DIR, 'Montserrat-Regular.ttf'),
    'bold':    os.path.join(BASE_DIR, 'Montserrat-Bold.ttf'),
    'medium':  os.path.join(BASE_DIR, 'Montserrat-Medium.ttf'),
    'italic':  os.path.join(BASE_DIR, 'Montserrat-Italic.ttf')
}

#----------------------------------------
# Generuje diagonální gradientní pozadí
#----------------------------------------
def generate_gradient_background(width, height):
    image = Image.new('RGB', (width, height))
    color1 = tuple(random.randint(0, 255) for _ in range(3))
    color2 = tuple(random.randint(0, 255) for _ in range(3))
    for y in range(height):
        for x in range(width):
            ratio = (x + y) / (width + height)
            r = int(color1[0] + (color2[0] - color1[0]) * ratio)
            g = int(color1[1] + (color2[1] - color1[1]) * ratio)
            b = int(color1[2] + (color2[2] - color1[2]) * ratio)
            image.putpixel((x, y), (r, g, b))
    return image.convert('RGBA')

#----------------------------------------
# Vytvoří průhledný čtverec (overlay) uprostřed
# padding 0.1 znamená box 90% velikosti
#----------------------------------------
def create_overlay_square(image, padding=0.1, opacity=0.25):
    w, h = image.size
    size = int(min(w, h) * (1 - padding))
    overlay = Image.new('RGBA', (size, size), (255, 255, 255, int(255 * opacity)))
    x = (w - size) // 2
    y = (h - size) // 2
    image.paste(overlay, (x, y), overlay)
    return x, y, size

#----------------------------------------
# Načte fonty Montserrat s fallback
#----------------------------------------
def load_fonts():
    try:
        return {
            'weekday_bold': ImageFont.truetype(MONT_FONT_PATHS['bold'],   80),
            'date':         ImageFont.truetype(MONT_FONT_PATHS['medium'], 60),
            'name':         ImageFont.truetype(MONT_FONT_PATHS['bold'],   150),
            'name_smaller': ImageFont.truetype(MONT_FONT_PATHS['bold'],     120),
            'stats_num':    ImageFont.truetype(MONT_FONT_PATHS['bold'],    80),
            'stats_lbl':    ImageFont.truetype(MONT_FONT_PATHS['regular'], 45),
            'origin':       ImageFont.truetype(MONT_FONT_PATHS['italic'],  48),
            'footer':       ImageFont.truetype(MONT_FONT_PATHS['regular'], 42)
        }
    except IOError as e:
        print(f"⚠️ Nepodařilo se načíst fonty, používám výchozí. chyba: {e}")
        default = ImageFont.load_default()
        return {k: default for k in ['weekday_bold','date','name','stats_num','stats_lbl','origin','footer']}

#----------------------------------------
# Pomocná funkce pro centrované vykreslení textu
#----------------------------------------
def draw_centered(draw, text, font, x_center, y):
    if not isinstance(text, str):
        print(f"⚠️ Neplatný text: {text} (typ: {type(text)}) – převádím na string")
        text = str(text) if text is not None else ""
    width = font.getlength(text)
    draw.text((x_center - width/2, y), text, font=font, fill='black')

#----------------------------------------
# Vykreslí texty: den, datum, jméno, statistiky, původ, footer
#----------------------------------------
def draw_texts(image, name, info=None):
    draw = ImageDraw.Draw(image)
    fonts = load_fonts()
    w, h = image.size
    x0, y0, sq = create_overlay_square(image)

    # Dny a měsíce
    weekdays = ['Pondělí','Úterý','Středa','Čtvrtek','Pátek','Sobota','Neděle']
    months = {
        1:'ledna', 2:'února', 3:'března', 4:'dubna', 5:'května', 6:'června',
        7:'července', 8:'srpna', 9:'září', 10:'října', 11:'listopadu', 12:'prosince'
    }

    # Dnešní den a datum
    today = datetime.now()
    day_name = weekdays[today.weekday()]
    date_txt = f"{today.day}. {months[today.month]}"

    # 📏 Výška řádku – overlay rozdělíme do 8 zón
    line_height = sq // 8
    center_x = w // 2

    # 1) Den v týdnu
    y_weekday = y0 + line_height * 0 + 20
    draw_centered(draw, day_name, fonts['weekday_bold'], center_x, y_weekday)

    # 2) Datum
    y_date = y0 + line_height * 1
    draw_centered(draw, date_txt, fonts['date'], center_x, y_date)

    y_name = y0 + line_height * 2 + 60

    # ✏️ Výběr fontu podle délky jména
    font_for_name = fonts['name_smaller'] if len(name) >= 12 else fonts['name']

    if info is None:
        # 3) Svátek víc uprostřed
        draw_centered(draw, name, font_for_name, center_x, h // 2)
    else:
        # 3) Jméno
        draw_centered(draw, name, font_for_name, center_x, y_name)

        # 4) Statistiky (hodnoty + popisky)
        stats_y = y0 + line_height * 4 + 80
        col_w = sq / 3
        base_x = center_x - sq / 2
        stats_vals = [info.get('rank'), info.get('count'), info.get('avg_age')]
        stats_lbls = ['nejčastější', 'nositelů', 'ø věk']
        for i, (val, lbl) in enumerate(zip(stats_vals, stats_lbls)):
            x = base_x + col_w * i + col_w / 2
            txt_val = f"{val}." if i == 0 else str(val)
            draw_centered(draw, txt_val, fonts['stats_num'], x, stats_y)
            draw_centered(draw, lbl, fonts['stats_lbl'], x, stats_y + 80)

        # 5) Původ jména
        y_orig = y0 + line_height * 6 + 10
        origin_txt = f"původ: {info.get('origin', '–')}"
        draw_centered(draw, origin_txt, fonts['origin'], center_x, y_orig)



    # 6) Footer
    y_footer = y0 + sq - 50
    draw_centered(draw, '@svatekazdyden', fonts['footer'], center_x, y_footer)

def generate_nasa_image():
    """
    Stáhne NASA APOD obrázek, ořízne jej a přidá text. Vrací (path, explanation) nebo (None, None).
    """
    output_dir = Path(BASE_DIR) / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    apod_data = get_nasa_apod()
    if not apod_data:
        return None, None

    url = apod_data["hdurl"]
    explanation = apod_data["explanation"]

    try:
        res = requests.get(url)
        res.raise_for_status()
        img = Image.open(BytesIO(res.content))
    except Exception as e:
        print(f"❌ [image_generator] Chyba při stahování APOD obrázku: {e}")
        return None, None

    img = img.convert("RGB")
    img_square = ImageOps.fit(img, (1080, 1080), Image.LANCZOS, centering=(0.5, 0.5))

    filename = f"{datetime.now().strftime('%Y-%m-%d')}_NASA.png"
    filepath = str(output_dir / filename)  # Převést na string
    img_square.save(filepath)

    return filepath, explanation

#----------------------------------------
# Generování obrázku pro jedno jméno
#----------------------------------------
def generate_image_for(name, info=None):
    from pathlib import Path
    # vytvoří output adresář pokud neexistuje
    output_dir = Path(BASE_DIR) / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    img = generate_gradient_background(1080, 1080)
    draw_texts(img, name, info)
    filename = f"{datetime.now().strftime('%Y-%m-%d')}_{name}.png"

    # Vytvoření cesty k souboru
    filepath = os.path.join(output_dir, filename)

    print("✅ [image_generator] Soubor byl uložen do: "+os.path.abspath(filepath))
    img.save(filepath)
    return filepath

#----------------------------------------
# Hlavní blok: načtení jmen a generování obrázků
#----------------------------------------
if __name__ == '__main__':
    print("🍀 Získávám dnešní sváteční jména...")
    names = get_todays_names()
    if not names:
        print("ℹ️ Dnes žádné sváteční jméno.")
    for name in names:
        print(f"🔄 Generuji obrázek pro: {name}")
        info = get_name_info(name)
        print(f"   ✅ Počet: {info['count']}, pořadí: {info['rank']}, průměrný věk: {info['avg_age']}, původ: {info.get('origin','–')}")
        out = generate_image_for(name, info)
        print(f"🌟 Obrázek uložen: {out}\n")