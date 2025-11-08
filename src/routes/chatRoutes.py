from fastapi import APIRouter, HTTPException, Depends
from src.services.supabase import supabase
from src.services.clerkAuth import get_current_user_clerk_id
from src.models.index import ChatCreate, MessageCreate, MessageRole
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.services.llm import openAI
from src.rag.retrieval.index import retrieve_context
from src.rag.retrieval.utils import prepare_prompt_and_invoke_llm

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
        chat_insert_data = {
            "title": chat.title,
            "project_id": chat.project_id,
            "clerk_id": current_user_clerk_id,
        }
        chat_creation_result = (
            supabase.table("chats").insert(chat_insert_data).execute()
        )

        if not chat_creation_result.data:
            raise HTTPException(status_code=422, detail="Failed to create chat")

        return {
            "success": True,
            "message": "Chat created successfully",
            "data": chat_creation_result.data[0],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while creating chat: {str(e)}",
        )


@router.delete("/delete/{chat_id}")
async def delete_chat(
    chat_id: str, current_user_clerk_id: str = Depends(get_current_user_clerk_id)
):
    try:
        chat_deletion_result = (
            supabase.table("chats")
            .delete()
            .eq("id", chat_id)
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )
        if not chat_deletion_result.data:
            raise HTTPException(status_code=404, detail="Chat not found")

        return {
            "success": True,
            "message": "Chat deleted successfully",
            "data": chat_deletion_result.data[0],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while deleting chat {chat_id}: {str(e)}",
        )


@router.get("/{chat_id}")
async def get_chat(
    chat_id: str, current_user_clerk_id: str = Depends(get_current_user_clerk_id)
):
    try:
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
            raise HTTPException(
                status_code=404,
                detail="Chat not found or you don't have permission to access it",
            )

        chat_result = chat_ownership_verification_result.data[0]

        messages_result = (
            supabase.table("messages").select("*").eq("chat_id", chat_id).execute()
        )
        chat_result["messages"] = messages_result.data

        return {
            "success": True,
            "message": "Chat retrieved successfully",
            "data": chat_result,
        }

    except Exception as e:
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
    Step 2 : get user's project settings from the database.
    Step 3 : Retrieval
    Step 4 : Generation (Retrieved Context + User Message)
    Step 5 : Insert the AI Response into the database.
    """
    try:
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
            raise HTTPException(status_code=422, detail="Failed to create message")

        # Step 3 : Retrieval
        texts, images, tables, citations = retrieve_context(project_id, message)

        # Step 4 : Generation (Retrived Context + User Message)
        final_response = prepare_prompt_and_invoke_llm(
            user_query=message, texts=texts, images=images, tables=tables
        )

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
            raise HTTPException(status_code=422, detail="Failed to create AI response")

        return {
            "success": True,
            "message": "Message created successfully",
            "data": {
                "userMessage": message_creation_result.data[0],
                "aiResponse": ai_response_creation_result.data[0],
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while creating message: {str(e)}",
        )
