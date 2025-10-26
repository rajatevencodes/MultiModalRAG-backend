from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["projectRoutes"])


@router.get("/get_projects")
async def get_projects():
    try:
        # Placeholder for actual project retrieval logic
        projects = [
            {"id": 1, "name": "Project Alpha"},
            {"id": 2, "name": "Project Beta"},
        ]
        return {"projects": projects}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="An error occurred while fetching projects"
        )


@router.post("/create")
async def create_project():
    try:
        # Placeholder for actual project creation logic
        return {"message": "Project created successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="An error occurred while creating project"
        )
