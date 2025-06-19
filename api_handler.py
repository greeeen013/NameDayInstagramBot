from dotenv import load_dotenv
import os
import requests
import json

# Načtení API klíče z .env souboru
load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
NASA_API_KEY = os.getenv("NASA_API_KEY")


def generate_with_gemini(prompt, model="gemini-2.0-flash", max_retries=3):
    """
    Získává odpověď od Google Gemini API pomocí přímých HTTP požadavků.

    Args:
        prompt (str): Textový vstup (prompt) pro AI
        model (str): Použitý model (výchozí je gemini-2.0-flash)
        max_retries (int): Maximální počet opakování při chybě

    Returns:
        str: Odpověď od AI nebo None pokud selže
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"

    headers = {
        'Content-Type': 'application/json'
    }

    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()

            data = response.json()

            if data and 'candidates' in data and len(data['candidates']) > 0:
                return data['candidates'][0]['content']['parts'][0]['text']
            else:
                print(f"Attempt {attempt + 1}: Empty response from API")

        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed with error: {str(e)}")
            if attempt == max_retries - 1:
                return None

        except (KeyError, IndexError) as e:
            print(f"Attempt {attempt + 1}: Failed to parse response - {str(e)}")
            if attempt == max_retries - 1:
                return None

    return None

def get_nasa_apod():
    """
    Načte dnešní data APOD (Astronomický snímek dne) z NASA API.
    Vrací slovník s 'hdurl' a 'vysvětlení', nebo None v případě chyby.
    """
    if not NASA_API_KEY:
        print("❌ [api_handler] NASA_API_KEY není nastaveno v .env souboru.")
        return None
    try:
        res = requests.get(f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}")
        if res.status_code != 200:
            print(f"❌ [api_handler] Chyba {res.status_code} při volání NASA APOD API.")
            return None
        data = res.json()
        url = data.get("hdurl") or data.get("url")
        explanation = data.get("explanation")
        if not url or not explanation:
            print("❌ [api_handler] Chybí URL nebo explanation v odpovědi NASA.")
            return None
        return {
            "hdurl": url,
            "explanation": explanation
        }
    except Exception as e:
        print(f"❌ [api_handler] Výjimka při volání NASA APOD API: {e}")
        return None


if __name__ == "__main__":
    names = "Jan, Marie"
    prompt = f"vygeneruj text pouze a jenom v češtině pro lidi co slaví svátek s jménem {names} (ty jména neupravuj neženštuj nic) zpracuj to nějako vtipně klidně použij emoji napiš jejich původ horoskop a hezky jim popřej k svátku zpracuj to jako popisek pod fotku na nic se neptej jen piš"

    response = generate_with_gemini(prompt)
    if response:
        print("Generated description:")
        print(response)
    else:
        print("Failed to generate description")