from api_handler import generate_with_gemini
from instagram_bot import post_album_to_instagram
from name_info import get_todays_names, get_name_info, get_todays_holiday
from image_generator import generate_image_for, generate_nasa_image
import os
from datetime import datetime, timedelta


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
    names = get_todays_names()
    image_paths = []

    if names:
        print("🎨 Generuji obrázky pro jména...")
        for name in names:
            info = get_name_info(name)
            img_path = generate_image_for(name, info)
            if img_path:
                image_paths.append(img_path)

        if not image_paths:
            print("❌ Nepodařilo se vygenerovat žádné obrázky pro jména.")
            return

        info = get_name_info(names[0]) if names else None
        origin = info.get('origin') if info else 'neuvedeno'

        prompt = (
            f"Napiš kreativní, vtipný a energický popisek na Instagram v češtině, který oslavuje svátek těchto jmen: {names}. "
            f"POZOR – pokud je jméno jen jedno, piš výhradně v jednotném čísle ('Oslava svátku pro Květoslava je tady!'), "
            f"pokud je jmen víc, piš v množném čísle ('Oslava svátku pro Alexeje a Květoslava je tady!'). "
            f"Začni hlavní větou stylu: 🎉 Oslava svátku pro {names} je tady! 🎉 – nebo podobně výraznou oslavnou větou s emojis. "
            f"Na druhý řádek napiš odlehčené a zábavné přání těmto jménům. "
            f"Na třetí řádek zakomponuj původ jména: {origin}, s nadsázkou. "
            f"Na čtvrtý řádek vysvětli význam jména a přidej vtipný komentář. "
            f"Na pátý řádek napiš 2–3 historické osobnosti s tímto jménem a jejich význam. "
            f"Na závěr výzva: 'Znáš nějakého {names}? Označ ho v komentáři a popřej mu! 🎂'. "
            f"Piš v uvolněném, zábavném a emoji-friendly stylu pro sociální sítě."
        )
    else:
        print("ℹ️ Žádné jméno dnes neslaví. Kontroluji státní svátky...")
        holiday = get_todays_holiday()

        if not holiday:
            print("❌ Dnes není žádný svátek ani jmeniny.")
            return

        print(f"🎨 Generuji obrázek pro svátek: {holiday}")
        img_path = generate_image_for(holiday)
        if not img_path:
            print("❌ Nepodařilo se vygenerovat obrázek pro svátek.")
            return
        image_paths.append(img_path)

        prompt = (
            f"Napiš kreativní, vtipný, ale zároveň uctivý popisek na Instagram v češtině, který oslavuje významný den: {holiday}. "
            f"Začni oslavnou větou s emojis, např. 🎉 Dnes si připomínáme {holiday}! 🇨🇿 – udrž tón slavnostní, ale svěží. "
            f"Na druhý řádek napiš odlehčené shrnutí, co tento den pro Česko znamená. "
            f"Na třetí řádek přidej zajímavou historickou souvislost. "
            f"Na čtvrtý řádek 2–3 osobnosti nebo symboly spojené s tímto svátkem. "
            f"Závěrem výzvu k akci: 'Jak si připomínáte {holiday} vy? ✨'. "
            f"Tón: stylový, přirozený, sociálně-síťový. Emojis používej střídmě."
        )

    # 🧠 Vygeneruj AI popis
    ai_response = generate_with_gemini(prompt)
    if not ai_response:
        ai_response = f"🎉 Dnes slavíme {' a '.join(names) if names else holiday}! 🎉\n\nPřipojte se k oslavám tohoto výjimečného dne!"
        print("⚠️ AI odpověď nebyla dostupná. Používám výchozí text.")

    # 📸 Přidej NASA obrázek
    nasa_path, nasa_explanation = generate_nasa_image()
    if nasa_path:
        image_paths.append(nasa_path)
        print("🌌 NASA obrázek přidán do příspěvku.")
        if nasa_explanation:
            print("🌍 Překládám popis NASA obrázku...")
            translated = generate_with_gemini("Přelož následující text z angličtiny do češtiny a uprav jej jako stručný instagramový popisek."
                                                "Zachovej pouze informativní obsah, odstraň pozvánky na akce nebo osobní oslovení."
                                                "Text musí být přirozený, věcný a vhodný pro české publikum a nesmí obsahovat žádné formátovací symboly (hvězdičky, hashtagy, pomlčky na začátku řádku apod.). Pouze čistý text."

                                                "Příklad správného výstupu:"
                                                "Co je to za neobvyklou skvrnu na Měsíci? Je to Mezinárodní vesmírná stanice (ISS)."
                                                "Tento snímek zachycuje ISS při přechodu před Měsícem v roce 2019."
                                                "Expozice byla pouhých 1/667 sekundy, zatímco celý přechod trval asi půl sekundy."
                                                "Na detailním snímku jsou vidět solární panely a konstrukce stanice."
                                                "Vlevo dole je kráter Tycho a měsíční moře (tmavé oblasti) a pevniny (světlé oblasti)"
                                                
                                                "Text ke zpracování:"
                                                f"{nasa_explanation}")
            if translated:
                ai_response += f"\n📷 Fotka z vesmíru:\n{translated}"

    # 📝 Připrav finální popis
    sources =("\nInformace jsou z: czso.cz a nasejmena.cz \nZdroj obrázku: NASA Astronomy Picture of the Day (APOD)")
    hashtags = (
        "\n\n#DnesMaSvatek #SvatekDnes #SvatekKazdyDen "
        "#CeskeJmeniny #Svatky #PoznejSvatky #DnesSlavi"
    )
    description = ai_response + sources + hashtags

    # 📤 Odeslání na Instagram
    print("🚀 Publikuji příspěvek na Instagram...")
    post_album_to_instagram(image_paths, description)






if __name__ == "__main__":
    main()
    print("🔄 [main] Kontroluji zda jsou tu obrázky starší 7 dnů popřípadě je smažu...")
    delete_old_png_files()
