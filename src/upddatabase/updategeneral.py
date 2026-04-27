from bs4 import BeautifulSoup
import requests
import json
import re 
from dotenv import load_dotenv
import google.generativeai as genai
import os 
import time 

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_JSON_PATH = os.path.join(BASE_DIR, "scraped_data", "scrapping_ufca.json")
os.makedirs(os.path.dirname(SAVE_JSON_PATH), exist_ok=True)

headers = {"User-Agent": os.getenv("USER_AGENT", "Mozilla/5.0")}

## ATUALIZAÇÃO DE CONTEÚDO DE CURSOS

def atualizar_cursos():
  url = "https://www.ufca.edu.br/cursos/graduacao/"
  global headers
  req = requests.get(url, headers=headers)
  soup = BeautifulSoup(req.text, "html.parser")
  span = ""
  contents = soup.find_all("a", class_="item")
  conteudo_cursos = {}
  legenda_cursos = {
      "1": "primeiro", "2": "segundo", "3": "terceiro", "4": "quarto",
      "5": "quinto", "6": "sexto", "7": "sétimo", "8": "oitavo",
      "9": "nono", "10": "décimo", "11": "décimo primeiro", "12": "décimo segundo"
  }
  for content in contents:
    print("Visitando :", content['href'])

    req = requests.get(content['href'], headers=headers)
    soup = BeautifulSoup(req.text, "html.parser")
    texts = soup.find_all("div", class_="ui bottom attached tab segment active")
    matriz_curricular = soup.find_all("div", class_="extrablocks-accordion ui styled fluid accordion")
    span = ""
    semestres = {}
    curso = "Nome não encontrado"
    for enum, div in enumerate(matriz_curricular, start = 1):
      time.sleep(0.2)
      tag_titulo = soup.select_one("article#content h1")
      if tag_titulo:
          curso = tag_titulo.text.strip()
      else:
          tag_titulo_backup = soup.select_one("div.twelve.wide.column h1")
          if tag_titulo_backup:
              curso = tag_titulo_backup.text.strip()
      
      print("Curso sendo visitado: ", curso)
      if enum == len(matriz_curricular):
        num_sem = f"Disciplinas ou cadeiras optativas de {curso}:"
      else:
        if str(enum) in legenda_cursos:
          num_sem = f"Disciplinas ou cadeiras do semestre {enum} ({legenda_cursos[str(enum)]} semestre) de {curso}"
        else:
          num_sem = f"Disciplinas ou cadeiras do semestre {enum} de {curso}"
      cadeiras = (div.find_all("span", class_="extrablocks-accordion-item-label"))
      for cadeira in cadeiras: 
        span += cadeira.text + ", "
      semestres.update({num_sem: span})
      span = ""
      if enum == len(matriz_curricular):
        conteudo_cursos.update({f"Quantidade de semestres de {curso}": f"{enum - 1} semestres"})
    
    descricao = {}
    for text in texts:
      descricao = {f"Descrição de {curso}": text.text.replace("\n", "")}
    
    conteudo_cursos.update(descricao)
    conteudo_cursos.update(semestres)
  
  return conteudo_cursos

##ATUALIZAÇÃO DE INSTITUIÇÕES

def atualizar_pro_reitorias():
  global headers
  url = "https://www.ufca.edu.br/instituicao/administrativo/estrutura-organizacional/pro-reitorias/"
  req = requests.get(url, headers=headers)
  soup = BeautifulSoup(req.text, "html.parser")

  contents = soup.find_all("ul", class_="ui fluid vertical menu")
  a_elements = []

  informacoes_pro_reitorias = {}

  for ul in contents:
      a_elements.extend(ul.find_all("a"))

  for a in a_elements:
    time.sleep(0.2)
    url = a['href']
    nome_instituicao = url.replace("https://www.ufca.edu.br/instituicao/administrativo/estrutura-organizacional/pro-reitorias/", "").replace("/", "").upper()
    soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")

    marker_icon = soup.find("i", class_="envelope outline icon")

    contents_div = soup.find('div', class_=re.compile(r'extrablocks-tabs extrablocks-tabs-\d+'))
    inner_content = soup.find('div', class_='ui bottom attached tab segment extrablocks-tab active')
    
    if contents_div:
        primeiro_p = contents_div.find('p')
        p_text = primeiro_p.get_text(strip=True) if primeiro_p else ""
        print(f"Informações {nome_instituicao}: ", p_text)
        
        aux = ""
        if inner_content:
            lis = inner_content.find_all('li')
            for li in lis:
                a_tag = li.find("a") 
                if a_tag and a_tag.get("href"):
                    aux += li.get_text(strip=True) + a_tag["href"]
                else:
                    aux += li.get_text(strip=True)

        informacoes_pro_reitorias.update({f"Informações {nome_instituicao}" :  p_text + aux})
                                    
    if marker_icon:
        contact_block = marker_icon.find_parent("div", class_="extrablocks-accordion-item-content")
        if contact_block:
            contact = contact_block.get_text("\n", strip=True).split("\n")
            contact[0] = "Endereço: " + contact[0]
            informacoes_pro_reitorias.update({f"Contato {nome_instituicao}" : str(contact)})
            print(f"Contatos {nome_instituicao}: ", contact)
    else:
        print(f"❌ Não foi encontrado o ícone de localização em {url}")
  
  return informacoes_pro_reitorias
    
def atualizar_unidades_academicas():
  url = "https://www.ufca.edu.br/instituicao/administrativo/estrutura-organizacional/unidades-academicas/"
  req = requests.get(url, headers=headers)
  soup = BeautifulSoup(req.text, "html.parser")

  contents = soup.find_all("ul", class_="ui fluid vertical menu")
  a_elements = []

  for ul in contents:
      a_elements.extend(ul.find_all("a"))

  all_data = {}
  for a in a_elements:
    time.sleep(0.2)
    url = a['href']
    html = requests.get(url, headers=headers).text
    soup = BeautifulSoup(html, "html.parser")
    instituicao = url.replace("https://www.ufca.edu.br/instituicao/administrativo/estrutura-organizacional/unidades-academicas/", "").replace("/", "")
    print(instituicao)
    alvo = soup.find("div", class_=re.compile(r"extrablocks-tabs-\d+"))

    texto = ""
    if alvo:
        for tag in alvo(["script", "style", "noscript"]):
            tag.decompose()
        texto = alvo.get_text(separator="\n", strip=True)
    
    prompt = f"Use as informações a seguir para produzir um JSON, e retorne APENAS O JSON em sua resposta, contendo as seguintes informações: o nome da instituição, o contato, o que ele faz, cursos e endereço. Exemplo: 'CCAB Contato' : 'Contato do CCAB é...', 'CCAB Endereço' : 'O endereço do CCAB é...', 'CCAB Cursos': 'Os cursos do CCAB são...'. Instituição: {instituicao}, informações: {texto}"
    
    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
    try:
        data = json.loads(response.text)
        all_data.update(data)
    except:
        print("Erro ao decodificar JSON da unidade acadêmica")

  return all_data

def atualizar_orgaos_complementares():
  url = "https://www.ufca.edu.br/instituicao/administrativo/estrutura-organizacional/orgaos-complementares/"
  req = requests.get(url, headers=headers)
  soup = BeautifulSoup(req.text, "html.parser")

  contents = soup.find_all("ul", class_="ui fluid vertical menu")
  a_elements = []

  for ul in contents:
      a_elements.extend(ul.find_all("a"))

  all_data = {}
  for a in a_elements:
    time.sleep(0.2)
    url = a['href']
    html = requests.get(url, headers=headers).text
    soup = BeautifulSoup(html, "html.parser")
    instituicao = url.replace("https://www.ufca.edu.br/instituicao/administrativo/estrutura-organizacional/orgaos-complementares/", "").replace("/", "")
    print(instituicao)
    alvo = soup.find("div", class_=re.compile(r"extrablocks-tabs-\d+"))

    texto = ""
    if alvo:
        for tag in alvo(["script", "style", "noscript"]):
            tag.decompose()
        texto = alvo.get_text(separator="\n", strip=True)
    
    prompt = f"Use as informações abaixo para produzir um JSON, e retorne APENAS O JSON em sua resposta, contendo as seguintes informações: o nome da instituição, o contato, o que ele faz e endereço. Preencha pelo menos 3 palavras semânticamente parecidas e o nome da instituição nas keys, pois serão usados em RAG. Exemplo: 'CCAB Contato, Telefone, Email' : 'Contato do CCAB é...', 'CCAB Endereço, Localização, forma de chegar...' : 'O endereço do CCAB é...'. Não coloque listas nos valores das chaves do json, apenas texto. Instituição: {instituicao}, informações: {texto}"
    
    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
    try:
        data = json.loads(response.text)
        all_data.update(data)
    except:
        print("Erro ao decodificar JSON do órgão complementar")

  return all_data 

from src.vectordb.manager import index_json_file

def reload_context():
  contexto_obtido = {}
  contexto_obtido.update(atualizar_cursos())
  contexto_obtido.update(atualizar_pro_reitorias())
  contexto_obtido.update(atualizar_unidades_academicas())
  contexto_obtido.update(atualizar_orgaos_complementares())

  # Explicit check for first-time creation or updates
  if not os.path.exists(SAVE_JSON_PATH):
      with open(SAVE_JSON_PATH, "w", encoding="utf-8") as f:
          json.dump(contexto_obtido, f, ensure_ascii=False, indent=4)
      print(f"Criando contexto pela primeira vez em {SAVE_JSON_PATH}. Atualizando banco vetorial...")
      index_json_file(SAVE_JSON_PATH, "Dúvidas Gerais e Contatos")
  else:
      with open(SAVE_JSON_PATH, "r", encoding="utf-8") as f:
          try:
              old_data = json.load(f)
          except:
              old_data = {}
              
      if old_data != contexto_obtido:
          with open(SAVE_JSON_PATH, "w", encoding="utf-8") as f:
              json.dump(contexto_obtido, f, ensure_ascii=False, indent=4)
          print(f"Novas informações detectadas. Contexto atualizado em {SAVE_JSON_PATH}. Atualizando banco vetorial...")
          index_json_file(SAVE_JSON_PATH, "Dúvidas Gerais e Contatos")
      else:
          print("Informações gerais sem atualização.")
