from dotenv import load_dotenv
import google.generativeai as genai
import os
import requests
import json

# Načtení API klíče z .env souboru
load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")


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

            # Extract the response text from the nested structure
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


if __name__ == "__main__":
    names = "Jan, Marie"
    prompt = f"vygeneruj text pouze a jenom v češtině pro lidi co slaví svátek s jménem {names} (ty jména neupravuj neženštuj nic) zpracuj to nějako vtipně klidně použij emoji napiš jejich původ horoskop a hezky jim popřej k svátku zpracuj to jako popisek pod fotku na nic se neptej jen piš"

    response = generate_with_gemini(prompt)
    if response:
        print("Generated description:")
        print(response)
    else:
        print("Failed to generate description")