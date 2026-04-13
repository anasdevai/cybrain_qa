from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routes import router
from .public_routes import public_router

app = FastAPI(
    title="Cybrain QS API",
    description="SOP Editor + Stage 1 Public Chatbot Data Provisioning API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://65.21.244.158",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
app.include_router(router)
app.include_router(public_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "status": "ok",
        "message": "Cybrain QS API is running",
        "version": "1.0.0",
        "docs": "/docs",
        
    }
