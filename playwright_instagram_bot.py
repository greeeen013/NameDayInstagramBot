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

    browser = playwright.chromium.launch(
        headless=headless,
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(
        locale="cs-CZ",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = context.new_page()
    try:
        print("🌍 [playwright] Přecházím na login stránku...")
        page.goto("https://www.instagram.com/accounts/login/")
        page.wait_for_timeout(3000) # Počká 3 vteřiny než se stránka plně renderovat
        
        try:
            print("🍪 [playwright] Zkouším odkliknout cookies...")
            page.locator("button:has-text('Allow all cookies'), button:has-text('Povolit všechny soubory cookie'), button:has-text('Povolit všechny')").first.click(timeout=5000)
        except:
            print("🍪 [playwright] Cookies banner nenalezen nebo timeout, pokračuji...")
            
        print("🔐 [playwright] Vyplňuji přihlašovací údaje...")
        try:
            page.get_by_label("Mobile number, username or email").click()
            page.get_by_label("Mobile number, username or email").fill(username)
            page.get_by_label("Password").click()
            page.get_by_label("Password").fill(password)
        except:
            page.get_by_label("Číslo mobilu, uživatelské jméno nebo e-mail").click()
            page.get_by_label("Číslo mobilu, uživatelské jméno nebo e-mail").fill(username)
            page.get_by_label("Heslo").click()
            page.get_by_label("Heslo").fill(password)
        
        print("🔐 [playwright] Klikám na Log in / Odesílám formulář...")
        try:
            page.get_by_label("Password", exact=True).press("Enter")
        except:
            try:
                page.get_by_label("Heslo", exact=True).press("Enter")
            except:
                page.locator('button[type="submit"]').first.click()

        print("⏳ [playwright] Čekám na validaci přihlašovacích údajů...")
        page.wait_for_timeout(5000)
            
        print("⏳ [playwright] Čekám, jestli se objeví 2FA ověření...")
        try:
            page.wait_for_selector('input[name="verificationCode"]', timeout=15000)
            if totp_secret:
                print("🔐 [playwright] Bylo vyžadováno 2FA. Generuji kód...")
                totp = pyotp.TOTP(totp_secret.replace(" ", ""))
                code = two_factor_code if two_factor_code else totp.now()
                page.locator('input[name="verificationCode"]').fill(code)
                print(f"🔑 [playwright] Zadán kód: {code}. Potvrzuji...")
                page.locator('button[type="button"], button[type="submit"]').first.click()
                page.wait_for_timeout(5000)
            else:
                print("❌ [playwright] Bylo vyžadováno 2FA, ale v .env není IG_2FA_SECRET. Skript počká 30 vteřin pro manuální zadání.")
                page.wait_for_timeout(30000)
        except:
            print("✅ [playwright] 2FA nebylo vyžadováno nebo se kódové pole neukázalo, pokračuji dál...")
             
        try:
            print("💾 [playwright] Zkouším odkliknout Save info...")
            page.locator('button:has-text("Save info"), button:has-text("Uložit údaje")').first.click(timeout=10000)
        except:
            pass

        print("⏭️ [playwright] Odklikávám vyskakovací okna po přihlášení...")
        try:
            page.locator('button:has-text("Not Now"), button:has-text("Teď ne"), text="Not Now", text="Teď ne"').first.click(timeout=5000)
        except:
            pass

        print("📸 [playwright] Začínám proces nahrávání fotky...")
        try:
            page.locator('svg[aria-label="Nový příspěvek"], svg[aria-label="New post"]').first.click(timeout=10000)
        except:
            print("  ➡️ Fallback na text/xpath...")
            page.locator('xpath=//svg[@aria-label="Nový příspěvek" or @aria-label="New post"]').first.click()
        
        try:
            page.locator('text="Post", text="Příspěvek"').first.click(timeout=5000)
        except:
            pass
        
        print("📁 [playwright] Klikám na výběr souborů...")
        page.wait_for_timeout(2000)
        with page.expect_file_chooser() as fc_info:
            try:
                page.get_by_role("button", name="Vybrat z počítače").click(timeout=5000)
            except:
                try:
                    page.get_by_role("button", name="Select From Computer").click(timeout=5000)
                except:
                    page.locator('text="Vybrat z počítače", text="Select From Computer"').first.click(timeout=5000)
                    
        file_chooser = fc_info.value
        file_chooser.set_files(images)
        print(f"✅ [playwright] Soubory vloženy: {images}")

        print("➡️ [playwright] Čekám delší dobu na zpracování plátna v headless mode...")
        page.wait_for_timeout(10000)
        
        print("➡️ [playwright] Klikám na Další / Next (ořezávání)...")
        try:
            page.get_by_text("Další", exact=True).first.click(timeout=10000)
        except:
            page.get_by_text("Next", exact=True).first.click(timeout=10000)

        print("➡️ [playwright] Klikám na Další / Next (filtry)...")
        page.wait_for_timeout(3000)
        try:
            page.get_by_text("Další", exact=True).first.click(timeout=10000)
        except:
            page.get_by_text("Next", exact=True).first.click(timeout=10000)

        print("📝 [playwright] Vyplňuji popisek...")
        page.wait_for_timeout(3000)
        caption_box = page.locator('div[aria-label="Napište popisek..."], div[aria-label="Write a caption..."]').first
        caption_box.click(timeout=10000)
        caption_box.fill(caption)

        print("🚀 [playwright] Klikám na Sdílet / Share...")
        page.wait_for_timeout(3000)
        page.locator('div[role="button"]:text-is("Sdílet"), div[role="button"]:text-is("Share")').first.click(timeout=10000, force=True)
        
        print("⏳ [playwright] Čekám na dokončení nahrávání...")
        page.wait_for_timeout(15000)
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
