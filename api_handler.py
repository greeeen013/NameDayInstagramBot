import random
from datetime import datetime
from io import BytesIO
from bs4 import BeautifulSoup

from PIL import Image
from dotenv import load_dotenv
import os
import requests
import json
import re

from google import genai
from together import Together

# Načtení API klíče z .env souboru
load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
NASA_API_KEY = os.getenv("NASA_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")



def generate_with_gemini(prompt, model="gemini-2.0-flash", max_retries=3):
    """
    Získává odpověď od Google Gemini API pomocí google-genai SDK.

    Args:
        prompt (str): Textový vstup (prompt) pro AI
        model (str): Použitý model (výchozí je gemini-2.0-flash)
        max_retries (int): Maximální počet opakování při chybě

    Returns:
        str: Odpověď od AI nebo None pokud selže
    """
    try:
        # Použije GEMINI_API_KEY z .env (automaticky jako GOOGLE_API_KEY pokud je nastaveno správně, 
        # ale pro jistotu předáme api_key explicitně, pokud se liší název env proměnné)
        client = genai.Client(api_key=GEMINI_API_KEY)

        print(f"promptuju gemini...")
        
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                
                if response and response.text:
                    print(f"gemini uspesne odpovedelo prvnich 100 znaku:\n{response.text[:100]}...")
                    return response.text
                else:
                    print(f"Pokus {attempt + 1}: Prázdná odpověď z Gemini API")

            except Exception as e:
                print(f"Pokus {attempt + 1} selhal s chybou: {str(e)}")
                if attempt == max_retries - 1:
                    return None
                    
    except Exception as e:
         print(f"Kritická chyba při inicializaci Gemini klienta: {e}")
         return None

    return None

def generate_with_deepseek(prompt, model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free", max_retries=3):
    """
    DEPRECATED: Původně pro DeepSeek, nyní jen wrapper pro generate_with_gemini.
    """
    return generate_with_gemini(prompt, max_retries=max_retries)


def get_nasa_apod(max_retries=3):
    if not NASA_API_KEY:
        print("❌ [api_handler] NASA_API_KEY není nastaveno v .env souboru.")
        return None

    import time
    from datetime import datetime, timedelta

    def _fetch(date_str=None):
        base = "https://api.nasa.gov/planetary/apod"
        params = {"api_key": NASA_API_KEY, "thumbs": "true"}
        if date_str:
            params["date"] = date_str
        try:
            res = requests.get(base, params=params, timeout=10)
            return res
        except Exception as e:
            print(f"❌ [api_handler] Výjimka při volání NASA APOD API: {e}")
            return None

    # 1) Zkus dnešek s retry/backoff
    for attempt in range(1, max_retries + 1):
        res = _fetch()
        if res and res.status_code == 200:
            break
        wait = min(2 ** attempt, 10)
        code = res.status_code if res else "no-response"
        body = res.text[:200] if (res and res.text) else ""
        print(f"❌ [api_handler] Chyba {code} při volání NASA APOD API (pokus {attempt}/{max_retries}). {body}")
        time.sleep(wait)
    else:
        # 2) Fallback – zkus včerejšek (často pomůže)
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        res = _fetch(yesterday)
        if not res or res.status_code != 200:
            code = res.status_code if res else "no-response"
            print(f"❌ [api_handler] Fallback (včerejšek) selhal – kód {code}.")
            return None

    data = res.json()
    # Vem hdurl/url/thumb (pro video)
    url = data.get("hdurl") or data.get("url") or data.get("thumbnail_url")
    explanation = data.get("explanation")
    if not url or not explanation:
        print("❌ [api_handler] Chybí URL nebo explanation v odpovědi NASA.")
        return None
    return {"hdurl": url, "explanation": explanation}

def generate_ai_background(width=1080, height=1080):
    """Generuje pozadí pomocí Google Gemini (Imagen)"""
    if not GEMINI_API_KEY:
        print("❌ [AI] Chybí GEMINI_API_KEY (GOOGLE_API_KEY) v .env")
        return None

    # wait_for_image_window(min_secs=300) # Removed as per user request

    # Prompty pro generování (stejné jako předtím)
    prompts = [
          "calm autumn landscape with falling leaves and soft light",
          "cozy corner with pillows and candles under dim lighting",
          "forest clearing covered in morning mist",
          "minimalist room with natural tones and soft lighting",
          "mountain cabin in winter with glowing window and snowy landscape",
          "soft sunlight streaming through curtains",
          "peaceful lake surrounded by trees at sunset",
          "Scandinavian interior with muted lights",
          "reading nook with a blanket, book, and hot tea",
          "quiet morning forest with dewdrops on leaves",
          "relaxing café with wooden furniture and plants",
          "neutral background with watercolor texture in beige tones",
          "night cityscape from afar with gentle bokeh",
          "cozy bed with duvets and soft lamp light",
          "old wooden table with a cup of coffee and a journal",
          "view from a window on a rainy day",
          "lightly snow-covered fields under a grey sky",
          "forest path with soft moss and diffused light",
          "cozy fireplace corner with a fluffy rug",
          "minimalist background with pastel shades",
          "mountain valley in mist and morning light",
          "soft blanket draped over a warm-toned sofa",
          "quiet beach at sunrise with no people",
          "blooming meadow in pastel colors",
          "rainy window with blurred droplets and warm indoor light",
          "modern room with houseplants and an aroma diffuser",
          "quiet evening riverside with lanterns",
          "library with old books and soft lighting",
          "waving wheat in golden light",
          "glowing lanterns hanging in a garden at dusk",
          "soft textures of beige and grey fabrics",
          "relaxed afternoon with coffee on the terrace",
          "blurred light effects in warm tones",
          "quiet alley in an old town with no people",
          "aerial view of foggy mountains",
          "wooden interior with natural decorations",
          "cozy lantern light in the garden at twilight",
          "pastel sunset over water surface",
          "calm tones of grey, beige, and white in a natural style",
          "tea ceremony in a Japanese room",
          "shadow of a tree falling on a wall",
          "green houseplants on a windowsill in morning light",
          "road fading into fog with autumn trees",
          "cozy kitchen with herbs and warm lighting",
          "neutral marble texture with soft reflections",
          "old radio and a tea mug on a wooden cabinet",
          "half-empty café with a retro feel",
          "peaceful evening on a balcony with a blanket and tea",
          "zen garden with stones and sand",
          "soft pastel colors and blurred light"
    ]

    try:
        # Použití Google GenAI klienta (již importován jako genai)
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Výběr modelu - Imagen 3 nebo 4 podle dostupnosti pro "Paid Tier 1"
        # Zkoušíme nejnovější fast model, který by měl být dostupný pro placené účty
        model_name = "imagen-4.0-fast-generate-001" 
        
        prompt = random.choice(prompts)
        full_prompt = "hyper realistic environment, " + prompt

        print(f"📝 [AI] Generuji obrázek s modelem {model_name}...")
        print(f"📝 [AI] Prompt: '{full_prompt}'")

        response = client.models.generate_images(
            model=model_name,
            prompt=full_prompt,
            config={
                'number_of_images': 1,
            }
        )

        if not response.generated_images:
            print("❌ [AI] API nevrátilo žádný obrázek")
            return None

        # Získání obrazových dat (bytes)
        image_bytes = response.generated_images[0].image.image_bytes
        print(f"⬇️ [AI] Obrázek vygenerován ({len(image_bytes)} bytes).")

        img = Image.open(BytesIO(image_bytes))
        print(f"🖼️ [AI] Načteno: {img.size} ({img.format}), mód: {img.mode}")

        if img.size != (width, height):
            print(f"🔄 [AI] Změna velikosti na {width}x{height}")
            img = img.resize((width, height), Image.Resampling.LANCZOS)

        return img.convert('RGBA')

    except Exception as e:
        print(f"❌ [AI] Chyba při generování obrázku přes Gemini:")
        if "quota" in str(e).lower() or "billed" in str(e).lower():
            print("⚠️ [AI] Zdá se, že nemáte povolenou fakturaci (Paid Tier) nebo jste vyčerpali kvótu.")
        import traceback
        traceback.print_exc()
        return None


def clean_event_name(text):
    """Vyčistí název události od závorek a jejich obsahu"""
    # Odstraníme hranaté závorky s čísly [123]
    text = re.sub(r'\[\d+\]', '', text)
    # Odstraníme kulaté závorky a jejich obsah (I Forgot Day)
    text = re.sub(r'\([^)]*\)', '', text)
    # Odstraníme přebytečné mezery a ořízneme text
    return ' '.join(text.split()).strip()


def get_todays_international_days():
    # České názvy měsíců
    czech_months = {
        1: 'leden', 2: 'únor', 3: 'březen', 4: 'duben', 5: 'květen',
        6: 'červen', 7: 'červenec', 8: 'srpen', 9: 'září',
        10: 'říjen', 11: 'listopad', 12: 'prosinec'
    }

    # Získání aktuálního data
    today = datetime.today()
    day = today.day
    month = today.month
    today_str = f"{day}. {czech_months[month]}"
    #print(f"[DEBUG] Hledám dnešní datum: {today_str}")

    try:
        # Stažení stránky
        url = "https://cs.wikipedia.org/wiki/Mezin%C3%A1rodn%C3%AD_dny_a_roky"
        #print(f"[DEBUG] Stahuji stránku: {url}")
        headers = {"User-Agent": "NameDayInstagramBot/1.0 (https://github.com/greeeen013/NameDayInstagramBot)"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parsování HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Nalezení tabulky mezinárodních dnů
        #print("[DEBUG] Hledám tabulku mezinárodních dnů...")
        tables = soup.find_all('table', {'class': 'wikitable'})
        table = None
        for t in tables:
            if "Datum" in str(t):
                table = t
                break
        if not table:
            #print("[DEBUG] Tabulka nebyla nalezena!")
            return []
        #print("[DEBUG] Tabulka nalezena")

        events = []
        found_today = False
        collect_events = False

        # Procházení řádků tabulky
        #print("[DEBUG] Procházím řádky tabulky...")
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if not cells:
                continue

            # Zpracování prvního sloupce (datum)
            date_cell = cells[0]
            date_text = date_cell.get_text().strip()
            #print(f"[DEBUG] Zpracovávám řádek s datem/textem: {date_text}")

            # Zvláštní případ - když je název dne přímo v date_cell
            if ("den" in date_text or "dny" in date_text) and found_today:
                clean_text = clean_event_name(date_text)
                #print(f"[DEBUG] Nalezen den přímo v datovém sloupci: {clean_text}")
                events.append(clean_text)
                continue

            # Kontrola formátu data (den. měsíc)
            if '.' in date_text:
                if found_today and date_text != today_str:
                    #print(f"[DEBUG] Nalezeno další datum: {date_text}, ukončuji hledání")
                    break

                if date_text == today_str:
                    found_today = True
                    collect_events = True
                    #print("[DEBUG] Nalezeno dnešní datum! Začínám sbírat události...")

            # Sbírání událostí pro dnešní datum
            if collect_events and len(cells) > 1:
                event_cell = cells[1]
                event_text = event_cell.get_text().strip()
                #print(f"[DEBUG] Zpracovávám událost: {event_text}")

                # Hledání názvů obsahujících "den" nebo "dny"
                if "den" in event_text or "dny" in event_text:
                    #print("[DEBUG] Nalezena událost obsahující 'den' nebo 'dny'")
                    # Extrakce jednotlivých názvů mezinárodních dnů
                    for sub in event_cell.find_all(['a', 'sup']):
                        sub_text = sub.get_text().strip()
                        if "den" in sub_text or "dny" in sub_text:
                            clean_text = clean_event_name(sub_text)
                            #print(f"[DEBUG] Přidávám událost: {clean_text}")
                            events.append(clean_text)

                    # Přidání celého textu, pokud neobsahuje podprvky
                    if not any("den" in e or "dny" in e for e in events):
                        clean_text = clean_event_name(event_text)
                        #print(f"[DEBUG] Přidávám celou událost: {clean_text}")
                        events.append(clean_text)

        # Zpracování událostí
        #print("[DEBUG] Filtruji a upravuji výsledné události...")
        final_events = []
        for event in events:
            # Rozdělení textů s čárkami
            if ',' in event:
                for e in event.split(','):
                    e = clean_event_name(e.strip())
                    if "den" in e or "dny" in e:
                        final_events.append(e)
            else:
                final_events.append(event)

        # Odstranění duplicit a prázdných řetězců
        final_events = list(set([e for e in final_events if e]))
        #print(f"[DEBUG] Konečný seznam událostí: {final_events}")
        return final_events

    except Exception as e:
        print(f"[get_todays_international_days] Chyba při zpracování: {e}")
        return []

if __name__ == "__main__":
    print("Testuju gemini")
    resp = generate_with_gemini("Napiš krátkou básničku o létě v češtině.")
    print("Gemini response:")
    print(resp)
    #else:
    #    print("Žádné mezinárodní dny dnes nenalezeny.")