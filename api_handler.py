from openai import OpenAI
from dotenv import load_dotenv
import os

# Načtení API klíče z .env souboru
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENROUTER_API_KEY")


def generate_with_openrouter(prompt, model="anthropic/claude-3-haiku", max_retries=3):
    """
    Get AI response from OpenRouter API with robust error handling.

    Args:
        prompt (str): The user's input prompt
        model (str): The model to use (default is Claude 3 Haiku)
        max_retries (int): Number of retries if request fails

    Returns:
        str: The AI's response or None if failed
    """

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENAI_API_KEY,
    )

    for attempt in range(max_retries):
        try:
            completion = client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://github.com/your-repo",
                    "X-Title": "NameDayInstagramBot",
                },
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            if completion and completion.choices and len(completion.choices) > 0:
                return completion.choices[0].message.content
            else:
                print(f"Attempt {attempt + 1}: Empty response from API")

        except Exception as e:
            print(f"Attempt {attempt + 1} failed with error: {str(e)}")
            if attempt == max_retries - 1:
                return None

    return None


if __name__ == "__main__":
    names = "Jan, Marie"
    prompt = f"vygeneruj text pouze a jenom v češtině pro lidi co slaví svátek s jménem {names} (ty jména neupravuj neženštuj nic) zpracuj to nějako vtipně klidně použij emoji napiš jejich původ horoskop a hezky jim popřej k svátku zpracuj to jako popisek pod fotku na nic se neptej jen piš"

    response = generate_with_openrouter(prompt)
    if response:
        print("Generated description:")
        print(response)
    else:
        print("Failed to generate description")