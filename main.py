from api_handler import generate_with_openrouter
from instagram_bot import post_album_to_instagram
from name_info import get_todays_names, get_name_info
from image_generator import generate_image_for
import os
from datetime import datetime, timedelta


def delete_old_png_files():
    # Path to the directory with images
    image_dir = 'output/obrazky'

    # Vypočítá 7 dní zpátky
    seven_days_ago = datetime.now() - timedelta(days=7)

    # zkontroluje zda složka existuje
    if not os.path.exists(image_dir):
        return

    # projede všechny soubory
    for filename in os.listdir(image_dir):
        if filename.lower().endswith('.png'):
            try:
                # zkusí vzít datum ze souboru (format YYYY-MM-DD*.png)
                date_str = filename[:10]  # Prvních 10 charakteru by mělo byt datum YYYY-MM-DD
                file_date = datetime.strptime(date_str, "%Y-%m-%d")

                # pokud je starší než 7 dní, smaže ho
                if file_date < seven_days_ago:
                    file_path = os.path.join(image_dir, filename)
                    os.remove(file_path)
                    print(f"🗑️ [main] Smazán starý obrázek: {filename}")
            except ValueError:
                # Skip files that don't match our date pattern
                continue

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

    print("🔄 [main] Kontroluji a mažu staré obrázky...")
    delete_old_png_files()

if __name__ == "__main__":
    main()
