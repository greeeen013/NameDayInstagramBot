from api_handler import generate_with_deepseek, get_todays_international_days
from instagram_bot import post_album_to_instagram
from name_info import get_name_details, get_today_names_and_holidays, letter_map
from image_generator import generate_image_for, generate_nasa_image, generate_international_day_image
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
    Zpracuje všechny případy (jména/svátky) a vrátí finální text pro Instagram
    1. Pokud je svátek - vrátí jeden text o svátku
    2. Pokud jsou jména - vrátí texty o jednotlivých jménech oddělené ---
    """
    final_text = ""

    # Přidání úvodního řádku s jmény/svátky
    if names:
        if len(names) == 1:
            intro = f"🎉 Dnes svátek slaví {names[0]}! 🎉"
        else:
            # Spojení jmen s čárkami a "a" před posledním jménem
            names_str = ", ".join(names[:-1]) + " a " + names[-1]
            intro = f"🎉 Dnes svátek slaví {names_str}! 🎉"
        final_text += f"{intro}\n\n"

    if holidays:
        # Zpracování svátků
        for holiday in holidays:
            prompt = generate_prompt(is_holiday=True, name_or_holiday=holiday)
            response = generate_with_deepseek(prompt)
            if response:
                final_text += f"{response}\n\n"

    if names:
        # Zpracování jmen
        for i, (name, info) in enumerate(zip(names, names_info or [])):
            prompt = generate_prompt(is_holiday=False, name_or_holiday=name, info=info)
            response = generate_with_deepseek(prompt)
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


def main():
    """
    1) Načte dnešní sváteční jména.
    2) Pokud nejsou jmeniny, zkontroluje svátky.
    3) Pro každý případ vygeneruje příslušný obsah a obrázky.
    4) Nahraje obsah na Instagram.
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
        return

    international_days = get_todays_international_days()

    if international_days:
        for day_name in international_days:
            image_paths.append(generate_international_day_image(day_name))
            # ... pokračuj v postování obrázku
    else:
        print("Dnes není žádný mezinárodní den. Používám standardní obrázek.")

    # Generování textu
    ai_response = generate_all_prompts(names, holidays, names_info)
    if not ai_response:
        ai_response = f"🎉 Dnes slavíme {' a '.join(names) if names else holidays[0]}! 🎉\n\nPřipojte se k oslavám tohoto výjimečného dne!"
        print("⚠️ AI odpověď nebyla dostupná. Používám výchozí text.")

    # Přidání NASA obrázku
    nasa_path, nasa_explanation = generate_nasa_image()
    if nasa_path:
        image_paths.append(nasa_path)
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

    # Odeslání na Instagram
    print("🚀 Publikuji příspěvek na Instagram...")
    post_album_to_instagram(image_paths, description)


if __name__ == "__main__":
    main()
    print("🔄 [main] Kontroluji zda jsou tu obrázky starší 7 dnů popřípadě je smažu...")
    delete_old_png_files()