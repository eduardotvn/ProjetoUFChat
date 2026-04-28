import os
from google import genai
from dotenv import load_dotenv
from src.promptbuilder import build_prompt
from src.semanticrouter import route_request

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_ID = 'gemini-flash-latest'

async def generate_agent_response(user_id: str, user_message: str) -> str:
    
    router_results = route_request(user_id, user_message)
    
    system_instruction, contents = build_prompt(user_id, user_message, router_results)
    
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=contents,
        config={
            'candidate_count': 1,
            'max_output_tokens': 1000,
            'temperature': 0.7,
            'system_instruction': system_instruction
        }
    )
    
    return response.text

def count_user_request_tokens(text: str) -> int:

    return client.models.count_tokens(model=MODEL_ID, contents=text).total_tokens
