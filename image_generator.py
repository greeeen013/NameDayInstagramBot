import random
import textwrap
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# import funkcí pro získání dnešních jmen a informací o jménu
from name_info import get_todays_names, get_name_info

# Cesty k fontům Montserrat
MONT_FONT_PATHS = {
    'regular': 'Montserrat-Regular.ttf',
    'bold':    'Montserrat-Bold.ttf',
    'medium':  'Montserrat-Medium.ttf',
    'italic':  'Montserrat-Italic.ttf'
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
            'stats_num':    ImageFont.truetype(MONT_FONT_PATHS['bold'],    80),
            'stats_lbl':    ImageFont.truetype(MONT_FONT_PATHS['regular'], 45),
            'origin':       ImageFont.truetype(MONT_FONT_PATHS['italic'],  48),
            'footer':       ImageFont.truetype(MONT_FONT_PATHS['regular'], 42)
        }
    except IOError:
        print("⚠️ Nepodařilo se načíst fonty, používám výchozí.")
        default = ImageFont.load_default()
        return {k: default for k in ['weekday_bold','date','name','stats_num','stats_lbl','origin','footer']}

#----------------------------------------
# Pomocná funkce pro centrované vykreslení textu
#----------------------------------------
def draw_centered(draw, text, font, x_center, y):
    width = font.getlength(text)
    draw.text((x_center - width/2, y), text, font=font, fill='black')

#----------------------------------------
# Vykreslí texty: den, datum, jméno, statistiky, původ, footer
#----------------------------------------
def draw_texts(image, name, info):
    draw = ImageDraw.Draw(image)
    fonts = load_fonts()
    w, h = image.size
    x0, y0, sq = create_overlay_square(image)

    # Dny a měsíce
    weekdays = ['Pondělí','Úterý','Středa','Čtvrtek','Pátek','Sobota','Neděle']
    months = {1:'ledna',2:'února',3:'března',4:'dubna',5:'května',6:'června',
              7:'července',8:'srpna',9:'září',10:'října',11:'listopadu',12:'prosince'}

    # 1) Název dne jako "Sobota"
    today = datetime.now()
    day_name = weekdays[today.weekday()]
    y_weekday = y0 + 20
    draw_centered(draw, day_name, fonts['weekday_bold'], w/2, y_weekday)
    wd_height = fonts['weekday_bold'].getbbox(day_name)[3] - fonts['weekday_bold'].getbbox(day_name)[1]

    # 2) Datum pod dnem
    date_txt = f"{today.day}. {months[today.month]}"
    y_date = y_weekday + wd_height + 40
    draw_centered(draw, date_txt, fonts['date'], w/2, y_date)
    dt_height = fonts['date'].getbbox(date_txt)[3] - fonts['date'].getbbox(date_txt)[1]

    # 3) Jméno svátku uprostřed boxu
    y_name = y_date + dt_height + 140
    draw_centered(draw, name, fonts['name'], w/2, y_name)
    nm_height = fonts['name'].getbbox(name)[3] - fonts['name'].getbbox(name)[1]

    # 4) Statistiky
    stats_y = y_name + nm_height + 100
    col_w = sq / 3
    base_x = w/2 - sq/2
    stats_vals = [info.get('rank'), info.get('count'), info.get('avg_age')]
    stats_lbls = ['nejčastější','nositelů','ø věk']
    for i, (val, lbl) in enumerate(zip(stats_vals, stats_lbls)):
        x = base_x + col_w*i + col_w/2
        txt_val = f"{val}." if i == 0 else str(val)
        draw_centered(draw, txt_val, fonts['stats_num'], x, stats_y)
        draw_centered(draw, lbl, fonts['stats_lbl'], x, stats_y + 80)

    # 5) Původ jména
    origin_txt = f"původ: {info.get('origin','–')}"
    y_orig = stats_y + 170
    draw_centered(draw, origin_txt, fonts['origin'], w/2, y_orig)

    # 6) Footer uvnitř boxu, 2 px nad spodní hranou
    y_footer = y0 + sq - 40 - 10
    draw_centered(draw, '@svatekazdyden', fonts['footer'], w/2, y_footer)

#----------------------------------------
# Generování obrázku pro jedno jméno
#----------------------------------------
def generate_image_for(name, info):
    img = generate_gradient_background(1080, 1080)
    draw_texts(img, name, info)
    filename = f"{datetime.now().strftime('%Y-%m-%d')}_{name}.png"
    img.save(filename)
    return filename

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
