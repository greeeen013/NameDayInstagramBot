import os
from dotenv import load_dotenv
from playwright_instagram_bot import post_to_instagram

load_dotenv()
username = os.getenv("IG_USERNAME")
password = os.getenv("IG_PASSWORD")

if not username or not password:
    print("❌ Chybí přihlašovací údaje (IG_USERNAME nebo IG_PASSWORD v .env)!")
    exit(1)

print("🚀 [test_playwright] Spouštím záložní Playwright skript...")
try:
    # `post_to_instagram` očekává list obrázků, popisek a 2FA kód
    # Zadejte reálnou cestu k obrázku (nemusí existovat pro test samotného přihlášení, 
    # ale Playwright tam spadne, pokud se k němu dostane)
    test_image = "test_image.jpg"
    test_caption = "Testování Playwright nahrávání! 🤖"
    
    post_to_instagram(images=[test_image], caption=test_caption, two_factor_code=None, headless=False)
    print("✅ [test_playwright] Skript doběhl bez pádu.")
except Exception as e:
    print(f"❌ [test_playwright] Skript spadl: {e}")
    print("Pokud to spadlo na Timeout 30000ms, zkontrolujte vygenerované soubory:")
    print(" - playwright_debug_login_init.png")
    print(" - playwright_debug_login_init.html")
