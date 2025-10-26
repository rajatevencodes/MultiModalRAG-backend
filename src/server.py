from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.userRoutes import router as userRoutes

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

app.include_router(userRoutes, prefix="/user", tags=["User Management"])


@app.get("/healthcheck")
def read_root():
    return {"message": "🎉 App is working ☺️👌"}
