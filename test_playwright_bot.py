import os
import time
import glob
import random
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import pyotp

def test_playwright_flow():
    print("🛠️ Začínám testovací Playwright skript s ukládáním screenshotů...")
    load_dotenv()
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    totp_secret = os.getenv("IG_2FA_SECRET")

    if not username or not password:
        print("❌ Chyba: Přihlašovací údaje IG_USERNAME a IG_PASSWORD nenalezeny v .env souboru.")
        return

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            locale="cs-CZ",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        os.makedirs("test_outputs_image", exist_ok=True)
        step_counter = 1

        def snap(step_name):
            nonlocal step_counter
            try:
                page.wait_for_timeout(1000)
                safe_name = "".join([c if c.isalnum() else "_" for c in step_name])
                filename = f"test_outputs_image/{step_counter:02d}_{safe_name}.png"
                page.screenshot(path=filename)
                print(f"📸 Debug screenshot uložen: {filename}")
                step_counter += 1
            except Exception as e:
                print(f"⚠️ Nelze uložit screenshot {step_name}: {e}")
        
        try:
            print("🌍 Přecházím na login stránku...")
            page.goto("https://www.instagram.com/accounts/login/")
            page.wait_for_timeout(3000) # Počká 3 vteřiny než se stránka plně renderovat
            snap("login_stranka_nactena")
            
            try:
                print("🍪 Zkouším odkliknout cookies...")
                page.locator("button:has-text('Allow all cookies'), button:has-text('Povolit všechny soubory cookie'), button:has-text('Povolit všechny')").first.click(timeout=5000)
                snap("po_odkliknuti_cookies")
            except:
                print("🍪 Cookies banner nenalezen nebo timeout, pokračuji...")
                snap("zadne_cookies_banner")
                
            print("🔐 Vyplňuji přihlašovací údaje...")
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
            snap("vyplneny_login_formular")
            
            print("🔐 Klikám na Log in / Odesílám formulář...")
            try:
                page.get_by_label("Password", exact=True).press("Enter")
            except:
                try:
                    page.get_by_label("Heslo", exact=True).press("Enter")
                except:
                    page.locator('button[type="submit"]').first.click()

            snap("po_odeslani_loginu")
            
            print("⏳ Čekám, jestli se objeví 2FA ověření...")
            try:
                page.wait_for_selector('input[name="verificationCode"]', timeout=8000)
                snap("zobrazilo_se_2FA_pole")
                if totp_secret:
                    print("🔐 Bylo vyžadováno 2FA. Generuji kód z IG_2FA_SECRET...")
                    totp = pyotp.TOTP(totp_secret.replace(" ", ""))
                    code = totp.now()
                    page.locator('input[name="verificationCode"]').fill(code)
                    snap("vyplneno_2FA_pole")
                    print(f"🔑 Zadán kód: {code}. Potvrzuji...")
                    page.locator('button:has-text("Confirm"), button:has-text("Potvrdit")').first.click()
                    page.wait_for_timeout(5000)
                    snap("po_odeslani_2FA")
                else:
                    print("❌ Bylo vyžadováno 2FA, ale v .env není vyplněn IG_2FA_SECRET. Skript počká 30 vteřin pro manuální zadání.")
                    page.wait_for_timeout(30000)
            except:
                print("✅ 2FA nebylo vyžadováno nebo se neukázalo pole pro kód, pokračuji dál...")
                 
            try:
                print("💾 Zkouším odkliknout Save info...")
                page.locator('button:has-text("Uložit informace"), button:has-text("Save info")').first.click(timeout=5000)
                snap("po_odeslani_save_info")
            except:
                pass
                
            try:
                print("⏭️ Odklikávám vyskakovací okna po přihlášení (Not Now)...")
                page.locator('button:has-text("Teď ne"), button:has-text("Not now")').first.click(timeout=5000)
                snap("po_odmitnuti_upozorneni")
            except:
                pass

            snap("konecna_nastenka_po_prihlaseni")

            try:
                print("➕ Klikám na New post (Create)...")
                page.locator('svg[aria-label="Nový příspěvek"], svg[aria-label="New post"]').click(timeout=10000)
            except:
                 print("➕ Fallback klikám na New post text...")
                 page.locator('xpath=//svg[@aria-label="Nový příspěvek" or @aria-label="New post"]').click()
                 
            print("➕ Čekám na otevření okna (Post)...")
            page.wait_for_timeout(3000)
            snap("po_kliknuti_na_vytvorit")
            
            print("📁 Klikám na výběr souborů...")
            png_files = glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "*.png"))
            if not png_files:
                print("❌ Žádné PNG soubory ve složce output nebyly nalezeny pro test.")
                return
            test_image = random.choice(png_files)
            print(f"📸 Vybrán testovací obrázek: {test_image}")

            with page.expect_file_chooser() as fc_info:
                # Upraveno tak, aby to chytilo tlačítko bez ohledu na tag (button, div, span)
                try:
                    page.locator('text="Vybrat z počítače"').first.click(timeout=5000)
                except:
                    # Fallback na EN text "Select from computer" pokud zlobí jazyk
                    page.locator('text="Select from computer"').first.click(timeout=5000)

            file_chooser = fc_info.value
            file_chooser.set_files([test_image])
            snap("po_vybrani_obrazku_z_disku")
            
            print("➡️ Čekám delší dobu na zpracování plátna s fotkou (headless mode je pomalý)...")
            page.wait_for_timeout(10000)
            print("➡️ Klikám na Další / Next (ořezávání)...")
            try:
                page.get_by_text("Další", exact=True).first.click(timeout=10000)
            except:
                page.get_by_text("Next", exact=True).first.click(timeout=10000)
            snap("po_prvnim_dalsi")

            print("➡️ Klikám na Další / Next (filtry)...")
            page.wait_for_timeout(3000)
            try:
                page.get_by_text("Další", exact=True).first.click(timeout=10000)
            except:
                page.get_by_text("Next", exact=True).first.click(timeout=10000)
            snap("po_druhem_dalsi")

            print("📝 Vyplňuji testovací popisek...")
            page.wait_for_timeout(3000)
            snap("pred_vyplnenim_popisku")
            caption_box = page.locator('div[aria-label="Napište popisek..."], div[aria-label="Write a caption..."]').first
            caption_box.click(timeout=10000)
            caption_box.fill("test")
            snap("po_vyplneni_popisku")

            print("🚀 Klikám na Sdílet / Share...")
            page.wait_for_timeout(3000)
            page.locator('div[role="button"]:text-is("Sdílet"), div[role="button"]:text-is("Share")').first.click(timeout=10000, force=True)

            print("🎉 Test úspěšně nahrál obrázek, vyplnil popisek a klikl na Sdílet. Skript zde končí.")
            page.wait_for_timeout(10000)
            snap("hotovo_zverejneno")
            
        except Exception as e:
            print(f"❌ Nastala chyba při testování: {e}")
            try:
                page.screenshot(path="playwright_test_error.png", full_page=True)
                print("📸 Detailní Error Screenshot uložen jako playwright_test_error.png")
            except:
                pass
            try:
                with open("playwright_test_error.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                print("📄 Celá HTML struktura uložena do: playwright_test_error.html")
            except Exception as e2:
                print(f"⚠️ Nepodařilo se uložit HTML: {e2}")
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    test_playwright_flow()
