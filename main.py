from api_handler import generate_with_openrouter
from instagram_bot import post_album_to_instagram
from name_info import get_todays_names, get_name_info
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
    image_dir = 'output/obrazky'

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
                print(f"📆 [main_delete_old_png_files] Zkouším rozpoznat datum z: '{date_str}'")

                file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                print(f"🗓️ [main_delete_old_png_files] Úspěšně rozpoznáno datum: {file_date}")

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
    2) Pro každé jméno získá informace a vygeneruje obrázek.
    3) Nahraje všechny obrázky jako album na Instagram s popiskem.
    """
    print("🍀 Načítám dnešní sváteční jména...")
    names = get_todays_names()
    if not names:
        print("ℹ️ Žádné sváteční jméno pro dnešek. Ukončuji.")
        return

    image_paths = []
    for name in names:
        print(f"🔄 [main] Generuji obrázek pro: {name}")
        info = get_name_info(name)
        img_path = generate_image_for(name, info)
        print(f"   ✔️ [main] Obrázek uložen jako: {img_path}")
        image_paths.append(img_path)

    print("🔄 [main] Generuji AI popis pro Instagram...")
    info = get_name_info(names[0])
    prompt = (
        f"Napiš kreativní, vtipný a energický popisek na Instagram v češtině, který oslavuje svátek těchto jmen: {names}. "
        f"POZOR – pokud je jméno jen jedno, piš výhradně v jednotném čísle ('Oslava svátku pro Květoslava je tady!'), "
        f"pokud je jmen víc, piš v množném čísle ('Oslava svátku pro Alexeje a Květoslava je tady!'). "
        f"Jména spoj správně ve 2. pádě, nesmí se opakovat ani být v nominativu. "
        f"Začni hlavní větou stylu: 🎉 Oslava svátku pro Alexeje a Alexe je tady! 🎉 – nebo podobně výraznou oslavnou větou s emojis. "
        f"Na druhý řádek napiš odlehčené a zábavné přání těmto jménům – mluv ke jménům jako k osobnostem, ne k lidem. "
        f"Na třetí řádek nenuceně zakomponuj původ jména, použij hodnotu {info['origin']} a formuluj to s nadsázkou."
        f"Na čtvrtý řádek přidej odlehčenou zmínku o známých nebo historických nositelích těchto jmen – zmiň že se jedná o historická jména."
        f"Na pátý řádek přidej co se dnes slaví za den jako třeba den koček nebo den bez mobilu, nebo něco podobného. "
        f"Na závěr přidej výzvu k akci, např. 'Tak co, znáte nějakého TY JMENA (ve 2. pádě), tak ho označte do komentářů a popřejte jim/nebo mu pokud se jedna o jedno jmeno! 🎂'. "
        f"Celý výstup piš uvolněně, s lehkým humorem, bohatě používej emojis a piš jako popisek na sociální sítě. Nepřej konkrétním osobám, ale těm jménům samotným. "
        f"Text musí být poutavý, zábavný, stylový – žádná suchá fakta, ale lehká forma infotainmentu. "
    )

    ai_response = generate_with_openrouter(prompt)
    if ai_response:
        print("Generated description:")
        print(ai_response)
    else:
        ai_response = "Dnes má svátek " +{names}+"."
        print("Failed to generate description")
    description = ai_response+(f"\n\n\n."
                                  f"informace jsou z: czso.cz a nasejmena.cz\n"
                                  f"#DnesMáSvátek #SvátekDnes #KdoMáDnesSvátek #SvátečníDen #Jmeniny #DenníSvátek #SvátekKaždýDen #ČeskéJmeniny #SvátekVČesku #DnesSlaví #KaždýDen #DenníPost #Zajímavosti #PůvodJména #JménoDne #JmennéZajímavosti #PoznejJména"
                                  f"#českýinstagram #postdne #inspirace #czsk #czechinstagram #dnes")
    print("🚀 [main] Odesílám album na Instagram...")
    print(image_paths)
    post_album_to_instagram(image_paths, description)

    print("🔄 [main] Kontroluji zda jsou tu obrázky starší 7 dnů popřípadě je smažu...")


if __name__ == "__main__":
    delete_old_png_files()
