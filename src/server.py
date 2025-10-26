from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes.userRoutes import router as userRoutes
from src.routes.projectRoutes import router as projectRoutes

app = FastAPI(
    title="MultiModal RAG",
    description="API for Enterprise-level MultiModal RAG System",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO : Update this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type"],
)
app.include_router(userRoutes, prefix="/api/user")
app.include_router(projectRoutes, prefix="/api/project")


@app.get("/healthcheck")
def read_root():
    return {"message": "🎉 App is working ☺️👌"}
