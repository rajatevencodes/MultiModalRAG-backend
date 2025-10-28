from fastapi import APIRouter, HTTPException, Depends
from src.services.supabase import supabase
from src.services.clerkAuth import get_current_user_clerk_id
from src.models.index import ProjectCreate

router = APIRouter(tags=["projectFilesRoutes"])

"""
`/api/project`

Get project files: GET `/{project_id}/files`

"""


@router.get("/{project_id}/files")
async def get_project_files(
    project_id: str, current_user_clerk_id: str = Depends(get_current_user_clerk_id)
):
    try:
        project_files_result = (
            supabase.table("project_documents")
            .select("*")
            .eq("project_id", project_id)
            .eq("clerk_id", current_user_clerk_id)
            .order("created_at", desc=True)
            .execute()
        )

        return {
            "success": True,
            "message": "Project files retrieved successfully",
            "data": project_files_result.data,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while retrieving project {project_id} files: {str(e)}",
        )
