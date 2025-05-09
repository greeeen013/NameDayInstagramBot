from api_handler import generate_with_gemini
from instagram_bot import post_album_to_instagram
from name_info import get_todays_names, get_name_info, get_todays_holiday
from image_generator import generate_image_for
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

    if not names:
        print("ℹ️ Žádné sváteční jméno pro dnešek. Kontroluji svátky...")
        holiday = get_todays_holiday()

        if not holiday:
            print("❌ Dnes není žádný svátek ani jmeniny.")
            return

        # Generování popisu pro svátek
        print("🔄 Generuji AI popis pro Svátek na Instagram popisek...")
        prompt = (
            f"Napiš kreativní, vtipný, ale zároveň uctivý popisek na Instagram v češtině, který oslavuje významný den: {holiday}. "
            f"Začni oslavnou větou s emojis, např. 🎉 Dnes si připomínáme {holiday}! 🇨🇿 – udrž tón slavnostní, ale svěží. "
            f"Na druhý řádek napiš zábavné a odlehčené shrnutí, co tento den pro Česko znamená – nepoužívej přehnanou ironii. "
            f"Na třetí řádek přidej zajímavou historickou souvislost nebo fakt s lehkým nadhledem, ale s respektem. "
            f"Na čtvrtý řádek napiš 2–3 konkrétní osobnosti, události nebo symboly spojené s tímto svátkem – napiš, proč jsou významné. "
            f"Na závěr přidej výzvu k akci, např. 'Jak si připomínáte {holiday} vy? Podělte se s námi v komentářích! ✨'. "
            f"Celý výstup by měl být přístupný, stylový a přirozený – ideální pro sociální sítě. Používej emojis střídmě, drž tón mezi důstojným a lehce odlehčeným."
        )


        # Generování obrázku pro svátek
        print(f"🔄 Generuji obrázek pro svátek: {holiday}")
        img_path = generate_image_for(holiday)

        if not img_path:
            print("❌ Nepodařilo se vygenerovat obrázek pro svátek")
            return

        # Generování AI popisu
        ai_response = generate_with_gemini(prompt)
        if not ai_response:
            ai_response = f"🎉 Dnes slavíme {holiday}! 🎉\n\nPřipojte se k oslavám tohoto výjimečného dne!"
            print("❌ Nepodařilo se vygenerovat AI popis. Používám výchozí text.")

        print(ai_response)
        description = (ai_response +
                       f"\n\n\nInformace o svátcích: wikipedie.cz\n"
                       f"#DnesMaSvatek #SvatekDnes #{holiday.replace(' ', '')} "
                       f"#SvatecniDen #DenniSvatek #SvatekKazdyDen #SvatekVCesku "
                       f"#DnesSlavi #Zajimavosti #PoznejSvatky")

        print("🚀 Odesílám příspěvek o svátku na Instagram...")
        post_album_to_instagram([img_path], description)

    else:
        # Původní logika pro jmeniny
        image_paths = []
        for name in names:
            print(f"🔄 Generuji obrázek pro: {name}")
            info = get_name_info(name)
            img_path = generate_image_for(name, info)
            if img_path:
                image_paths.append(img_path)

        if not image_paths:
            print("❌ Nepodařilo se vygenerovat žádné obrázky")
            return

        print("🔄 Generuji AI popis pro Jména na Instagram popisek...")
        info = get_name_info(names[0]) if names else None

        prompt = (
            f"Napiš kreativní, vtipný a energický popisek na Instagram v češtině, který oslavuje svátek těchto jmen: {names}. "
            f"POZOR – pokud je jméno jen jedno, piš výhradně v jednotném čísle ('Oslava svátku pro Květoslava je tady!'), "
            f"pokud je jmen víc, piš v množném čísle ('Oslava svátku pro Alexeje a Květoslava je tady!'). "
            f"Začni hlavní větou stylu: 🎉 Oslava svátku pro {names} je tady! 🎉 – nebo podobně výraznou oslavnou větou s emojis. "
            f"Na druhý řádek napiš odlehčené a zábavné přání těmto jménům – mluv ke jménům jako k osobnostem, ne k lidem. "
            f"Na třetí řádek zakomponuj původ jména, použij hodnotu {info['origin'] if info else 'neuvedeno'} a formuluj to s nadsázkou. "
            f"Na čtvrtý řádek vtipně vysvětli význam jména – například 'květoslava – kvetoucí, květinová' a přidej zábavný komentář. "
            f"Na pátý řádek napiš 2–3 historické nebo známé osobnosti s tímto jménem, každou uveď ve formátu: Jméno – důvod slavnosti (např. 'Josef Jungmann – národní buditel'). "
            f"Nepoužívej jména vícekrát v textu. "
            f"Na závěr přidej výzvu k akci, např. 'Tak co, znáte nějakého {names}? Označte ho v komentářích a popřejte mu! 🎂'. "
            f"Celý výstup piš uvolněně, s lehkým humorem, bohatě používej emojis. Piš jako popisek na sociální sítě, ne jako encyklopedii."
        )

        ai_response = generate_with_gemini(prompt)
        if not ai_response:
            ai_response = f"🎉 Dnes má svátek {names}! 🎉\n\nVšem {names} přejeme vše nejlepší!"
            print("❌ Nepodařilo se vygenerovat AI popis. Používám výchozí text.")

        print(ai_response)
        description = (ai_response +
                       f"\n\n\nInformace jsou z: czso.cz a nasejmena.cz\n"
                       f"#DnesMaSvatek #SvatekDnes #KdoMaDnesSvatek #SvatecniDen #Jmeniny "
                       f"#DenniSvatek #SvatekKazdyDen #CeskeJmeniny #SvatekVCesku #DnesSlavi")

        print("🚀 Odesílám album na Instagram...")
        post_album_to_instagram(image_paths, description)






if __name__ == "__main__":
    main()
    print("🔄 [main] Kontroluji zda jsou tu obrázky starší 7 dnů popřípadě je smažu...")
    delete_old_png_files()
