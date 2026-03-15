import time
from api_handler import generate_with_deepseek, get_todays_international_days
from instagram_bot import post_album_to_instagram as post_instagrapi
from playwright_instagram_bot import post_to_instagram as post_playwright
from name_info import get_name_details, get_today_names_and_holidays
from image_generator import generate_image_for, generate_nasa_image, generate_international_day_image
from name_utils import letter_map
from SaveNameStats import get_name_stats_failsafe
from caption_cache import get_cached_caption, save_caption_to_cache
import os
from datetime import datetime, timedelta


def generate_prompt(is_holiday: bool, name_or_holiday: str, info: dict = None) -> str:
    """Generuje jednotlivý prompt pro jedno jméno nebo svátek"""
    if is_holiday:
        holiday = name_or_holiday
        prompt = (
            f"Napiš kreativní, vtipný, ale zároveň uctivý instagramový popisek v češtině k oslavě dne {holiday}.\n"
            "Nepoužívej žádný # ani _ ani * ani slovíčka z jiných jazyků\n"
            "Popisek bude tvořen jedním odstavcem o 3–4 větách, který představí tento svátek.\n"
            f"Začni radostným zvoláním s emoji, že dnes je {holiday}.\n"
            "Dále stručně uveď, co tento den pro Česko znamená nebo co připomíná.\n"
            "Přidej také nějakou zajímavost nebo vtipný fakt o tomto svátku.\n"
            "Tón popisku bude veselý a slavnostní, ale zároveň respektující význam dne."
        )
        return prompt
    else:
        name = name_or_holiday
        origin = info.get("origin", "neznámý") if info else "neznámý"
        meaning = info.get("meaning", "neuveden") if info else "neuveden"
        prompt = (
            f"Zde jsou informace o jménu {name}: Původ: {origin}; Význam: {meaning}.\n"
            f"Napiš kreativní, vtipný, ale zároveň uctivý instagramový popisek v češtině k oslavě jmenin jména {name}.\n"
            "Nepoužívej žádný # ani _ ani * ani anglická slovíčka\n"
            "Popisek bude jeden odstavec o čtyřech větách.\n"
            f"V první větě oslov přímo {name} a popřej mu/jí k svátku (použij humor a emoji).\n"
            f"Druhá věta zmíní původ jména (využij informaci, že původ je {origin}).\n"
            f"Třetí věta zmíní význam jména (využij informaci, že význam je {meaning}).\n"
            #f"Čtvrtá věta připomene nějakou známou osobnost nebo zajímavost spojenou se jménem {name}.\n"
            "Tón popisku bude veselý a přátelský, ale s respektem. Pozor na správné skloňování (vokativ) jména a použití správného rodu."
        )
        return prompt


def generate_all_prompts(names: list, holidays: list, names_info: list = None) -> str:
    """
    Zpracuje všechny případy (jména/svátky) a vrátí finální text pro Instagram.
    Pro každé jméno / svátek nejdříve zkontroluje trvalou cache (caption_cache.json).
    AI je voláno pouze při cache MISS – výsledek se okamžitě uloží pro příští roky.
    """
    final_text = ""

    # Přidání úvodního řádku s jmény/svátky
    if names:
        if len(names) == 1:
            intro = f"🎉 Dnes svátek slaví {names[0]}! 🎉"
        else:
            names_str = ", ".join(names[:-1]) + " a " + names[-1]
            intro = f"🎉 Dnes svátek slaví {names_str}! 🎉"
        final_text += f"{intro}\n\n"

    if holidays:
        for holiday in holidays:
            # 1) Zkus cache
            response = get_cached_caption(holiday)
            if response is None:
                # 2) Cache MISS → zavolej AI
                prompt = generate_prompt(is_holiday=True, name_or_holiday=holiday)
                response = generate_with_deepseek(prompt)
                if response:
                    save_caption_to_cache(holiday, response)
            if response:
                final_text += f"{response}\n\n"

    if names:
        for name, info in zip(names, names_info or []):
            # 1) Zkus cache
            response = get_cached_caption(name)
            if response is None:
                # 2) Cache MISS → zavolej AI
                prompt = generate_prompt(is_holiday=False, name_or_holiday=name, info=info)
                response = generate_with_deepseek(prompt)
                if response:
                    save_caption_to_cache(name, response)
            if response:
                final_text += f"{response}\n\n"

    return final_text.strip()


def delete_old_png_files():
    """
    Smaže PNG soubory starší než 7 dní ve formátu YYYY-MM-DD*.png
    - Prochází adresář 'output/obrazky'
    - Hledá soubory odpovídající vzoru data
    - Maže ty, které jsou starší než 7 dní
    """
    # Cesta k adresáři s obrázky
    image_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    print(f"🔍 [main_delete_old_png_files] Prohledávám adresář: {image_dir}")

    # Vypočítá datum před 7 dny (hranice pro mazání)
    seven_days_ago = datetime.now() - timedelta(days=7)
    print(f"⏳ [main_delete_old_png_files] Mazací hranice: soubory starší než {seven_days_ago.date()}")

    # Kontrola existence adresáře
    if not os.path.exists(image_dir):
        print(f"⚠️ [main_delete_old_png_files] Adresář nenalezen! Ukončuji funkci.")
        return

    file_count = 0
    deleted_count = 0

    # Prochází všechny soubory v adresáři
    for filename in os.listdir(image_dir):
        file_path = os.path.join(image_dir, filename)

        # Přeskočí podadresáře
        if os.path.isdir(file_path):
            print(f"📂 [main_delete_old_png_files] Přeskočen podadresář: {filename}")
            continue

        file_count += 1

        # Zpracovává pouze PNG soubory
        if filename.lower().endswith('.png'):
            print(f"🖼️ [main_delete_old_png_files] Zpracovávám soubor: {filename}")

            try:
                # Pokusí se získat datum z názvu souboru (formát YYYY-MM-DD)
                date_str = filename[:10]  # Prvních 10 znaků by mělo být datum

                file_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                # Porovnání data - pokud je soubor starší než 7 dní, smaže ho
                if file_date < seven_days_ago.date():
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"🗑️ [main_delete_old_png_files] SMAZÁNO: {filename} (datum: {file_date})")
                else:
                    print(f"👍 [main_delete_old_png_files] Zachovávám (je aktuální): {filename}")

            except ValueError:
                # Přeskočí soubory, které neodpovídají formátu data
                print(f"❓ [main_delete_old_png_files] Přeskočeno - neplatný formát data: {filename}")
                continue
        else:
            print(f"⏭️ [main_delete_old_png_files] Přeskočeno - není PNG: {filename}")

    # Výpis statistik po dokončení
    print(f"📊 [main_delete_old_png_files] CELKEM: {file_count} souborů prohledáno")
    print(f"📊 [main_delete_old_png_files] SMAZÁNO: {deleted_count} souborů")
    print(f"🏁 [main_delete_old_png_files] Úklid dokončen!")


def save_caption(caption: str):
    """Saves the generated caption to a file."""
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    os.makedirs(output_dir, exist_ok=True)
    today_str = datetime.now().strftime('%Y-%m-%d')
    filepath = os.path.join(output_dir, f'caption_{today_str}.txt')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(caption)
    print(f"📝 [main] Caption saved to {filepath}")


def load_caption() -> str:
    """Loads the caption from a file if it exists."""
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    today_str = datetime.now().strftime('%Y-%m-%d')
    filepath = os.path.join(output_dir, f'caption_{today_str}.txt')
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            print(f"📖 [main] Loading cached caption from {filepath}")
            return f.read()
    return None


def prepare_content():
    """
    Fáze 1 (drahá): Načte jména, vygeneruje obrázky a caption.
    Vrátí (image_paths, description) nebo vyhodí výjimku.
    """
    print("🍀 Načítám dnešní sváteční jména...")
    names, holidays = get_today_names_and_holidays()
    image_paths = []
    names_info = []

    # Speciální případ - Cyril a Metoděj
    if holidays == ['Den věrozvěstů Cyrila a Metoděje']:
        print("🎉 Dnes slaví svátek Cyril a Metoděj!")
        names = ["Cyril", "Metoděj"]

        # Generování obrázků
        holiday_img = generate_image_for(holidays[0])
        if holiday_img:
            image_paths.append(holiday_img)

        for name in names:
            try:
                info = get_name_details(name, letter_map)
                if info is None:  # Explicitní kontrola None
                    info = get_name_stats_failsafe(name, datetime.now())
            except Exception as e:
                print(f"⚠️ Chyba při získávání statistik: {e}")
                info = get_name_stats_failsafe(name, datetime.now())

            if info:
                names_info.append(info)
                img_path = generate_image_for(name, info)
            else:
                img_path = generate_image_for(name)
                names_info.append({})

            if img_path:
                image_paths.append(img_path)

    # Normální případ - jména
    elif names:
        print("🎨 Generuji obrázky pro jména...")
        for name in names:
            try:
                info = get_name_details(name, letter_map)
            except Exception as e:
                print(f"⚠️ Chyba při získávání statistik: {e}")
                info = None

            if info:
                names_info.append(info)
                img_path = generate_image_for(name, info)
            else:
                # Fallback bez statistik
                img_path = generate_image_for(name)
                names_info.append({})

            if img_path:
                image_paths.append(img_path)

    # Pouze svátek
    elif holidays:
        print("ℹ️ Žádné jméno dnes neslaví. Kontroluji státní svátky...")
        holiday = holidays[0]
        print(f"🎨 Generuji obrázek pro svátek: {holiday}")
        img_path = generate_image_for(holiday)
        if img_path:
            image_paths.append(img_path)

    else:
        print("❌ Dnes není žádný svátek ani jmeniny.")
        return None, None

    international_days = get_todays_international_days()

    if international_days:
        for day_name in international_days:
            image_paths.append(generate_international_day_image(day_name))
    else:
        print("Dnes není žádný mezinárodní den. Používám standardní obrázek.")

    # Generování textu - s kontrolou cache
    description = load_caption()

    if not description:
        ai_response = generate_all_prompts(names, holidays, names_info)
        if not ai_response:
            ai_response = f"🎉 Dnes slavíme {' a '.join(names) if names else holidays[0]}! 🎉\n\nPřipojte se k oslavám tohoto výjimečného dne!"
            print("⚠️ AI odpověď nebyla dostupná. Používám výchozí text.")

        # Přidání NASA obrázku
        nasa_path, nasa_explanation = generate_nasa_image()
        if nasa_path:
            image_paths.append(nasa_path)
            print("✔️ NASA obrázek přidán.")
            if nasa_explanation:
                translated = generate_with_deepseek(
                    "Přelož následující text z angličtiny do češtiny a uprav jej jako stručný instagramový popisek, klidně použij emoji ale nepoužívej žádný # ani _ ani *.\n"
                    f"Text ke zpracování:\n{nasa_explanation}"
                )
                if translated:
                    ai_response += f"\n\n📷 Fotka vesmíru:\n{translated}"

        # Finální popis
        sources = "\n\nKdo má svátek je z: kalendar.beda.cz \nStatistiky jsou z: nasejmena.cz \nZdroj obrázku: NASA Astronomy Picture of the Day (APOD)"
        hashtags = "\n\n#DnesMaSvatek #SvatekDnes #SvatekKazdyDen #CeskeJmeniny #Svatky #PoznejSvatky #DnesSlavi"
        description = ai_response + sources + hashtags

        # Uložení do cache
        save_caption(description)

    return image_paths, description


def post_with_retry(image_paths: list, description: str, max_retries: int = 10, retry_delay: int = 3600):
    """
    Fáze 2 (levná, opakovatelná): Zkouší přihlásit se na Instagram a odeslat příspěvek.
    Opakuje pouze tuto fázi – bez opakování drahého generování obsahu.
    """
    import pyotp
    totp_secret = os.getenv("IG_2FA_SECRET")

    for attempt in range(1, max_retries + 1):
        print(f"▶️ Pokus o přihlášení a publikaci {attempt}/{max_retries}")
        try:
            # 2FA kód generujeme těsně před pokusem (kód vyprší za 30 s)
            if totp_secret:
                totp = pyotp.TOTP(totp_secret.replace(" ", ""))
                two_factor_code = totp.now()
                print(f"🔐 Generuji 2FA kód: {two_factor_code}")
            else:
                two_factor_code = None
                print("⚠️ Chybí IG_2FA_SECRET, 2FA kód nebude zadán.")

            # Playwright je primární metoda (spolehlivější než instagrapi)
            # PLAYWRIGHT_HEADLESS=1 pro server bez displeje, jinak poběží viditelně
            playwright_headless = os.getenv("PLAYWRIGHT_HEADLESS", "0") == "1"
            try:
                print("▶️ Zkouším nahrát přes playwright...")
                post_playwright(image_paths, description, two_factor_code, headless=playwright_headless)
                print("✅ Příspěvek úspěšně publikován přes playwright!")
                return
            except Exception as play_e:
                print(f"⚠️ Playwright selhal (pokus {attempt}/{max_retries}): {play_e}")
                print("▶️ Zkouším záložní nahrání přes instagrapi...")
                try:
                    post_instagrapi(image_paths, description)
                    print("✅ Příspěvek úspěšně publikován přes instagrapi!")
                    return
                except Exception as e:
                    print(f"❌ Instagrapi také selhalo: {e}")
                    raise Exception(f"Obě metody selhaly.")
        except Exception as e:
            print(f"❌ Chyba při publikaci (pokus {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                print(f"⏳ Čekám {retry_delay} sekund (1 hodina) před dalším pokusem...")
                time.sleep(retry_delay)
            else:
                print("⛔ Dosažen maximální počet pokusů publikace. Končím.")
                raise


def main():
    # --- Fáze 1: Generování obsahu (jednou, drahé API volání) ---
    print("▶️ Spouštím generování obsahu...")
    image_paths, description = prepare_content()

    if image_paths is None:
        print("⛔ Žádný obsah k publikaci. Ukončuji.")
        return

    # --- Fáze 2: Publikace na Instagram (opakujeme jen tuto část) ---
    print("🚀 Publikuji příspěvek na Instagram...")
    post_with_retry(image_paths, description, max_retries=10, retry_delay=3600)

if __name__ == "__main__":
    main()
    print("🔄 [main] Kontroluji zda jsou tu obrázky starší 7 dnů popřípadě je smažu...")
    delete_old_png_files()