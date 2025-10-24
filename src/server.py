from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="MultiModal RAG",
    description="API for Enterprise-level MultiModal RAG System",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type"],
)

print("hello from server.py")


@app.get("/healthcheck")
def read_root():
    return {"message": "🎉 App is working ☺️👌"}
