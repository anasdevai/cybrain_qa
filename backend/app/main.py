from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routes import router
from .public_routes import public_router
from .ai_routes import ai_router
from .auth_routes import router as auth_router
from .chat_history_routes import router as chat_history_router

app = FastAPI(
    title="Cybrain QS API",
    description="SOP Editor + Stage 1 Public Chatbot Data Provisioning API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
app.include_router(router)
app.include_router(public_router)
app.include_router(ai_router)
app.include_router(chat_history_router)
app.include_router(auth_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "status": "ok",
        "message": "Cybrain QS API is running",
        "version": "1.0.0",
        "docs": "/api/docs",
        
    }


