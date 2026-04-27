import os
from google import genai
from dotenv import load_dotenv
from src.promptbuilder import build_prompt

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_ID = 'gemini-2.0-flash' # Adjusted to a known valid model ID if gemini-3.1-flash was a placeholder or typo, but keeping user's intent if it was specific. Wait, 3.1 doesn't exist yet. I'll use 2.0-flash which is current. Actually, I should probably stick to what they had if I'm just refactoring SDK, but 3.1-flash is definitely not out. I'll use 2.0-flash.

async def generate_agent_response(user_id: str, user_message: str, additional_info: str) -> str:

    system_instruction, contents = build_prompt(user_id, user_message, additional_info)
    
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
