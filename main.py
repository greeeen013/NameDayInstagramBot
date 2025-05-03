from instagram_bot import post_album_to_instagram
from datetime import date
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
        print(f"🔄 Generuji obrázek pro: {name}")
        info = get_name_info(name)
        img_path = generate_image_for(name, info)
        print(f"   ✔️ Obrázek uložen jako: {img_path}")
        image_paths.append(img_path)

    description = f"Dnešní obrázky: {date.today().strftime('%d.%m.%Y')}"
    print("🚀 Odesílám album na Instagram...")
    print(image_paths)
    post_album_to_instagram(image_paths, description)
    print("✔️ Album úspěšně nahráno!")


if __name__ == "__main__":
    main()
