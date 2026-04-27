from src.redisdb.memory import get_chat_history

def build_prompt(user_id: str, user_message: str, additional_info: str) -> tuple[str, list]:

    
    system_instruction = (
        "Você é o UFChat, um assistente virtual de suporte ao corpo universitário da UFCA (Universidade Federal do Cariri). "
        "Seja prestativo, educado e utilize as informações fornecidas para responder.\n\n"
        f"Informação adicional: {additional_info}\n\n"
        "Este é o contexto da conversa, responda a requisição do usuário com a informação de apoio."
    )

    history = get_chat_history(user_id)
    
    contents = []

    for pair in reversed(history):
        contents.append({"role": "user", "parts": [pair["user"]]})
        contents.append({"role": "model", "parts": [pair["agent"]]})
    
    contents.append({"role": "user", "parts": [user_message]})
    
    return system_instruction, contents
