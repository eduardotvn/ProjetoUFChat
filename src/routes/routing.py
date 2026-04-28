from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from src.utils.hashing import generate_user_id
from src.agentcall import generate_agent_response, count_user_request_tokens
from src.redisdb.memory import add_message_pair

router = APIRouter()

class UserRequest(BaseModel):
    phone_number: str = Field(..., exemplo="5588999999999")
    message: str = Field(..., exemplo="Qual o cardápio do RU hoje?")


@router.post("/user_request")
async def handle_user_request(request: UserRequest):
    try:
        token_count = count_user_request_tokens(request.message)
        if token_count > 1500:
            return {
                "status": "success",
                "response": "Desculpe, mas esta mensagem é muito longa, tente resumi-la ou vamos por partes, tudo bem?"
            }

        user_id = generate_user_id(request.phone_number)
        
        agent_response = await generate_agent_response(user_id, request.message)
        
        add_message_pair(user_id, request.message, agent_response)
        
        return {
            "status": "success",
            "response": agent_response
        }
        
    except HTTPException as e:
        raise e
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
