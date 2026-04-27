import os
from google import genai
from typing import Literal
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_ID = 'gemini-2.0-flash'

Category = Literal[
    "Dúvidas Gerais e Contatos",
    "Links de Documentos",
    "Novidades ou Notícias",
    "Cardápio do RU",
    "Requisição Perigosa"
]

def route_request(user_message: str) -> Category:

    
    system_instruction = (
        "Você é um roteador semântico para o UFChat. Sua única tarefa é classificar a mensagem do usuário "
        "em uma das seguintes categorias, respondendo EXATAMENTE com o nome da categoria:\n\n"
        "1. 'Dúvidas Gerais e Contatos': Para dúvidas sobre processos, datas, contatos e informações gerais da UFCA.\n"
        "2. 'Links de Documentos': Quando o usuário solicita links para documentos online no site oficial da UFCA.\n"
        "3. 'Novidades ou Notícias': Para informações sobre notícias ou novidades da universidade.\n"
        "4. 'Cardápio do RU': Quando o usuário solicita o cardápio semanal do Restaurante Universitário.\n"
        "5. 'Requisição Perigosa': Para solicitações que envolvam dados sensíveis (como informações pessoais de professores), "
        "conteúdo perigoso ou impróprio.\n\n"
        "Responda apenas com o nome da categoria, sem explicações adicionais."
    )

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=user_message,
        config={
            'candidate_count': 1,
            'max_output_tokens': 20,
            'temperature': 0.1,
            'system_instruction': system_instruction
        }
    )
    
    category = response.text.strip()
    
    valid_categories = [
        "Dúvidas Gerais e Contatos",
        "Links de Documentos",
        "Novidades ou Notícias",
        "Cardápio do RU",
        "Requisição Perigosa"
    ]
    
    if category in valid_categories:
        return category
    
    return "Dúvidas Gerais e Contatos"
