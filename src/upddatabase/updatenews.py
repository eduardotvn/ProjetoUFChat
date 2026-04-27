import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta
import re
import time
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, "scraped_data", "novidades_noticias.json")
os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)

BASE = "https://www.ufca.edu.br/noticias/"
DOMAIN = "https://www.ufca.edu.br"

headers = {"User-Agent": "Mozilla/5.0 (compatible; UFCA-Scraper/1.0; +eduardo.tavares@aluno.ufca.edu.br)"}

hoje = datetime.now()
tres_meses_atras = hoje - timedelta(days=90)

def extrair_data(texto):
    padrao = r"Publicado em (\d{2}/\d{2}/\d{4})"
    m = re.search(padrao, texto)
    if not m:
        return None
    return datetime.strptime(m.group(1), "%d/%m/%Y")

def obter_links_de_noticias():
    resp = requests.get(BASE, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "/noticias/" in href and "/page/" not in href and "/categoria/" not in href:
            full_url = urljoin(BASE, href)
            if full_url not in links:
                links.append(full_url)

    return links


def filtrar_noticias_recentes():
    links = obter_links_de_noticias()
    noticias_validas = []

    for link in links:
        try:
            time.sleep(0.3)
            print("Checando:", link)

            resp = requests.get(link, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            p_data = soup.find("p", class_="content-update-data")
            if not p_data:
                continue

            data = extrair_data(p_data.get_text())

            if not data:
                continue

            if tres_meses_atras <= data <= hoje:
                titulo = soup.find("h1").get_text(strip=True) if soup.find("h1") else "Sem título"
                noticias_validas.append({
                    "titulo": titulo,
                    "link": link,
                    "data": data.strftime("%d/%m/%Y")
                })

        except:
            continue

    return noticias_validas

from src.vectordb.manager import index_json_file

def update_news():
    noticias = filtrar_noticias_recentes()
    if len(noticias) > 5:
        noticias = noticias[:5]
    
    if not os.path.exists(JSON_PATH):
        with open(JSON_PATH, "w", encoding='utf-8') as f:
            json.dump(noticias, f, ensure_ascii=False, indent=4)
        
        print(f"Criando banco de notícias pela primeira vez em {JSON_PATH}. Atualizando banco vetorial...")
        index_json_file(JSON_PATH, "Novidades ou Notícias")
    else:
        try:
            with open(JSON_PATH, "r", encoding='utf-8') as f:
                old_news = json.load(f)
        except:
            old_news = []

        if old_news != noticias:
            with open(JSON_PATH, "w", encoding='utf-8') as f:
                json.dump(noticias, f, ensure_ascii=False, indent=4)
            
            print(f"Novas notícias detectadas. Atualizando banco vetorial...")
            index_json_file(JSON_PATH, "Novidades ou Notícias")
        else:
            print("Notícias sem atualização.")

    for n in noticias:
        print(f"{n['data']} - {n['titulo']} -> {n['link']}")

update_news()