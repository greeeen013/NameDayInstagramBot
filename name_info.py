import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

dny_cesky = [
        "Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"
    ]

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

    dnes = datetime.now()
    den_nazev = dny_cesky[dnes.weekday()]
    datum = f"{dnes.day}.{dnes.month}.{dnes.year}"
    hledany_radek = f"{den_nazev}\xa0{datum}"  # např. Čtvrtek 1.5.2025
    print(f"Hledaný řetězec: '{hledany_radek}'")

    # Najdi dnešní buňku s datem
    td_dens = soup.find("td", string=hledany_radek)
    if not td_dens:
        # Zkusíme alternativní formát (např. "Sobota&nbsp;3.5.2025")
        alternativni_format = f"{den_nazev}&nbsp;{datum}"
        td_dens = soup.find("td", string=alternativni_format)
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

        # Zkontrolujeme všechny možné třídy pro jména
        if any(cls in obsah_td.get("class", []) for cls in ["kal_jme", "kal_jmev", "kal_jmes"]):
            # Najdeme všechny odkazy v buňce (pro případ více jmen)
            a_tags = obsah_td.find_all("a")
            if not a_tags:
                print("Dnes nikdo nemá svátek.")
                return None

            # Projdeme všechna jména v daný den
            for a_tag in a_tags:
                name_text = a_tag.text.strip()
                if name_text.lower() == hledane_jmeno.lower():
                    href = a_tag.get("href")
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

                    # Získání původu jména
                    dopinfo = soup.find("span", {"class": "dopinfo"})
                    puvod = None
                    if dopinfo:
                        # Extrahujeme původ z textu
                        puvod_match = re.search(r'původ:\s*([^,]+)', dopinfo.text)
                        if puvod_match:
                            puvod = puvod_match.group(1).strip()

                    count = int(cisla[0])
                    rank = int(cisla[1])
                    avg_age = int(cisla[2])

                    vysledek = {
                        "name": name_text,
                        "count": count,
                        "rank": rank,
                        "avg_age": avg_age,
                        "origin": puvod if puvod else "neuvedeno"
                    }
                    print(f"Výsledek: {vysledek}")
                    return vysledek

            # Pokud jsme prošli všechna jména a nenašli jsme hledané
            print(f"Dnes má svátek {', '.join([a.text.strip() for a in a_tags])}, ale ne '{hledane_jmeno}'.")
            return None

        # Pokud narazíme na další den, končíme
        if any(cls in obsah_td.get("class", []) for cls in ["kal_dens", "kal_den", "kal_denv"]):
            break

        td = td.find_next_sibling("tr")

    print("Dnes nikdo nemá svátek.")
    return None

def get_todays_names():
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    print("Zjišťuji, kdo má dnes svátek...")

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
    hledane_formaty = [
        f"{den_nazev}\xa0{datum}",  # např. "Čtvrtek\xa01.5.2025"
        f"{den_nazev}&nbsp;{datum}" # např. "Sobota&nbsp;3.5.2025"
    ]

    # Najdi dnešní buňku s datem
    td_dens = None
    for format in hledane_formaty:
        td_dens = soup.find("td", string=format)
        if td_dens:
            break

    if not td_dens:
        print("Dnešní datum nebylo nalezeno v kalendáři.")
        return None

    # Procházej další řádky, dokud nenajde jména nebo nový den
    td = td_dens.find_parent("tr").find_next_sibling("tr")
    jmena = []

    while td:
        obsah_td = td.find("td")
        if not obsah_td:
            td = td.find_next_sibling("tr")
            continue

        # Zkontrolujeme všechny možné třídy pro jména
        if any(cls in obsah_td.get("class", []) for cls in ["kal_jme", "kal_jmev", "kal_jmes"]):
            # Najdeme všechny odkazy v buňce (pro případ více jmen)
            a_tags = obsah_td.find_all("a")
            if a_tags:
                jmena.extend([a.text.strip() for a in a_tags])

        # Pokud narazíme na další den, končíme
        if any(cls in obsah_td.get("class", []) for cls in ["kal_dens", "kal_den", "kal_denv"]):
            break

        td = td.find_next_sibling("tr")

    if not jmena:
        print("Dnes nikdo nemá svátek.")
        return None

    print(f"Dnes má svátek: {', '.join(jmena)}")
    return jmena

if __name__ == "__main__":
    print(get_todays_names())
    jmeno = "Alexej"
    info = get_name_info(jmeno)
    if info:
        print(f"Jméno: {info['name']}, Počet nositelů: {info['count']}, Pořadí: {info['rank']}, Průměrný věk: {info['avg_age']}")
    else:
        print("Žádné informace nebyly nalezeny.")