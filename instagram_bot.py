from instagrapi import Client
from dotenv import load_dotenv
import os
from datetime import datetime, timezone

load_dotenv()

IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

cl = Client()

def login():
    if not IG_USERNAME or not IG_PASSWORD:
        raise ValueError("Instagram login credentials not found in .env file")
    cl.login(IG_USERNAME, IG_PASSWORD)

def has_posted_today():
    login()
    posts = cl.user_medias_v1(cl.user_id, amount=1)  # BEZ GQL - stabilnější

    today = datetime.now(timezone.utc).date()

    for post in posts:
        if post.taken_at.date() == today:
            return True
    return False


def post_to_instagram(image_path, description):
    if has_posted_today():
        print("Dnes už byl příspěvek přidán, nepřidávám další.")
        return

    cl.photo_upload(image_path, caption=description)
    print(f"Uploaded {image_path} to Instagram with caption: {description}")

if __name__ == "__main__":
    post_to_instagram("example.png", "Testovací popis")
