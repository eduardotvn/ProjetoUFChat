import requests
from bs4 import BeautifulSoup
import os
import json 
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, "scraped_data", "links_gerais.json")
os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)

headers = {"User-Agent": os.getenv("USER_AGENT", "Mozilla/5.0")}

def obter_pdf_ru():
    global headers
    url_pag = "https://www.ufca.edu.br/assuntos-estudantis/refeitorio-universitario/cardapios/"
    resp = requests.get(url_pag, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    botoes = soup.find_all("a", class_="ui teal button")

    if not botoes:
        print("Nenhum botão encontrado no HTML!")
        return None

    botao_recente = botoes[0]

    url_intermediaria = botao_recente.get("href")

    resp_final = requests.get(url_intermediaria, allow_redirects=True, headers=headers)
    return resp_final.url

def update_menu():
    link = obter_pdf_ru()
    
    # Initialize or load existing cardapio
    cardapio_data = {"Cardápio da Semana": ""}
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, "r", encoding='utf-8') as f:
                cardapio_data = json.load(f)
        except:
            pass

    if cardapio_data.get("Cardápio da Semana") != link:
        cardapio_data["Cardápio da Semana"] = link
        with open(JSON_PATH, "w", encoding='utf-8') as f:
            json.dump(cardapio_data, f, ensure_ascii=False, indent=4)
        print(f"Cardápio atualizado: {link}")
    else:
        print("Cardápio já está atualizado.")

update_menu()