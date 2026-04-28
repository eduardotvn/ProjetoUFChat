import os
import json
from google import genai
from typing import Dict, List, Optional
from dotenv import load_dotenv
from src.redisdb.memory import get_chat_history

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_ID = 'gemini-flash-latest'

def route_request(user_id: str, user_message: str) -> Dict[str, str]:

    
    system_instruction = (
        "Você é um roteador semântico para o UFChat. Sua tarefa é analisar o histórico da conversa e a mensagem atual do usuário "
        "para identificar todas as necessidades do usuário.\n\n"
        "Categorias disponíveis:\n"
        "1. 'Dúvidas Gerais e Contatos': Para dúvidas sobre processos, datas, contatos e informações gerais da UFCA.\n"
        "2. 'Links de Documentos': Quando o usuário solicita links para documentos online no site oficial da UFCA.\n"
        "3. 'Novidades ou Notícias': Para informações sobre notícias ou novidades da universidade.\n"
        "4. 'Cardápio do RU': Quando o usuário solicita o cardápio semanal do Restaurante Universitário.\n"
        "5. 'Requisição Perigosa': Para solicitações que envolvam dados sensíveis, conteúdo perigoso ou impróprio.\n\n"
        "6. 'Sem Necessidade': Para solicitações que não precisam de informações extras, como saudações"
        "Para cada necessidade identificada, retorne EXATAMENTE um objeto JSON onde a chave é a Categoria e o valor é a descrição curta da necessidade específica.\n"
        "Exemplo de saída: {\"Cardápio do RU\": \"Cardápio de hoje\", \"Dúvidas Gerais e Contatos\": \"Telefone da PRAE\"}"
        "Exemplo de saída: {\"Sem Necessidade\": \"N/A\"}"
    )

    history = get_chat_history(user_id)
    contents = []

    for pair in reversed(history):
        contents.append({"role": "user", "parts": [{"text": pair["user"]}]})
        contents.append({"role": "model", "parts": [{"text": pair["agent"]}]})
    
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    response = client.models.generate_content(
        model=MODEL_ID,
        contents=contents,
        config={
            'candidate_count': 1,
            'temperature': 0.1,
            'system_instruction': system_instruction,
            'response_mime_type': 'application/json'
        }
    )
    
    try:
        if response.text:
            return json.loads(response.text)
        return {"Dúvidas Gerais e Contatos": user_message}
    except (json.JSONDecodeError, AttributeError):
        return {"Dúvidas Gerais e Contatos": user_message}
