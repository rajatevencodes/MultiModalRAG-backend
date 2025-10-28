from fastapi import APIRouter, HTTPException, Depends
from src.services.supabase import supabase
from src.services.clerkAuth import get_current_user_clerk_id
from src.models.index import ChatCreate
from src.models.index import ChatCreate

router = APIRouter(tags=["chatRoutes"])

"""
`/api/chat`

Create a new chat: POST `/create`
Delete a chat: DELETE `/delete/{chat_id}`
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
