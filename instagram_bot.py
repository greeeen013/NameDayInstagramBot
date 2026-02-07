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
DEVICE_SETTINGS_FILE = BASE_DIR / "device.json"


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
    
    # 1. Načtení nebo vytvoření fixního zařízení (aby se neměnilo UUID při každém smazání session)
    if DEVICE_SETTINGS_FILE.exists():
        try:
            device_settings = json.loads(DEVICE_SETTINGS_FILE.read_text())
            cl.set_device(device_settings)
            print(f"📱 Načteno uložené zařízení: {DEVICE_SETTINGS_FILE}")
        except Exception as e:
             print(f"⚠️ Chyba při načítání device.json: {e}. Generuji nové.")
             cl.set_device({"app_version": "269.0.0.18.75", "android_version": 26, "android_release": "8.0.0", "dpi": "480dpi", "resolution": "1080x1920", "manufacturer": "OnePlus", "device": "OnePlus6", "model": "ONEPLUS A6003", "cpu": "qcom", "version_code": "314665256"})
             DEVICE_SETTINGS_FILE.write_text(json.dumps(cl.device_settings, indent=4))
    else:
        print("📱 Generuji nové zařízení a ukládám do device.json...")
        # Instagrapi generuje random device při initu, stačí ho uložit
        DEVICE_SETTINGS_FILE.write_text(json.dumps(cl.get_settings()["device_settings"], indent=4))

    if SESSION_FILE.exists():
        try:
            cl.load_settings(str(SESSION_FILE))
            settings = cl.get_settings()
            # Re-apply device and user_agent (zajistíme, že se nepřeepsalo něčím starým ze session)
            if DEVICE_SETTINGS_FILE.exists():
                 device_settings = json.loads(DEVICE_SETTINGS_FILE.read_text())
                 cl.set_device(device_settings)
            
            cl.login(username, password)
            cl.inject_sessionid_to_public()
            print(f"✅ Přihlášeno pomocí uložené session: {SESSION_FILE}")
            return cl
        except (LoginRequired, json.JSONDecodeError, Exception) as e:
            print(f"⚠️ Session vypršela: {e}")
            # Smažte starou session
            if SESSION_FILE.exists():
                SESSION_FILE.unlink()

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
        print(f"⚠️ Instagram vyžaduje challenge (např. SMS/Email). Pokouším se o automatické řešení...")
        try:
            cl.challenge_resolve(cl.last_json)
            print("✅ Challenge úspěšně vyřešena!")
            cl.dump_settings(str(SESSION_FILE))
            cl.inject_sessionid_to_public()
            return cl
        except Exception as resolve_error:
            print(f"❌ Nepodařilo se vyřešit challenge: {resolve_error}")
            raise e
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
    Přihlásí se, předzpracuje obrázky a nahraje fotku nebo album.
    Obsahuje retry logiku pro případ ChallengeRequired (neplatná session).
    """
    max_attempts = 3
    
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"🔄 [insta_bot] Pokus o operaci {attempt}/{max_attempts}...")
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
            
            # Pokud vše proběhne bez chyby, ukončíme cyklus
            return

        except ChallengeRequired:
            print(f"⚠️ [insta_bot] Detekována ChallengeRequired (pokus {attempt}/{max_attempts}).")
            print("🛑 Mažu poškozenou session, device a zkusím to znovu...")
            
            if SESSION_FILE.exists():
                SESSION_FILE.unlink()
                print(f"🗑️ [insta_bot] Smazáno: {SESSION_FILE}")

            # Smažeme i device.json, aby se vygenerovalo nové zařízení (pomáhá při smyčce challenge)
            if DEVICE_SETTINGS_FILE.exists():
                DEVICE_SETTINGS_FILE.unlink()
                print(f"🗑️ [insta_bot] Smazáno: {DEVICE_SETTINGS_FILE}")
            
            if attempt == max_attempts:
                print("❌ [insta_bot] Vyčerpány všechny pokusy o obnovu session. Končím.")
                raise
            
            # Delší pauza před dalším pokusem
            wait_time = random.uniform(20, 60)
            print(f"⏳ Čekám {int(wait_time)}s před dalším pokusem...")
            time.sleep(wait_time)
        
        except Exception as e:
            print(f"❌ [insta_bot] Neočekávaná chyba: {e}")
            raise


if __name__ == "__main__":
    images = ["image1.png", "image2.png", "image3.png"]
    desc = "Dnešní svátky 🎉\n\n#svatky #jmeniny #kalendar"
    print("🚀 [main] Odesílám toto album na Instagram:..")
    print(f"📋 [main] {images}")
    post_album_to_instagram(images, desc)
