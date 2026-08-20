import uuid
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID # PostgreSQL'e özel UUID veri tipi
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Profile
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)

    # Learning Preferences
    native_language = Column(String, default="tr", nullable=False)
    target_language = Column(String, default="en", nullable=False)

    # Account Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # User Preferences
    preferences = Column(
        JSON,
        default=lambda: {
            "theme": "light",
            "ai_personality": "friendly",
            "notifications_enabled": True,
        },
        nullable=False,
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    last_login = Column(DateTime(timezone=True), nullable=True)