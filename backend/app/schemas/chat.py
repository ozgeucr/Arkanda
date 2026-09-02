from pydantic import BaseModel, UUID4, ConfigDict
from typing import List, Optional
from datetime import datetime

# --- MESAJ ŞEMALARI (Message) ---

class MessageBase(BaseModel):
    role: str
    content: str

class MessageCreate(BaseModel):
    # Kullanıcıdan sadece mesaj metnini alacağız, rolünü (user) biz backend'de atayacağız
    content: str

class MessageResponse(MessageBase):
    id: UUID4
    conversation_id: UUID4
    created_at: datetime
    
    # SQLAlchemy objelerini Pydantic modeline dönüştürmek için gerekli ayar
    model_config = ConfigDict(from_attributes=True)

# --- SOHBET OTURUMU ŞEMALARI (Conversation) ---

class ConversationBase(BaseModel):
    title: str

class ConversationCreate(ConversationBase):
    pass

class ConversationResponse(ConversationBase):
    id: UUID4
    user_id: UUID4
    created_at: datetime
    # Bir sohbet çekildiğinde içindeki mesajları da listele
    messages: List[MessageResponse] = []
    
    model_config = ConfigDict(from_attributes=True)