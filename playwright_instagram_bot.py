import re
import os
import time
import pyotp
from dotenv import load_dotenv
from playwright.sync_api import Playwright, sync_playwright, expect


def post_to_instagram(images: list, caption: str) -> None:
    load_dotenv()
    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    totp_secret = os.getenv("IG_2FA_SECRET")

    if not username or not password or not totp_secret:
        print("Error: Missing credentials in .env file!")
        return

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            print("Navigating to login page...")
            page.goto("https://www.instagram.com/accounts/login")
            
            # Handle cookies if present
            try:
                page.get_by_role("button", name="Allow all cookies").click(timeout=3000)
            except:
                pass

            # Login flow
            # Login flow
            print("Logging in...")
            # Try different selectors for username field as it varies
            try:
                page.get_by_role("textbox", name="Mobile number, username or").click(timeout=2000)
                page.get_by_role("textbox", name="Mobile number, username or").fill(username)
            except:
                page.get_by_role("textbox", name="Phone number, username or").click(timeout=2000)
                page.get_by_role("textbox", name="Phone number, username or").fill(username)

            page.get_by_role("textbox", name="Password").click()
            page.get_by_role("textbox", name="Password").fill(password)
            page.get_by_role("button", name="Log in", exact=True).click()

            # 2FA handling
            print("Waiting for 2FA prompt...")
            try:
                # Wait for the security code field to appear
                # It might redirect to /two_factor or just show the field
                page.wait_for_selector('input[name="verificationCode"]', timeout=10000)
                
                totp = pyotp.TOTP(totp_secret.replace(" ", ""))
                code = totp.now()
                print(f"Entering 2FA code: {code}")
                
                page.get_by_role("textbox", name="Security code").click()
                page.get_by_role("textbox", name="Security code").fill(code)
                page.get_by_role("button", name="Confirm").click()
                
                # Handle "Save info" if present
                try:
                    page.get_by_role("button", name="Save info").click(timeout=5000)
                except:
                    pass
            except Exception as e:
                print(f"2FA step might have been skipped or failed: {e}")

            # Handle "Not Now" (Notifications)
            try:
                page.get_by_role("button", name="Not now").click(timeout=5000)
            except:
                pass
            try:
                page.get_by_role("button", name="Cancel").click(timeout=3000)
            except:
                pass


            # Create Post
            print("Starting post creation...")
            # Wait for the "New post" link to be available
            page.wait_for_selector('a[aria-label="New post"], svg[aria-label="New post"]', timeout=20000)
            
            # Using get_by_role link name "New post Create" as seen in codegen
            try:
                page.get_by_role("link", name="New post Create").click()
            except:
                # Fallback to general selector if text varies
                page.get_by_role("link", name="New post").click()
                
            page.get_by_role("link", name="Post Post").click()
            
            print(f"Selecting files: {images}")
            
            with page.expect_file_chooser() as fc_info:
                page.get_by_role("button", name="Select From Computer").click()
            file_chooser = fc_info.value
            file_chooser.set_files(images)
            
            print("Clicking Next (Crop)...")
            page.get_by_role("button", name="Next").click()
            
            print("Clicking Next (Filter)...")
            page.get_by_role("button", name="Next").click()
            
            print("Adding caption...")
            page.get_by_role("textbox", name="Write a caption...").click()
            page.get_by_role("textbox", name="Write a caption...").fill(caption)
            
            print("Sharing...")
            try:
                page.get_by_role("button", name="Share").click()
            except:
                page.locator("div").filter(has_text=re.compile(r"^Share$")).nth(5).click()
            
            # Wait for upload confirmation
            print("Waiting for upload to complete...")
            try:
                page.wait_for_selector("text=Post shared", timeout=60000)
                print("Post shared successfully!")
            except:
                print("Warning: Did not see 'Post shared' confirmation, but might have finished.")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            print("Closing browser...")
            context.close()
            browser.close()

if __name__ == "__main__":
    # Test run
    # output_dir = os.path.join(os.path.dirname(__file__), "output")
    # images = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.startswith("img_") and f.endswith(".jpg")]
    # post_to_instagram(images, "Test caption")
    pass
