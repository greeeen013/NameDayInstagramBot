import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def get_name_info(hledane_jmeno):
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    print(f"Hledám svátek pro jméno '{hledane_jmeno}'...")

    # Načtení stránky se svátky
    res = session.get("https://www.nasejmena.cz/")
    if res.status_code != 200:
        print("Nepodařilo se načíst stránku se svátky.")
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    # Vlastní mapování českých dnů
    dny_cesky = [
        "Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"
    ]
    dnes = datetime.now()
    den_nazev = dny_cesky[dnes.weekday()]
    datum = f"{dnes.day}.{dnes.month}.{dnes.year}"
    hledany_radek = f"{den_nazev}\xa0{datum}"  # např. Čtvrtek 1.5.2025

    # Najdi dnešní buňku s datem
    td_dens = soup.find("td", class_="kal_dens", string=hledany_radek)
    if not td_dens:
        print("Dnešní datum nebylo nalezeno v kalendáři.")
        return None

    # Procházej další řádky, dokud nenajde jméno nebo nový den
    td = td_dens.find_parent("tr").find_next_sibling("tr")
    while td:
        obsah_td = td.find("td")
        if not obsah_td:
            td = td.find_next_sibling("tr")
            continue

        if "kal_jme" in obsah_td.get("class", []) or "kal_jmev" in obsah_td.get("class", []) or "kal_jmes" in obsah_td.get("class", []):
            # Zde se kontroluje, jestli je klikatelné
            a_tag = obsah_td.find("a")
            if not a_tag:
                print("Dnes nikdo nemá svátek.")
                return None

            name_text = a_tag.text.strip()
            href = a_tag.get("href")

            if name_text.lower() != hledane_jmeno.lower():
                print(f"Dnes má svátek někdo jiný ({name_text}), ne '{hledane_jmeno}'.")
                return None

            # Získání detailní stránky jména
            detail_url = f"https://www.nasejmena.cz/nj/{href}"
            res = session.get(detail_url)
            if res.status_code != 200:
                print("Nepodařilo se načíst detail jména.")
                return None

            soup = BeautifulSoup(res.text, "html.parser")
            header = soup.find("span", {"class": "hlavicka"})
            if not header:
                print("Nepodařilo se najít informace o jménu.")
                return None

            header_text = header.text
            cisla = re.findall(r'\d+', header_text)
            if len(cisla) < 3:
                print("Nepodařilo se parsovat statistiky.")
                return None

            count = int(cisla[0])
            rank = int(cisla[1])
            avg_age = int(cisla[2])

            vysledek = {
                "name": name_text,
                "count": count,
                "rank": rank,
                "avg_age": avg_age
            }
            print(f"Výsledek: {vysledek}")
            return vysledek

        if "kal_dens" in obsah_td.get("class", []) or "kal_den" in obsah_td.get("class", []) or "kal_denv" in obsah_td.get("class", []):
            # Už jsme u dalšího dne, končíme
            break

        td = td.find_next_sibling("tr")

    print("Dnes nikdo nemá svátek.")
    return None
