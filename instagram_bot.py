import os
import time
import random
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from PIL import Image
import json
import pyotp
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired, PleaseWaitFewMinutes

BASE_DIR = Path(__file__).resolve().parent
SESSION_FILE = BASE_DIR / "session.json"


def _upload_with_retry(func, *args, max_retries=3):
    """
    Retries uploads on PleaseWaitFewMinutes with incremental backoff.
    """
    for attempt in range(1, max_retries + 1):
        try:
            return func(*args)
        except PleaseWaitFewMinutes as e:
            wait = random.uniform(30, 60) * attempt
            print(f"⚠️ Rate limited on upload (attempt {attempt}/{max_retries}): {e}. Sleeping {int(wait)}s...")
            time.sleep(wait)
    raise Exception("❌ Max retries reached, upload failed.")

def login():
    load_dotenv()
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    totp_secret = os.getenv("IG_2FA_SECRET")

    if not username or not password:
        raise ValueError("IG_USERNAME nebo IG_PASSWORD není nastaveno v .env!")

    cl = Client()

    if SESSION_FILE.exists():
        try:
            cl.load_settings(str(SESSION_FILE))
            settings = cl.get_settings()
            # Re-apply device and user_agent
            cl.set_device(settings["device_settings"])
            cl.set_user_agent(settings["user_agent"])
            cl.login(username, password)
            cl.inject_sessionid_to_public()
            print(f"✅ Přihlášeno pomocí uložené session: {SESSION_FILE}")
            return cl
        except (LoginRequired, json.JSONDecodeError):
            print("⚠️ Platnost session skončila, přihlašuji znovu...")

    try:
        code = None
        if totp_secret:
            totp_secret = totp_secret.strip().replace(" ", "")
            code = pyotp.TOTP(totp_secret).now()
            print(f"🔐 Vygenerován 2FA kód: {code}")

        cl.login(username, password, verification_code=code)
        cl.dump_settings(str(SESSION_FILE))
        cl.inject_sessionid_to_public()
        print(f"✅ Úspěšně přihlášeno a session uložena: {SESSION_FILE}")
        return cl

    except ChallengeRequired as e:
        print(f"❌ Instagram vyžaduje další ověření: {e}")
        raise
    except Exception as e:
        print(f"❌ Chyba při přihlášení: {e}")
        raise

def has_posted_today(cl: Client, max_retries=3) -> bool:
    """Check if user has posted today, with retry on rate limit."""
    if not cl.user_id:
        raise ValueError("Nepodařilo se získat user_id po přihlášení")
    for attempt in range(1, max_retries + 1):
        try:
            posts = cl.user_medias_v1(cl.user_id, amount=1)
            break
        except PleaseWaitFewMinutes as e:
            wait = random.uniform(20, 40) * attempt
            print(f"⚠️ Rate limited on has_posted_today (attempt {attempt}/{max_retries}): {e}. Sleeping {int(wait)}s...")
            time.sleep(wait)
    else:
        print("⚠️ Nelze ověřit poslední post; předpokládám, že dnes nic nebylo.")
        return False

    today = datetime.now(timezone.utc).date()
    return any(p.taken_at.date() == today for p in posts)


def post_album_to_instagram(image_paths, description):
    """
    Přihlásí se, předzpracuje obrázky a nahraje fotku nebo album s retry logikou.
    """
    cl = login()

    if has_posted_today(cl):
        print("❌ [insta_bot] Dnes už bylo něco nahráno.")
        return

    if isinstance(image_paths, (str, Path)):
        image_paths = [image_paths]

    converted = []
    output_dir = BASE_DIR / "output"
    output_dir.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        for idx, path in enumerate(image_paths):
            img = Image.open(path).convert("RGB").resize((1080, 1080))
            out = output_dir / f"img_{idx}.jpg"
            img.save(out, "JPEG", quality=95)
            converted.append(out)

        # Small delay before upload
        time.sleep(random.uniform(5, 10))

        if len(converted) == 1:
            _upload_with_retry(cl.photo_upload, converted[0], description)
            print("✔️ [insta_bot] Fotka úspěšně nahrána!")
        else:
            _upload_with_retry(cl.album_upload, converted, description)
            print("✔️ [insta_bot] Album úspěšně nahráno!")


if __name__ == "__main__":
    images = ["image1.png", "image2.png", "image3.png"]
    desc = "Dnešní svátky 🎉\n\n#svatky #jmeniny #kalendar"
    print("🚀 [main] Odesílám toto album na Instagram:..")
    print(f"📋 [main] {images}")
    post_album_to_instagram(images, desc)
