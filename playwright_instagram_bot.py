import re
import os
from playwright.sync_api import Playwright, sync_playwright, expect
from dotenv import load_dotenv
import pyotp

def run(playwright: Playwright, images: list, caption: str, two_factor_code: str, headless: bool = True) -> None:
    load_dotenv()
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    totp_secret = os.getenv("IG_2FA_SECRET")

    browser = playwright.chromium.launch(headless=headless)
    context = browser.new_context()
    page = context.new_page()
    try:
        print("🌍 [playwright] Přecházím na login stránku...")
        page.goto("https://www.instagram.com/accounts/login/")
        page.wait_for_load_state("networkidle")

        print("🍪 [playwright] Zkouším odkliknout cookies...")
        try:
            page.get_by_role("button", name="Allow all cookies").click(timeout=5000)
        except Exception:
            print("  ➡️ Cookies dialog nenalezen nebo nevyžadován.")

        print("🔐 [playwright] Vyplňuji přihlašovací údaje...")
        page.get_by_role("textbox", name="Mobile number, username or").click()
        page.get_by_role("textbox", name="Mobile number, username or").fill(username)
        page.get_by_role("textbox", name="Password").click()
        page.get_by_role("textbox", name="Password").fill(password)
        page.get_by_role("button", name="Log in", exact=True).click()
        
        # Počkáme na načtení po loginu
        page.wait_for_timeout(5000)

        # 2FA
        # 2FA
        if totp_secret:
            try:
                print("🔐 [playwright] Detekován 2FA, zkouším zadat kód...")
                totp = pyotp.TOTP(totp_secret)
                code = two_factor_code if two_factor_code else totp.now()
                page.get_by_role("textbox", name="Security code").click(timeout=5000)
                page.get_by_role("textbox", name="Security code").fill(code)
                page.get_by_role("button", name="Confirm").click()
                page.wait_for_timeout(5000)
            except Exception as e:
                print(f"  ➡️ 2FA pole nenalezeno nebo nastala chyba: {e}")

        # Odkliknutí "Not Now" dialogů
        print("⏭️ [playwright] Odklikávám vyskakovací okna po přihlášení...")
        try:
            page.get_by_role("button", name="Not now").click(timeout=5000)
        except Exception:
            pass
        try:
            page.get_by_role("button", name="Not Now").click(timeout=5000)
        except Exception:
            pass

        # Vytvoření příspěvku
        print("📸 [playwright] Začínám proces nahrávání fotky...")
        page.get_by_role("link", name="New post Create").click()
        try:
            page.get_by_role("link", name="Post Post").click(timeout=3000)
        except Exception:
            pass
        
        # Výběr souboru
        page.wait_for_timeout(2000)
        with page.expect_file_chooser() as fc_info:
            page.get_by_role("button", name="Select From Computer").click()
        file_chooser = fc_info.value
        file_chooser.set_files(images)
        print(f"✅ [playwright] Soubory vloženy: {images}")

        # Další kroky
        page.wait_for_timeout(2000)
        page.get_by_role("button", name="Next").click()
        page.wait_for_timeout(2000)
        page.get_by_role("button", name="Next").click()

        # Vyplnění popisku
        print("📝 [playwright] Vyplňuji popisek...")
        page.wait_for_timeout(2000)
        page.get_by_role("textbox", name="Write a caption...").click()
        page.get_by_role("textbox", name="Write a caption...").fill(caption)

        # Sdílení
        print("🚀 [playwright] Klikám na Share...")
        page.get_by_role("button", name="Share").click()
        
        print("⏳ [playwright] Čekám na dokončení nahrávání...")
        page.wait_for_timeout(10000)
        print("✅ [playwright] Příspěvek by měl být úspěšně publikován.")
    except Exception as e:
        print(f"❌ [playwright] Chyba během playwright skriptu: {e}")
        try:
            screenshot_path = "playwright_debug_error.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 Screenshot uložen jako {screenshot_path}")
        except Exception as screenshot_e:
            print(f"⚠️ Nelze vytvořit screenshot: {screenshot_e}")
        raise
    finally:
        # ---------------------
        context.close()
        browser.close()


def post_to_instagram(images: list, caption: str, two_factor_code: str, headless: bool = True) -> None:
    with sync_playwright() as playwright:
        run(playwright, images, caption, two_factor_code, headless=headless)
