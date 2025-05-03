import tempfile
from PIL import Image

from instagrapi import Client
from dotenv import load_dotenv
import os
from datetime import datetime, timezone
from pathlib import Path

load_dotenv()

IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

cl = Client()


def login():
    if not IG_USERNAME or not IG_PASSWORD:
        raise ValueError("Instagram login credentials not found in .env file")
    cl.login(IG_USERNAME, IG_PASSWORD)


def has_posted_today():
    login()
    posts = cl.user_medias_v1(cl.user_id, amount=1)

    today = datetime.now(timezone.utc).date()

    for post in posts:
        if post.taken_at.date() == today:
            return True
    return False

def post_album_to_instagram(image_paths, description):
    """
    Přihlásí se a nahraje album na Instagram.
    Všechny obrázky převede na JPEG formát s rozměrem 1080x1080.
    """
    if has_posted_today():
        print("❌ [instagra_bot] Dnes už bylo něco nahráno.")
        return

    converted_paths = []
    with tempfile.TemporaryDirectory() as tmpdirname:
        for i, img_path in enumerate(image_paths):
            # Otevření původního obrázku
            img = Image.open(img_path).convert("RGB")
            # Úprava velikosti na 1080x1080 (čtverec, doporučeno pro IG)
            img = img.resize((1080, 1080))
            # Uložení dočasného JPEG souboru
            output_path = Path(tmpdirname) / f"converted_{i}.jpg"
            img.save(output_path, "JPEG", quality=95)
            converted_paths.append(output_path)

        # Nahrání převedených obrázků jako album
        cl.album_upload(converted_paths, description)
        print("✔️ [instagra_bot] Album úspěšně nahráno!")


if __name__ == "__main__":
    # Příklad použití s více obrázky
    images = ["image1.png", "image2.png", "image3.png"]
    description = "Dnešní svátky 🎉\n\n#svatky #jmeniny #kalendar"

    post_album_to_instagram(images, description)