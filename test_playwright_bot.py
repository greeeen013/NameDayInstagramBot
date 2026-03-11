import os
import time
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import pyotp

def test_playwright_flow():
    print("🛠️ Začínám testovací Playwright skript...")
    load_dotenv()
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    totp_secret = os.getenv("IG_2FA_SECRET")

    if not username or not password:
        print("❌ Chyba: Přihlašovací údaje IG_USERNAME a IG_PASSWORD nenalezeny v .env souboru.")
        return

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            print("🌍 Přecházím na login stránku...")
            page.goto("https://www.instagram.com/accounts/login/")
            page.wait_for_timeout(3000) # Počká 3 vteřiny než se stránka plně renderovat
            
            try:
                print("🍪 Zkouším odkliknout cookies...")
                page.locator("button:has-text('Allow all cookies'), button:has-text('Povolit všechny soubory cookie'), button:has-text('Povolit všechny')").first.click(timeout=5000)
            except:
                print("🍪 Cookies banner nenalezen nebo timeout, pokračuji...")
                
            print("🔐 Vyplňuji přihlašovací údaje...")
            page.get_by_label("Číslo mobilu, uživatelské jméno nebo e-mail").click()
            page.get_by_label("Číslo mobilu, uživatelské jméno nebo e-mail").fill(username)
            page.get_by_label("Heslo").click()
            page.get_by_label("Heslo").fill(password)
            print("🔐 Klikám na Log in / Odesílám formulář...")
            try:
                page.get_by_label("Heslo").press("Enter")
            except:
                page.locator("text='Přihlásit se'").first.click()
            
            print("⏳ Čekám, jestli se objeví 2FA ověření...")
            try:
                # Zkusíme počkat na pole pro ověřovací kód (max 5 vteřin)
                page.wait_for_selector('input[name="verificationCode"]', timeout=8000)
                if totp_secret:
                    print("🔐 Bylo vyžadováno 2FA. Generuji kód z IG_2FA_SECRET...")
                    # Odstraníme případné mezery ze secretu
                    totp = pyotp.TOTP(totp_secret.replace(" ", ""))
                    code = totp.now()
                    page.locator('input[name="verificationCode"]').fill(code)
                    print(f"🔑 Zadán kód: {code}. Potvrzuji...")
                    # Klikneme na tlačítko Potvrdit
                    page.locator('button:has-text("Potvrdit")').first.click()
                    # Počkáme chvíli na přihlášení
                    page.wait_for_timeout(5000)
                else:
                    print("❌ Bylo vyžadováno 2FA, ale v .env není vyplněn IG_2FA_SECRET. Skript počká 30 vteřin pro manuální zadání.")
                    page.wait_for_timeout(30000)
            except:
                print("✅ 2FA nebylo vyžadováno nebo se neukázalo pole pro kód, pokračuji dál...")
                 
            
            try:
                print("💾 Zkouším odkliknout Save info...")
                page.get_by_role("button", name="Save info").click(timeout=10000)
            except:
                pass

            try:
                print("➕ Klikám na New post (Create)...")
                page.get_by_role("link", name="New post Create").click(timeout=15000)
            except:
                 print("➕ Fallback klikám na New post...")
                 page.get_by_role("link", name="New post").click()
                 
            print("➕ Klikám na Post...")
            page.get_by_role("link", name="Post Post").click()
            
            print("📁 Klikám na výběr souborů...")
            # Níže simulujeme kliknutí, ale nenahrajeme žádné obrázky aby to nezveřejnilo reálný post
            page.get_by_role("button", name="Select From Computer").click()
            
            print("🎉 Test úspěšně dorazil k výběru obrázků. Skript zde končí.")
            page.wait_for_timeout(5000)
            
        except Exception as e:
            print(f"❌ Nastala chyba při testování: {e}")
            try:
                page.screenshot(path="playwright_test_error.png", full_page=True)
                print("📸 Screenshot uložen jako playwright_test_error.png")
            except:
                pass
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    test_playwright_flow()
