from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Veritabanı motorunu oluşturuyoruz
engine = create_engine(settings.DATABASE_URL)

# Veritabanı ile konuşacak oturum (session) fabrikası
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tüm modellerimizin (User, Conversation vb.) türeyeceği temel sınıf
Base = declarative_base()

# Her API isteğinde bağımlılık (Dependency) olarak kullanılacak veritabanı bağlantı fonksiyonu
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()