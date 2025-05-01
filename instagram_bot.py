from instagrapi import Client
from dotenv import load_dotenv
import os

load_dotenv()

IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

def post_to_instagram(image_path, description):
    if not IG_USERNAME or not IG_PASSWORD:
        raise ValueError("Instagram login credentials not found in .env file")

    cl = Client()
    cl.login(IG_USERNAME, IG_PASSWORD)

    cl.photo_upload(image_path, caption=description)
    print(f"Uploaded {image_path} to Instagram with caption: {description}")

if __name__ == "__main__":
    post_to_instagram("example.png", "Testovací popis")
