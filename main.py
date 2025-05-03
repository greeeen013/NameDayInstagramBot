from image_generator import generate_image
from instagram_bot import post_album_to_instagram
from datetime import date

def main():
    image_paths = generate_image()
    description = f"Dnešní obrázek: {date.today().strftime('%d.%m.%Y')}"
    post_album_to_instagram(image_paths, description)

if __name__ == "__main__":
    main()
