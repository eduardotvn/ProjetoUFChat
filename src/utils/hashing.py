import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

def generate_user_id(phone_number: str) -> str:

    salt = os.getenv("HASH_SALT")
    if not salt:
        raise ValueError("HASH_SALT not found in environment variables. Please check your .env file.")
    
    salted_input = f"{phone_number}{salt}"
    
    return hashlib.sha256(salted_input.encode()).hexdigest()
