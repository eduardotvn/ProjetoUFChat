import os
import google.generativeai as genai
from dotenv import load_dotenv
from src.promptbuilder import build_prompt

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-3.1-flash')

async def generate_agent_response(user_id: str, user_message: str, additional_info: str) -> str:

    system_instruction, contents = build_prompt(user_id, user_message, additional_info)
    
    response = model.generate_content(
        contents,
        generation_config=genai.types.GenerationConfig(
            candidate_count=1,
            max_output_tokens=1000,
            temperature=0.7,
        ),
        system_instruction=system_instruction
    )
    
    return response.text

def count_user_request_tokens(text: str) -> int:

    return model.count_tokens(text).total_tokens
