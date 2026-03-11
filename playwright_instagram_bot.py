import re
import os
from playwright.sync_api import Playwright, sync_playwright, expect
from dotenv import load_dotenv
import pyotp

def run(playwright: Playwright, images: list, caption: str, two_factor_code: str) -> None:
    load_dotenv()
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    totp_secret = os.getenv("IG_2FA_SECRET")

    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    try:
        print("🌍 [playwright] Přecházím na login stránku...")
        page.goto("https://www.instagram.com/accounts/login/")
        page.wait_for_timeout(3000) # Počká 3 vteřiny
        
        try:
            print("🍪 [playwright] Zkouším odkliknout cookies...")
            page.locator("button:has-text('Allow all cookies'), button:has-text('Povolit všechny soubory cookie'), button:has-text('Povolit všechny')").first.click(timeout=5000)
        except:
            print("🍪 [playwright] Cookies banner nenalezen nebo timeout, pokračuji...")
            
        print("🔐 [playwright] Vyplňuji přihlašovací údaje...")
        page.get_by_label("Číslo mobilu, uživatelské jméno nebo e-mail").click()
        page.get_by_label("Číslo mobilu, uživatelské jméno nebo e-mail").fill(username)
        page.get_by_label("Heslo").click()
        page.get_by_label("Heslo").fill(password)
        print("🔐 [playwright] Klikám na Log in / Odesílám formulář...")
        try:
            page.get_by_label("Heslo").press("Enter")
        except:
            page.locator("text='Přihlásit se'").first.click()
            
        print("⏳ [playwright] Čekám, jestli se objeví 2FA ověření...")
        try:
            # Zkusíme počkat na pole pro ověřovací kód (max 8 vteřin)
            page.wait_for_selector('input[name="verificationCode"]', timeout=8000)
            if totp_secret:
                print("🔐 [playwright] Bylo vyžadováno 2FA. Generuji kód z IG_2FA_SECRET...")
                totp = pyotp.TOTP(totp_secret.replace(" ", ""))
                code = totp.now()
                page.locator('input[name="verificationCode"]').fill(code)
                print(f"🔑 [playwright] Zadán kód: {code}. Potvrzuji...")
                page.locator('button:has-text("Potvrdit")').first.click()
                page.wait_for_timeout(5000)
            elif two_factor_code:
                print("🔐 [playwright] Bylo vyžadováno 2FA. Používám kód z parametru two_factor_code...")
                page.locator('input[name="verificationCode"]').fill(two_factor_code)
                page.locator('button:has-text("Potvrdit")').first.click()
                page.wait_for_timeout(5000)
            else:
                print("❌ [playwright] Bylo vyžadováno 2FA, ale nemám kód. Skript počká 30 vteřin pro manuální zadání.")
                page.wait_for_timeout(30000)
        except:
            print("✅ [playwright] 2FA nebylo vyžadováno nebo se neukázalo pole pro kód, pokračuji dál...")

        try:
            print("💾 [playwright] Zkouším odkliknout Save info...")
            page.get_by_role("button", name="Save info").click(timeout=10000)
        except:
            pass

        try:
            print("➕ [playwright] Klikám na Nový příspěvek (Create)...")
            page.locator('svg[aria-label="Nový příspěvek"], svg[aria-label="New post"]').first.click(timeout=15000)
        except:
             print("➕ [playwright] Fallback klikám na Nový příspěvek textem...")
             page.locator("text='Nový příspěvek'").first.click()
             
        try:
            print("➕ [playwright] Klikám na Příspěvek / Post v podmenu (pokud existuje)...")
            page.locator("span:has-text('Příspěvek'), span:has-text('Post')").first.click(timeout=5000)
        except:
            print("➕ [playwright] Podmenu se neukázalo, asi to skočilo rovnou na výběr fotky...")
        
        print("📁 [playwright] Vybírám soubory...")
        # Počkáme trochu na zobrazení modalu pro výběr fotky
        page.wait_for_timeout(2000)
        
        with page.expect_file_chooser() as fc_info:
            page.locator("button:has-text('Vybrat z počítače'), button:has-text('Select From Computer')").first.click()
        file_chooser = fc_info.value
        file_chooser.set_files(images)
        
        print("⏭️ [playwright] Klikám Další/Next 1...")
        page.locator("button:has-text('Další'), div[role='button']:has-text('Další'), div[role='button']:has-text('Next'), button:has-text('Next')").first.click()
        page.wait_for_timeout(2000)

        print("⏭️ [playwright] Klikám Další/Next 2...")
        page.locator("button:has-text('Další'), div[role='button']:has-text('Další'), div[role='button']:has-text('Next'), button:has-text('Next')").first.click()
        page.wait_for_timeout(2000)
        
        print("📝 [playwright] Vyplňuji popisek...")
        page.locator('div[role="textbox"]').first.click()
        page.locator('div[role="textbox"]').first.fill(caption)
        
        print("🚀 [playwright] Klikám na Sdílet/Share...")
        page.locator("button:has-text('Sdílet'), div[role='button']:has-text('Sdílet'), div[role='button']:has-text('Share'), button:has-text('Share')").first.click()
        
        print("✅ [playwright] Post shared successfully (hopefully)!")
        
        # Wait a bit to ensure upload finishes
        page.wait_for_timeout(10000)
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


def post_to_instagram(images: list, caption: str, two_factor_code: str) -> None:
    with sync_playwright() as playwright:
        run(playwright, images, caption, two_factor_code)
