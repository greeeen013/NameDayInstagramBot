import tempfile
from PIL import Image
import json
import pyotp
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
from dotenv import load_dotenv
import os
from datetime import datetime, timezone
from pathlib import Path


def login():
    # Načtení přihlašovacích údajů z .env
    load_dotenv()
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    totp_secret = os.getenv("IG_2FA_SECRET")

    if not username or not password:
        raise ValueError("IG_USERNAME nebo IG_PASSWORD není nastaveno v .env souboru!")

    # Vytvoření klienta
    cl = Client()

    # Cesta k uložení session
    SESSION_FILE = "session.json"

    # Pokus o načtení session ze souboru
    try:
        if os.path.exists(SESSION_FILE):
            # Správný způsob načtení session
            cl.load_settings(SESSION_FILE)  # Předáváme cestu k souboru
            cl.login(username, password)
            print("✅ Přihlášeno pomocí uložené session!")
            return cl
    except (LoginRequired, json.JSONDecodeError) as e:
        print(f"⚠️ Session expirovala nebo je neplatná: {e}. Přihlašuji se znovu...")

    # Pokud session neexistuje nebo je neplatná, přihlásíme se znovu
    try:
        # Pokud je nastaven TOTP secret, vygenerujeme 2FA kód
        verification_code = None
        if totp_secret:
            totp_secret = totp_secret.replace(" ", "").strip()
            totp = pyotp.TOTP(totp_secret)
            verification_code = totp.now()
            print(f"🔐 Vygenerován 2FA kód: {verification_code}")

        # Přihlášení
        cl.login(
            username=username,
            password=password,
            verification_code=verification_code
        )

        # Uložení session do souboru
        cl.dump_settings(SESSION_FILE)

        print("✅ Úspěšně přihlášeno a session uložena!")
        return cl
    except ChallengeRequired as e:
        print(f"❌ Instagram vyžaduje dodatečné ověření: {e}")
        raise Exception("Je potřeba manuální ověření (např. SMS).")
    except Exception as e:
        print(f"❌ Chyba při přihlašování: {e}")
        raise


def has_posted_today():
    global cl  # Přidáme global, abychom mohli modifikovat klienta vytvořeného nahoře
    cl = login()  # Přihlásíme se a získáváme klienta

    # Získání user_id - přidáme kontrolu
    if not cl.user_id:
        raise ValueError("Nepodařilo se získat user_id po přihlášení")

    posts = cl.user_medias_v1(cl.user_id, amount=1)
    today = datetime.now(timezone.utc).date()

    for post in posts:
        if post.taken_at.date() == today:
            return True
    return False

def post_album_to_instagram(image_paths, description):
    """
    Přihlásí se a nahraje album nebo jeden obrázek na Instagram.
    Všechny obrázky převede na JPEG formát s rozměrem 1080x1080.
    """
    if has_posted_today():
        print("❌ [instagra_bot] Dnes už bylo něco nahráno.")
        return

    # Pokud image_paths není seznam (např. je to jen string), převedeme na seznam
    if isinstance(image_paths, (str, Path)):
        image_paths = [image_paths]

    converted_paths = []
    with tempfile.TemporaryDirectory() as tmpdirname:
        for i, img_path in enumerate(image_paths):
            img = Image.open(img_path).convert("RGB")
            img = img.resize((1080, 1080))
            output_path = Path(tmpdirname) / f"converted_{i}.jpg"
            img.save(output_path, "JPEG", quality=95)
            converted_paths.append(output_path)

        # Pokud je jen jeden obrázek, použij single upload
        if len(converted_paths) == 1:
            cl.photo_upload(converted_paths[0], caption=description)
            print("✔️ [instagra_bot] Fotka úspěšně nahrána!")
        else:
            cl.album_upload(converted_paths, caption=description)
            print("✔️ [instagra_bot] Album úspěšně nahráno!")


if __name__ == "__main__":
    # Příklad použití s více obrázky
    images = ["image1.png", "image2.png", "image3.png"]
    description = "Dnešní svátky 🎉\n\n#svatky #jmeniny #kalendar"

    post_album_to_instagram(images, description)