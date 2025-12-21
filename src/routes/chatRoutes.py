from fastapi import APIRouter, HTTPException, Depends
from src.agents.supervisor_agent.agent import create_supervisor_agent
from src.agents.simple_agent.agent import create_simple_rag_agent
from src.services.supabase import supabase
from src.services.clerkAuth import get_current_user_clerk_id
from src.models.index import ChatCreate, MessageCreate, MessageRole
from src.rag.retrieval.utils import get_project_settings, get_chat_history
from src.config.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["chatRoutes"])

"""
`/api/chat`

Create a new chat: POST `/create`
Delete a chat: DELETE `/delete/{chat_id}`
Get a specific chat: `/{chat_id}`
Create a new message for specific project and specific chat: POST `/{project_id}/chats/{chat_id}/messages/create`
"""


@router.post("/create")
async def create_chat(
    chat: ChatCreate, current_user_clerk_id: str = Depends(get_current_user_clerk_id)
):
    try:
        logger.info("create_chat_started", project_id=chat.project_id)
        chat_insert_data = {
            "title": chat.title,
            "project_id": chat.project_id,
            "clerk_id": current_user_clerk_id,
        }
        chat_creation_result = (
            supabase.table("chats").insert(chat_insert_data).execute()
        )

        if not chat_creation_result.data:
            logger.error("create_chat_failed_supabase", project_id=chat.project_id)
            raise HTTPException(status_code=422, detail="Failed to create chat")

        logger.info("create_chat_success", chat_id=chat_creation_result.data[0]["id"])
        return {
            "success": True,
            "message": "Chat created successfully",
            "data": chat_creation_result.data[0],
        }

    except Exception as e:
        logger.error("create_chat_exception", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while creating chat: {str(e)}",
        )


@router.delete("/delete/{chat_id}")
async def delete_chat(
    chat_id: str, current_user_clerk_id: str = Depends(get_current_user_clerk_id)
):
    try:
        logger.info("delete_chat_started", chat_id=chat_id)
        chat_deletion_result = (
            supabase.table("chats")
            .delete()
            .eq("id", chat_id)
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )
        if not chat_deletion_result.data:
            logger.warning("delete_chat_not_found", chat_id=chat_id)
            raise HTTPException(status_code=404, detail="Chat not found")

        logger.info("delete_chat_success", chat_id=chat_id)
        return {
            "success": True,
            "message": "Chat deleted successfully",
            "data": chat_deletion_result.data[0],
        }
    except Exception as e:
        logger.error(
            "delete_chat_exception", chat_id=chat_id, error=str(e), exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while deleting chat {chat_id}: {str(e)}",
        )


@router.get("/{chat_id}")
async def get_chat(
    chat_id: str, current_user_clerk_id: str = Depends(get_current_user_clerk_id)
):
    try:
        logger.info("get_chat_started", chat_id=chat_id)
        # Verify if the chat exists and belongs to the current user
        # Selecting '*' to embeded the messages in the chat object.
        chat_ownership_verification_result = (
            supabase.table("chats")
            .select("*")
            .eq("id", chat_id)
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )

        if not chat_ownership_verification_result.data:
            logger.warning("get_chat_not_found_or_forbidden", chat_id=chat_id)
            raise HTTPException(
                status_code=404,
                detail="Chat not found or you don't have permission to access it",
            )

        chat_result = chat_ownership_verification_result.data[0]

        messages_result = (
            supabase.table("messages").select("*").eq("chat_id", chat_id).execute()
        )
        chat_result["messages"] = messages_result.data

        logger.info("get_chat_success", chat_id=chat_id)
        return {
            "success": True,
            "message": "Chat retrieved successfully",
            "data": chat_result,
        }

    except Exception as e:
        logger.error("get_chat_exception", chat_id=chat_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while getting chat {chat_id}: {str(e)}",
        )


@router.post("/{project_id}/chats/{chat_id}/messages/create")
async def create_message(
    project_id: str,
    chat_id: str,
    message: MessageCreate,
    current_user_clerk_id: str = Depends(get_current_user_clerk_id),
):
    """
    Step 1 : Insert the message into the database.
    Step 2 : RETRIEVAL PIPELINE based on the agent_type (Simple or Agentic)
    Step 3 : Get Chat History and perform Retrieval
    Step 4 : Invoke the agent_type(Simple or Agentic) for generation (Retrieved Context + User Message)
    Step 5 : Insert the AI Response into the database.
    """
    try:
        logger.info("create_message_started", chat_id=chat_id, project_id=project_id)
        # Step 1 : Insert the message into the database.
        message = message.content
        message_insert_data = {
            "content": message,
            "chat_id": chat_id,
            "clerk_id": current_user_clerk_id,
            "role": MessageRole.USER.value,
        }
        message_creation_result = (
            supabase.table("messages").insert(message_insert_data).execute()
        )

        if not message_creation_result.data:
            logger.error("create_message_failed_user_msg", chat_id=chat_id)
            raise HTTPException(status_code=422, detail="Failed to create message")

        # Step 2 : Get Project Settings from the database - Retrieval will be performed by the agent.
        # Based on the agent_type, Retrieval will be performed by the agent.
        try:
            project_settings = get_project_settings(project_id)
            agent_type = project_settings.get("agent_type", "simple")
        except Exception as e:
            agent_type = "simple"

        chat_history = get_chat_history(chat_id)

        # Invoke the agent_type
        if agent_type == "simple":
            agent = create_simple_rag_agent(project_id, chat_history=chat_history)

        if agent_type == "agentic":
            agent = create_supervisor_agent(project_id, chat_history=chat_history)

        result = agent.invoke({"messages": [{"role": "user", "content": message}]})
        final_response = result["messages"][-1].content
        citations = result.get("citations", [])

        # Step 5: Insert the AI Response into the database.
        ai_response_insert_data = {
            "content": final_response,
            "chat_id": chat_id,
            "clerk_id": current_user_clerk_id,
            "role": MessageRole.ASSISTANT.value,
            "citations": citations,
        }
        ai_response_creation_result = (
            supabase.table("messages").insert(ai_response_insert_data).execute()
        )
        if not ai_response_creation_result.data:
            logger.error("create_message_failed_ai_resp", chat_id=chat_id)
            raise HTTPException(status_code=422, detail="Failed to create AI response")

        logger.info("create_message_success", chat_id=chat_id)
        return {
            "success": True,
            "message": "Message created successfully",
            "data": {
                "userMessage": message_creation_result.data[0],
                "aiResponse": ai_response_creation_result.data[0],
            },
        }

    except Exception as e:
        logger.error(
            "create_message_exception", chat_id=chat_id, error=str(e), exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while creating message: {str(e)}",
        )
