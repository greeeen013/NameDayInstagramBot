from api_handler import generate_with_deepseek
from instagram_bot import post_album_to_instagram
from name_info import get_name_details, get_today_names_and_holidays, letter_map
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

def generate_name_prompt(names, names_info):
    newline = '\n'  # Definujeme si nový řádek předem

    name_details = []
    for name, info in zip(names, names_info):
        details = [
            f"Jméno: {name}",
            f"Původ: {info.get('origin', 'neznámý')}",
            f"Význam: {info.get('meaning', 'neuveden')}",
            f"Popularita: {info.get('rank', 'neuveden')}. místo",
            f"Průměrný věk nositelů: {info.get('avg_age', 'neuveden')} let",
            f"Počet nositelů: {info.get('count', 'neuveden')}"
        ]
        name_details.append(newline.join(details))  # Použijeme předdefinovaný newline

    names_list = ", ".join(names) if len(names) > 1 else names[0]
    number_agreement = "je" if len(names) == 1 else "jsou"

    separator = '-' * 50 + newline  # Vytvoříme separator s newline

    prompt = f"""
        Napiš Instagram post v češtině oslavující jméno {names_list} podle těchto pravidel:

        1. FORMÁT (žádné odsazení, jen odstavce):
        "Dnes slavíme {names_list}! [emoji]"

        [Prázdný řádek]

        [Odstavec o původu - s vtipem]
        [Prázdný řádek] 

        [Odstavec o významu - s vtipem]
        [Prázdný řádek]

        [Odstavec o osobnostech - 1-2 věty s emoji]
        [Prázdný řádek]

        "Tak co, znáte nějakého/nějakou {names_list}? Označte ho/ji v komentářích a popřejte mu/jí parádní oslavu! 🎂🥂"

        2. SPECIFICKÉ POKYNY PRO ZDEŇKU:
        - Jméno Zdeňka je ŽENSKÉ, používej výhradně ženské tvary
        - I když jméno vypadá podobně jako mužské Zdeněk, vždy používej ženské skloňování
        - Správné tvary: "oslavujeme Zdeňku", "popřejte jí", "znáte nějakou Zdeňku"

        3. PŘÍKLAD SPRÁVNÉHO VÝSTUPU:
        Dnes slavíme Zdeňku! 🌸

        Zdeňka má slovanský původ - stejně jako její "bratr" Zdeněk, ale na rozdíl od něj nosí jméno s něžnou příponou -ka. 

        Jméno Zdeňka znamená "ta, která přináší slávu". Takže pokud ještě nejste slavné, Zdeňky, máte to doslova v popisu práce! ✨

        Zdeňka Žádníková-Volková je česká herečka, která dokazuje, že ženy se jménem Zdeňka umí zazářit na jevišti i ve filmu. 🎭

        Tak co, znáte nějakou Zdeňku? Označte ji v komentářích a popřejte jí parádní oslavu! 🎂🥂

        4. DŮLEŽITÉ:
        - Žádné tagy ani jiné technické poznámky
        - Pouze čistý výstup ve formátu Instagram postu
        - Musí být přirozený, vtipný a vhodný pro české publikum
        - Musí určit správný rod pro to jméno
    """
    return prompt

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

    if names:
        print("🎨 Generuji obrázky pro jména...")
        names_info = []
        for name in names:
            info = get_name_details(name, letter_map)
            img_path = generate_image_for(name, info)
            if img_path:
                image_paths.append(img_path)
                names_info.append(info)

        prompt = generate_name_prompt(names, names_info)

    else:
        print("ℹ️ Žádné jméno dnes neslaví. Kontroluji státní svátky...")
        names, holidays = get_today_names_and_holidays()

        if not holidays:
            print("❌ Dnes není žádný svátek ani jmeniny.")
            return

        holiday = holidays[0]  # bereme první svátek, pokud jich je více
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
    ai_response = generate_with_deepseek(prompt)
    print(ai_response)
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
            translated = generate_with_deepseek("Přelož následující text z angličtiny do češtiny a uprav jej jako stručný instagramový popisek."
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
            print(translated)

    # 📝 Připrav finální popis
    sources =("\nKdo má svátek je z: kalendar.beda.cz \nStatistiky jsou z: nasejmena.cz \nZdroj obrázku: NASA Astronomy Picture of the Day (APOD)")
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
