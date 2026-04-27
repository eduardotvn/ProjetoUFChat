import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
from datetime import datetime
import re
import json
import os

# BASE_DIR is used to define JSON_PATH
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, "scraped_data", "editais.json")

# Create scraped_data directory if it doesn't exist
os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)

def get_soup(url):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; UFCA-Scraper/1.0; +eduardo.tavares@aluno.ufca.edu.br)"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

def extrair_paginas_por_ano(url_pagina):
    ano = str(datetime.now().year)
    soup = get_soup(url_pagina)

    sublinks = []
    for a in soup.find_all("a", href=True):
        href = a["href"]

        if not href.startswith("http"):
            href = urljoin(url_pagina, href)

        if url_pagina in href and ano in href:
            sublinks.append(href)

    sublinks = list(dict.fromkeys(sublinks))

    return sublinks

links_concurso = extrair_paginas_por_ano("https://www.ufca.edu.br/admissao/concursos-e-selecoes/docentes/efetivo/editais-vigentes/")

def extrair_links_documentos(url_pagina, doctype):
    ano = str(datetime.now().year)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; UFCA-Scraper/1.0; +eduardo.tavares@aluno.ufca.edu.br)"}
    resp = requests.get(url_pagina, headers=headers)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    meses = {"01": "Janeiro", "02": "Fevereiro", "03": "Março", "04": "Abril", "05": "Maio", "06":"Junho", "07":"Julho", "08":"Agosto", "09":"Setembro", "10":"Outubro", "11":"Novembro", "12":"Dezembro"}

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]

        if (href.lower().endswith(".pdf") or "wp-folder" in href.lower() or "uploads" in href.lower()) and ano in href.lower():
            full = unquote(urljoin(url_pagina, href))
            date = full.replace("https://documentos.ufca.edu.br/wp-folder/wp-content/uploads/", "")[:7]
            date = f"{meses[date[-2:]]} de {date[:4]}"
            doc_name = " ".join(re.split(r"[-_]",full.replace("https://documentos.ufca.edu.br/wp-folder/wp-content/uploads/", "")[8:]))
            if doctype == "graduação":
              links.append(f"Editais de Graduação, Admissão, Matrícula e Sisu de {ano} - {doc_name} - {date} : " + full)
            elif doctype == "prae":
              links.append(f"Edital de Assuntos Estudantis, Bolsas, Auxílios de {ano} - {doc_name} - {date} : " + full)
            elif doctype == "concurso":
              links.append(f"Edital de Concursos de {ano} - {doc_name} - {date} : " + full)
            else:
              links.append(f"Editais de EAD de {ano} - {doc_name} - {date} : " + full)
    for element in soup.find_all('div', class_='ui accordion'):
        titulo_tag = element.find('div', class_='title')
        titulo = None
            
        if titulo_tag:
            i_tag = titulo_tag.find('i', class_='dropdown icon')
            if i_tag:
                i_tag.extract() 
                    
            titulo = titulo_tag.get_text(strip=True)

        link_tag = element.find('a', class_='ui teal button')
        link = None
            
        if link_tag:
            link = link_tag.get('href')

        if link and ("post_type=doc" in link): 
            if doctype == "graduação":
                links.append((f"Editais de Graduação, Admissão e Matrícula - {titulo} : {link}").replace("–", "-"))
            elif doctype == "prae":
                links.append(f"Edital de Assuntos Estudantis, Bolsas, Auxílios - {titulo} : {link}")
            elif doctype == "concurso":
                links.append(f"Edital de Concursos - {titulo} : {link}")
            else:
                links.append(f"Editais de EAD - {titulo} : {link}")
    
    unique = list(dict.fromkeys(links))
    return unique

from src.vectordb.manager import index_json_file

def update_docs():
    url_grad = "https://www.ufca.edu.br/admissao/graduacao/sisu/editais-e-resultados/"
    url_prae = "https://www.ufca.edu.br/assuntos-estudantis/editais/editais-vigentes/"
    docs_grad = extrair_links_documentos(url_grad, "graduação")
    docs_prae = extrair_links_documentos(url_prae, "prae")
    docs = docs_grad + docs_prae
    for link in links_concurso:
        docs = docs + extrair_links_documentos(link, "concurso")

    # Explicit check for first-time creation or updates
    if not os.path.exists(JSON_PATH):
        with open(JSON_PATH,"w", encoding='utf-8') as f:
            json.dump(docs, f, ensure_ascii=False, indent=4)
        print("Criando banco de editais pela primeira vez...")
        index_json_file(JSON_PATH, "Links de Documentos")
    else:
        with open(JSON_PATH, "r", encoding='utf-8') as f:
            try:
                old_docs = json.load(f)
            except:
                old_docs = []
        
        if old_docs != docs:
            with open(JSON_PATH,"w", encoding='utf-8') as f:
                json.dump(docs, f, ensure_ascii=False, indent=4)
            print("Novos editais detectados. Atualizando banco vetorial...")
            index_json_file(JSON_PATH, "Links de Documentos")
        else:
            print("Editais sem atualização.")

update_docs()