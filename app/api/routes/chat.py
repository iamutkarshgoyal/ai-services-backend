from fastapi import FastAPI
import uuid
from app.graphs.node import app as graph_app, AgentState
from langgraph.types import Command
from app.graphs.approvals import Invoice_update_approval

app = FastAPI()

@app.post("/new_conversation")
def new_conversation():
    conversation_id = str(uuid.uuid4())
    return {"conversation_id": conversation_id}


@app.post("/chat")
def chat_endpoint(request: "AgentState"):
    """
    This endpoint receives a chat request, classifies the topic of the message, and returns a response along with the conversation ID and topic.
    Args: request (ChatRequest): The chat request containing the conversation ID and message.
    Returns: dict: A dictionary containing the conversation ID, message, response, and topic.
    """
    config = {"configurable": {"thread_id": request.conversation_id}}
    try:
        result = graph_app.invoke(
            {"message": request.message,
             "conversation_id": request.conversation_id},
            config=config)
        
        while result.get("__interrupt__"):
            interrupts = result["__interrupt__"]
            return {"status": "interrupted", "conversation_id" : request.conversation_id, 
                    "interrupts" : [
                        {"id" : item.id, "value" : item.value}
                        for item in interrupts
                    ]}

        return {"conversation_id": request.conversation_id, "message": request.message, "result" : result}
    
    except Exception as e:
        return {"conversation_id": request.conversation_id, "message": request.message, "response": f"Error: {str(e)}", "topic": None}


@app.post("/approval_status")
def approval_status(state: Invoice_update_approval, conversation_id: str):
    config = {"configurable": {"thread_id": conversation_id}}
    result = graph_app.invoke(Command(
                resume={"approved": state.approved}
            ), config=config,)

    return result

