from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Uygulama örneğini oluşturuyoruz
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