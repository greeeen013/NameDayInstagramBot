import re
import os
from playwright.sync_api import Playwright, sync_playwright, expect
from dotenv import load_dotenv

def run(playwright: Playwright, images: list, caption: str, two_factor_code: str) -> None:
    load_dotenv()
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")

    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.instagram.com/accounts/login/")
    
    try:
        page.get_by_role("button", name="Allow all cookies").click(timeout=5000)
    except:
        pass
        
    page.get_by_role("textbox", name="Mobile number, username or").click()
    page.get_by_role("textbox", name="Mobile number, username or").fill(username)
    page.get_by_role("textbox", name="Password").click()
    page.get_by_role("textbox", name="Password").fill(password)
    page.get_by_role("button", name="Log in", exact=True).click()
    
    # 2FA
    if two_factor_code:
        try:
            page.get_by_role("textbox", name="Security code").click(timeout=10000)
            page.get_by_role("textbox", name="Security code").fill(two_factor_code)
            page.get_by_role("button", name="Confirm").click()
        except Exception as e:
            print(f"2FA step skipped or failed: {e}")

    try:
        page.get_by_role("button", name="Save info").click(timeout=10000)
    except:
        pass

    try:
        page.get_by_role("link", name="New post Create").click(timeout=15000)
    except:
         # Fallback if text differs slightly (e.g. just "Create")
         page.get_by_role("link", name="New post").click()
         
    page.get_by_role("link", name="Post Post").click()
    page.get_by_role("button", name="Select From Computer").click()
    page.get_by_role("button", name="Select From Computer").set_input_files(images)
    
    page.get_by_role("button", name="Next").click()
    page.get_by_role("button", name="Next").click()
    
    page.get_by_role("textbox", name="Write a caption...").click()
    page.get_by_role("textbox", name="Write a caption...").fill(caption)
    
    page.get_by_role("button", name="Share").click()
    
    print("Post shared successfully (hopefully)!")
    
    # Wait a bit to ensure upload finishes
    page.wait_for_timeout(10000)

    # ---------------------
    context.close()
    browser.close()


def post_to_instagram(images: list, caption: str, two_factor_code: str) -> None:
    with sync_playwright() as playwright:
        run(playwright, images, caption, two_factor_code)
