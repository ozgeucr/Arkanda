from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.core.security import get_password_hash
from app.api.deps import get_current_user

# Router nesnemizi oluşturuyoruz
router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    # 1. E-posta adresi sistemde var mı kontrol et
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu e-posta adresi ile zaten bir kayıt mevcut."
        )
    
    # 2. Şifreyi güvenli hale getir (Hash'le)
    hashed_password = get_password_hash(user_in.password)
    
    # 3. Yeni kullanıcı modelini oluştur
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        first_name=user_in.first_name,
        last_name=user_in.last_name
    )
    
    # 4. Veritabanına kaydet
    db.add(new_user)
    db.commit()
    db.refresh(new_user) # Veritabanından (örneğin UUID ve tarih gibi) otomatik oluşturulan verileri geri al
    
    # 5. Yeni kullanıcıyı döndür (Şifre gizlenerek UserResponse şemasına göre dönecek)
    return new_user

@router.get("/me")
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Giriş yapmış kullanıcının profil bilgilerini döndürür."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "message": f"Merhaba {current_user.first_name}, güvenli bölgedesin! 🧡"
    }