import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps
import os

from api_handler import get_nasa_apod, generate_ai_background

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


# ----------------------------------------
# Generuje AI pozadí nebo záložní gradient
# ----------------------------------------
def generate_background(width, height):
    print("🔄 Pokus o generování AI pozadí...")
    ai_background = generate_ai_background(width, height)

    if ai_background is None:
        print("⚠️ AI selhalo, generuji gradient")
        bg = generate_gradient_background(width, height)
        print(f"🔵 Vygenerován gradient: {bg.size}")
        return bg

    print(f"🟢 Úspěšně vygenerováno AI pozadí: {ai_background.size}")
    return ai_background


#----------------------------------------
# Vytvoří průhledný čtverec (overlay) uprostřed
# padding 0.1 znamená box 90% velikosti
#----------------------------------------
def create_overlay_square(image, padding=0.1, opacity=0.75):
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
            'weekday_bold':         ImageFont.truetype(MONT_FONT_PATHS['bold'],   80),
            'date':                 ImageFont.truetype(MONT_FONT_PATHS['medium'], 60),
            'name':                 ImageFont.truetype(MONT_FONT_PATHS['bold'],   150),
            'name_smaller':         ImageFont.truetype(MONT_FONT_PATHS['bold'],     120),
            'stats_num':            ImageFont.truetype(MONT_FONT_PATHS['bold'],    80),
            'stats_lbl':            ImageFont.truetype(MONT_FONT_PATHS['regular'], 45),
            'origin':               ImageFont.truetype(MONT_FONT_PATHS['italic'],  48),
            'footer':               ImageFont.truetype(MONT_FONT_PATHS['regular'], 42),
            'bold_title_smaller':   ImageFont.truetype(MONT_FONT_PATHS['bold'], 60)
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
        # 3) Svátek uprostřed – zalomení textu svátku, pokud přesahuje 10 znaků
        if len(name) > 10:
            lines = []
            text = name  # kopie textu, který budeme postupně zkracovat
            limit = 10
            while len(text) > limit:
                # Zkusit najít mezeru *po* 10. znaku
                space_index = text.find(' ', limit)
                # Pokud není mezera po limitu, zkusit poslední mezeru před limitem
                if space_index == -1:
                    space_index = text.rfind(' ', 0, limit + 1)
                # Žádná mezera v dosahu -> ukončit cyklus
                if space_index == -1:
                    break
                # Vezmeme část textu před mezerou jako jeden řádek
                line = text[:space_index]
                lines.append(line.strip())  # .strip() pro odstranění případné mezery na konci
                text = text[space_index + 1:]  # zbytek textu po této mezeře
            # Přidat poslední část (poslední řádek)
            if text:
                lines.append(text.strip())
            # Vykreslit každý řádek centrovaně, posunutý vertikálně
            line_count = len(lines)
            ascent, descent = font_for_name.getmetrics()
            line_height = ascent + descent
            # Horní řádek posuneme tak, aby blok textu byl vystředěný
            start_y = h // 2 - ((line_count - 1) * line_height) // 2
            for i, line in enumerate(lines):
                draw_centered(draw, line, font_for_name, center_x, start_y + i * line_height)
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
    img_square = ImageOps.fit(img, (1080, 1080), Image.Resampling.LANCZOS, centering=(0.5, 0.5))

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

    img = generate_background(1080, 1080)
    draw_texts(img, name, info)
    filename = f"{datetime.now().strftime('%Y-%m-%d')}_{name}.png"

    # Vytvoření cesty k souboru
    filepath = os.path.join(output_dir, filename)

    print("✅ [image_generator] Soubor byl uložen do: "+os.path.abspath(filepath))
    img.save(filepath)
    return filepath


def generate_international_day_image(day_name):
    from pathlib import Path
    import os
    from PIL import Image, ImageDraw
    from datetime import datetime

    # Dny a měsíce
    weekdays = ['Pondělí', 'Úterý', 'Středa', 'Čtvrtek', 'Pátek', 'Sobota', 'Neděle']
    months = {
        1: 'ledna', 2: 'února', 3: 'března', 4: 'dubna', 5: 'května', 6: 'června',
        7: 'července', 8: 'srpna', 9: 'září', 10: 'října', 11: 'listopadu', 12: 'prosince'
    }

    # Předpokládáme, že následující proměnné a funkce jsou definovány jinde v kódu
    # BASE_DIR, generate_background, load_fonts, create_overlay_square, draw_centered, MONT_FONT_PATHS
    output_dir = Path(BASE_DIR) / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    img = generate_background(1080, 1080)
    draw = ImageDraw.Draw(img)
    fonts = load_fonts()
    w, h = img.size
    x0, y0, sq = create_overlay_square(img)
    center_x = w // 2

    # Rozvržení
    line_height = sq // 8

    # 1) Horní malý text: "dnes je"
    y1 = y0 + line_height * 0
    draw_centered(draw, "Dnes je", fonts['weekday_bold'], center_x, y1)

    # 2) Horní malý text s datumem
    today = datetime.now()
    date_txt = f"{today.day}. {months[today.month]}"
    y1 = y0 + line_height * 1 - 20
    draw_centered(draw, date_txt, fonts['date'], center_x, y1)

    # 3) Střední text: "Mezinárodní den"
    y2 = y0 + line_height * 2
    draw_centered(draw, "Mezinárodní den", fonts['stats_num'], center_x, y2)

    # 4) Velký text – název dne
    # Konfigurace dynamického chování
    CONFIG = {
        'font': {
            'max_size': 170,  # Zvýšená maximální velikost
            'min_size': 50,  # Zvýšená minimální velikost
            'chars_sensitivity': 1.2,  # Výrazně snížená citlivost na znaky
            'words_sensitivity': 0.8,  # Snížená citlivost na slova
            'lines_penalty': 10  # Mírný penal za více řádků
        },
        'wrapping': {
            'max_chars_per_line': 28,
            'min_chars_per_line': 10,
            'target_lines': 3,
            'long_word_threshold': 15  # Považovat slovo za dlouhé od tohoto počtu znaků
        },
        'spacing': {
            'line_spacing_factor': 0.25,  # Menší mezera mezi řádky
            'vertical_offset_factor': 0.8  # Jemnější vertikální pozicování
        }
    }

    # Získání textu
    display_text = day_name.replace("Mezinárodní den", "").replace("Den", "").strip().capitalize().replace(
        "Světový den", "").strip().capitalize().replace("Evropský den", "").strip().capitalize()

    # Vylepšené zalomení textu
    def balanced_wrap(text):
        words = text.split()
        if not words:
            return []

        # Rozdělení extrémně dlouhých slov
        for i, word in enumerate(words):
            if len(word) > CONFIG['wrapping']['long_word_threshold']:
                split_pos = len(word) // 2
                words[i:i + 1] = [word[:split_pos] + "-", word[split_pos:]]

        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            if len(test_line) <= CONFIG['wrapping']['max_chars_per_line']:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        # Optimalizace pro přirozenější zalomení
        if len(lines) > CONFIG['wrapping']['target_lines']:
            lines = []
            current_line = []
            avg_chars = len(text) / CONFIG['wrapping']['target_lines']

            for word in words:
                test_line = ' '.join(current_line + [word])
                if (len(test_line) <= avg_chars * 1.3 or not current_line):
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))

        return lines

    # Funkce pro přesunutí osamocených slov
    def fix_orphans(lines):
        orphans = set(['a', 'i', 'o', 'u', 'k', 's', 'v', 'z', 'se', 'si'])
        i = 0
        while i < len(lines) - 1:
            words = lines[i].split()
            if words and words[-1] in orphans:
                orphan_word = words.pop()
                lines[i] = ' '.join(words)
                lines[i+1] = orphan_word + ' ' + lines[i+1].lstrip()
                if not lines[i].strip():
                    lines.pop(i)
                    i -= 1
            i += 1
        return lines

    lines = balanced_wrap(display_text)
    orphans = set(['a', 'i', 'o', 'u', 'k', 's', 'v', 'z', 'se', 'si'])
    lines = fix_orphans(lines)

    words_count = len(display_text.split())
    chars_count = len(display_text)

    # Dynamická velikost písma
    size_reduction = (
            (chars_count * CONFIG['font']['chars_sensitivity']) +
            (words_count * CONFIG['font']['words_sensitivity']) +
            (len(lines) * CONFIG['font']['lines_penalty'])
    )

    font_size = max(
        CONFIG['font']['min_size'],
        CONFIG['font']['max_size'] - size_reduction
    )

    # Kontrola šířky a dodatečné zmenšování písma
    max_line_width = sq * 0.8
    temp_font = ImageFont.truetype(MONT_FONT_PATHS['bold'], int(font_size))
    if lines:
        max_width = max(temp_font.getlength(line) for line in lines)
    else:
        max_width = 0

    while max_width > max_line_width and font_size > CONFIG['font']['min_size']:
        font_size -= 1
        temp_font = ImageFont.truetype(MONT_FONT_PATHS['bold'], int(font_size))
        max_width = max(temp_font.getlength(line) for line in lines) if lines else 0

    dynamic_font = temp_font

    # Výpočet pozicování
    ascent, descent = dynamic_font.getmetrics()
    line_spacing = int(ascent * CONFIG['spacing']['line_spacing_factor'])
    total_height = len(lines) * (ascent + line_spacing) - line_spacing

    base_y_position = y0 + line_height * 4
    vertical_offset = {
        1: -30,
        2: -15,
        3: 0,
        4: 15,
        5: 25
    }.get(len(lines), 30)

    start_y = base_y_position + int(vertical_offset * CONFIG['spacing']['vertical_offset_factor']) - (total_height // 2) + 120

    # Vykreslení řádků
    for i, line in enumerate(lines):
        draw_centered(draw, line, dynamic_font, center_x, start_y + i * (ascent + line_spacing))

    # 5) Footer
    y_footer = y0 + sq - 50
    draw_centered(draw, "@svatekazdyden", fonts['footer'], center_x, y_footer)

    # Uložení
    filename = f"{datetime.now().strftime('%Y-%m-%d')}_{display_text.replace(' ', '_')}.png"
    filepath = os.path.join(output_dir, filename)
    img.save(filepath)
    print("✅ [image_generator] Mezinárodní den uložen do:", os.path.abspath(filepath))
    return filepath