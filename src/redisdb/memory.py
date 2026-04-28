import os
import json
import redis
from typing import List, Dict, Optional
from dotenv import load_dotenv
from src.utils.hashing import generate_user_id

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)

def add_message_pair(user_id: str, user_message: str, agent_response: str) -> str:

    key = f"chat_history:{user_id}"
    
    pair = {
        "user": user_message,
        "agent": agent_response
    }
    
    redis_client.lpush(key, json.dumps(pair))
  
    redis_client.ltrim(key, 0, 4)
    
    return user_id

def get_chat_history(user_id: str) -> List[Dict[str, str]]:

    key = f"chat_history:{user_id}"
    history_raw = redis_client.lrange(key, 0, -1)
    
    return [json.loads(pair) for pair in history_raw]

def delete_chat_history(user_id: str) -> bool:

    key = f"chat_history:{user_id}"
    return bool(redis_client.delete(key))
