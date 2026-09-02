from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.api.endpoints import user, auth, chat

app = FastAPI(
    title="ARKANDA API",
    description="AI English Tutor Backend System",
    version="1.0.0"
)

# CORS ayarları (Frontend'den gelecek isteklere izin vermek için)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Geliştirme aşamasında her yere açık, canlıda kısıtlanacak
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Kök (Root) endpoint'i
@app.get("/", tags=["General"])
async def root():
    return {"message": "Welcome to ARKANDA 🧡"}

# Sağlık kontrolü (Health Check) endpoint'i
@app.get("/health", tags=["General"])
async def health_check():
    return {
        "status": "ok",
        "service": "ARKANDA"
    }

app.include_router(user.router, prefix="/api/users", tags=["Users"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
