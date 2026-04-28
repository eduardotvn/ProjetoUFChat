import os
import json
from src.redisdb.memory import get_chat_history
from src.vectordb.manager import search_vectors

# Define o caminho para o JSON de links gerais
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LINKS_GERAIS_PATH = os.path.join(BASE_DIR, "scraped_data", "links_gerais.json")

def build_prompt(user_id: str, user_message: str, router_results: dict[str, str]) -> tuple[str, list]:
    """
    Constrói o prompt do sistema e o histórico de mensagens para o modelo, 
    incorporando informações recuperadas via RAG para cada intenção detectada.
    
    Args:
        user_id: ID do usuário para recuperar o histórico.
        user_message: Mensagem atual do usuário.
        router_results: Dicionário mapeando categorias para necessidades específicas.
        
    Returns:
        Um tupla contendo a instrução do sistema (str) e a lista de conteúdos (list).
    """
    
    additional_info_parts = []
    
    # Busca informações para cada intenção detectada pelo roteador
    for category, need in router_results.items():
        if category == "Requisição Perigosa":
            additional_info_parts.append(f"ALERTA DE SEGURANÇA: O usuário fez uma solicitação potencialmente perigosa: {need}")
            continue
            
        if category == "Cardápio do RU":
            try:
                if os.path.exists(LINKS_GERAIS_PATH):
                    with open(LINKS_GERAIS_PATH, 'r', encoding='utf-8') as f:
                        links = json.load(f)
                        # Busca o link específico do cardápio
                        cardapio_link = links.get("Cardápio da Semana")
                        if cardapio_link:
                            additional_info_parts.append(f"Link direto para o [Cardápio do RU]: {cardapio_link}")
                        else:
                            additional_info_parts.append("Aviso: O link para o Cardápio do RU não foi encontrado no arquivo de links gerais.")
                else:
                    additional_info_parts.append("Aviso: O arquivo de links gerais (links_gerais.json) não foi encontrado.")
            except Exception as e:
                print(f"Erro ao ler links gerais: {e}")
            continue # Pula a busca vetorial para esta categoria, pois usamos o link direto

        try:
            # Busca no banco vetorial correspondente à categoria
            context_results = search_vectors(query=need, category=category, n_results=2)
            if context_results:
                context_text = "\n".join(context_results)
                additional_info_parts.append(f"Informações sobre [{category}]:\n{context_text}")
        except Exception as e:
            # Caso a categoria não esteja mapeada ou ocorra outro erro
            print(f"Erro ao buscar vetores para {category}: {e}")
            continue

    additional_info = "\n\n".join(additional_info_parts) if additional_info_parts else "Nenhuma informação adicional encontrada."

    system_instruction = (
        "Você é o UFChat, um assistente virtual de suporte ao corpo universitário da UFCA (Universidade Federal do Cariri). "
        "Seja prestativo, educado e utilize as informações fornecidas para responder.\n\n"
        "### INFORMAÇÕES DE APOIO (RAG):\n"
        f"{additional_info}\n\n"
        "Utilize as informações acima para embasar sua resposta. Se a informação não estiver presente, "
        "oriente o usuário a procurar os canais oficiais da UFCA."
    )

    history = get_chat_history(user_id)
    
    contents = []

    # Formata o histórico cronologicamente
    for pair in reversed(history):
        contents.append({"role": "user", "parts": [{"text": pair["user"]}]})
        contents.append({"role": "model", "parts": [{"text": pair["agent"]}]})
    
    # Adiciona a mensagem atual
    contents.append({"role": "user", "parts": [{"text": user_message}]})
    
    return system_instruction, contents
