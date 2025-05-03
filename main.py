from api_handler import generate_with_openrouter
from instagram_bot import post_album_to_instagram
from name_info import get_todays_names, get_name_info
from image_generator import generate_image_for


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
        f"Napiš kreativní, vtipný a energický popisek na Instagram v češtině, který oslavuje svátek jmen uvedených v seznamu: {name}. "
        f"Všechna jména jsou česká a mužská – i když některá mohou znít mezinárodně (např. Alex). "
        f"(V textu použij jejich tvary ve 2. pádě – NA TO POZOR!, např. 'Alexeje a Alexe'). "
        f"Začni hlavní větou stylu: 🎉 Oslava svátku pro Alexeje a Alexe je tady! 🎉 – nebo podobně výraznou oslavnou větou s emojis. "
        f"Na druhý řádek napiš odlehčené a zábavné přání těmto jménům – mluv ke jménům jako k osobnostem, ne k lidem. "
        f"Na třetí řádek nenuceně zakomponuj původ jména, použij hodnotu {info['origin']} a formuluj to s nadsázkou nebo stylem 'No jo, tohle jméno má kořeny až v...'. "
        f"Na čtvrtý řádek přidej odlehčenou zmínku o známých nebo historických nositelích těchto jmen – klidně uhoď nějaký vtípek. "
        f"Na pátý řádek (nepovinně) přidej etymologii, pokud ji znáš – formou bonusové zajímavosti, třeba: 💡 Fun fact: jméno = co to znamená. "
        f"Na závěr přidej výzvu k akci, např. 'Tak co, znáte nějakého {name} (ve 2. pádě), tak ho označte do komentářů! 🎂'. "
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
    description = ai_response+(f"\n\n."
                                  f"."
                                  f"."
                                  f"."
                                  f"."
                                  f"informace jsou z: nasejmena.cz"
                                  f"#DnesMáSvátek #SvátekDnes #KdoMáDnesSvátek #SvátečníDen #Jmeniny #DenníSvátek #SvátekKaždýDen #ČeskéJmeniny #SvátekVČesku #DnesSlaví #KaždýDen #DenníPost #Zajímavosti #PůvodJména #JménoDne #JmennéZajímavosti #PoznejJména"
                                  f"#českýinstagram #postdne #inspirace #czsk #czechinstagram #dnes")
    print("🚀 [main] Odesílám album na Instagram...")
    print(image_paths)
    post_album_to_instagram(image_paths, description)



if __name__ == "__main__":
    main()
