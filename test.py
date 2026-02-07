day_name = "Světový humanitární den"
display_text = day_name.replace("Mezinárodní den", "").replace("Den", "").strip().capitalize().replace(
        "Světový", "").strip().capitalize().replace("Evropský den", "").strip().capitalize().replace("den", "").strip().capitalize()

print(f"Mezinárodní den:\n{display_text}")