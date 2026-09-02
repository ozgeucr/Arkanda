from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.chat import Conversation, Message
from app.models.memory import Memory
from app.models.user_interest import UserInterest
from app.models.important_topic import ImportantTopic

from app.schemas.chat import (
    ConversationResponse,
    ConversationCreate,
    MessageResponse,
    MessageCreate
)

from app.services.ai_service import generate_ai_response
from app.services.message_analyzer import analyze_user_message

router = APIRouter()

@router.post("/new", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    chat_in: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Giriş yapmış kullanıcı için yeni bir sohbet oturumu başlatır."""
    new_chat = Conversation(
        title=chat_in.title,
        user_id=current_user.id
    )
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat

@router.get("/history", response_model=List[ConversationResponse])
def get_my_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kullanıcının geçmiş sohbet oturumlarını listeler."""
    chats = db.query(Conversation).filter(Conversation.user_id == current_user.id).all()
    return chats

@router.post(
    "/{conversation_id}/message",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED
)
def send_message_to_chat(
    conversation_id: str,
    message_in: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Kullanıcının mesajını kaydeder, analiz eder ve
    kullanıcıya ait memory, interest ve important topic
    bilgilerini Gemini context'ine dahil ederek cevap üretir.
    """

    # ---------------------------------------------------------
    # 1. Sohbet kontrolü
    # ---------------------------------------------------------

    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sohbet oturumu bulunamadı veya bu sohbete erişim yetkiniz yok."
        )

    # ---------------------------------------------------------
    # 2. Kullanıcı mesajını oluştur
    # ---------------------------------------------------------

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=message_in.content,
        importance_score=0.0
    )

    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # ---------------------------------------------------------
    # 3. Kullanıcı mesajını analiz et
    # ---------------------------------------------------------

    analysis = analyze_user_message(message_in.content)

    # ---------------------------------------------------------
    # 4. Message importance score güncelle
    # ---------------------------------------------------------

    user_message.importance_score = analysis.get(
        "importance_score",
        0.0
    )

    db.commit()
    db.refresh(user_message)

    # ---------------------------------------------------------
    # 5. Memory kayıtlarını oluştur / güncelle
    # ---------------------------------------------------------

    for memory_data in analysis.get("memories", []):

        existing_memory = db.query(Memory).filter(
            Memory.user_id == current_user.id,
            Memory.key == memory_data["key"]
        ).first()

        if existing_memory:
            existing_memory.value = memory_data["value"]
            existing_memory.importance_score = memory_data.get(
                "importance_score",
                existing_memory.importance_score
            )

        else:
            new_memory = Memory(
                user_id=current_user.id,
                memory_type=memory_data.get(
                    "memory_type",
                    "fact"
                ),
                key=memory_data["key"],
                value=memory_data["value"],
                importance_score=memory_data.get(
                    "importance_score",
                    0.0
                )
            )

            db.add(new_memory)

    # ---------------------------------------------------------
    # 6. Interest kayıtlarını oluştur / güncelle
    # ---------------------------------------------------------

    for interest_data in analysis.get("interests", []):

        existing_interest = db.query(UserInterest).filter(
            UserInterest.user_id == current_user.id,
            UserInterest.topic == interest_data["topic"]
        ).first()

        if existing_interest:
            existing_interest.interest_level = interest_data.get(
                "interest_level",
                existing_interest.interest_level
            )

        else:
            new_interest = UserInterest(
                user_id=current_user.id,
                topic=interest_data["topic"],
                interest_level=interest_data.get(
                    "interest_level",
                    0.0
                )
            )

            db.add(new_interest)

    # ---------------------------------------------------------
    # 7. Important Topic kayıtlarını oluştur / güncelle
    # ---------------------------------------------------------

    for topic_data in analysis.get("important_topics", []):

        existing_topic = db.query(ImportantTopic).filter(
            ImportantTopic.user_id == current_user.id,
            ImportantTopic.topic == topic_data["topic"]
        ).first()

        if existing_topic:
            existing_topic.importance_level = topic_data.get(
                "importance_level",
                existing_topic.importance_level
            )

        else:
            new_topic = ImportantTopic(
                user_id=current_user.id,
                topic=topic_data["topic"],
                importance_level=topic_data.get(
                    "importance_level",
                    0.0
                )
            )

            db.add(new_topic)

    db.commit()

    # ---------------------------------------------------------
    # 8. Son 3 mesaj
    # ---------------------------------------------------------

    recent_messages = db.query(Message).filter(
        Message.conversation_id == conversation.id,
        Message.id != user_message.id
    ).order_by(
        Message.created_at.desc()
    ).limit(3).all()

    recent_messages.reverse()

    # ---------------------------------------------------------
    # 9. En önemli 5 mesaj
    # ---------------------------------------------------------

    important_messages = db.query(Message).filter(
        Message.conversation_id == conversation.id,
        Message.id != user_message.id,
        Message.importance_score > 0
    ).order_by(
        Message.importance_score.desc(),
        Message.created_at.desc()
    ).limit(5).all()

    important_messages.reverse()

    # ---------------------------------------------------------
    # 10. Mesaj context'lerini birleştir
    # ---------------------------------------------------------

    context_messages = []
    seen_message_ids = set()

    for message in recent_messages + important_messages:

        if message.id not in seen_message_ids:
            context_messages.append(message)
            seen_message_ids.add(message.id)

    # ---------------------------------------------------------
    # 11. Kullanıcı Memory'lerini getir
    # ---------------------------------------------------------

    memories = db.query(Memory).filter(
        Memory.user_id == current_user.id
    ).order_by(
        Memory.importance_score.desc()
    ).limit(10).all()

    # ---------------------------------------------------------
    # 12. Kullanıcı Interest'lerini getir
    # ---------------------------------------------------------

    interests = db.query(UserInterest).filter(
        UserInterest.user_id == current_user.id
    ).order_by(
        UserInterest.interest_level.desc()
    ).limit(10).all()

    # ---------------------------------------------------------
    # 13. Important Topic'leri getir
    # ---------------------------------------------------------

    important_topics = db.query(ImportantTopic).filter(
        ImportantTopic.user_id == current_user.id
    ).order_by(
        ImportantTopic.importance_level.desc()
    ).limit(10).all()

    # ---------------------------------------------------------
    # 14. Memory context oluştur
    # ---------------------------------------------------------

    memory_context = []

    for memory in memories:
        memory_context.append(
            f"Memory: {memory.key} = {memory.value}"
        )

    for interest in interests:
        memory_context.append(
            f"User interest: {interest.topic} "
            f"(interest level: {interest.interest_level})"
        )

    for topic in important_topics:
        memory_context.append(
            f"Important topic: {topic.topic} "
            f"(importance level: {topic.importance_level})"
        )

    # ---------------------------------------------------------
    # 15. Gemini'den yanıt al
    # ---------------------------------------------------------

    ai_reply_text = generate_ai_response(
        user_input=message_in.content,
        history=context_messages,
        memory_context=memory_context
    )

    # ---------------------------------------------------------
    # 16. AI mesajını kaydet
    # ---------------------------------------------------------

    ai_message = Message(
        conversation_id=conversation.id,
        role="ai",
        content=ai_reply_text
    )

    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)

    # ---------------------------------------------------------
    # 17. Yanıt
    # ---------------------------------------------------------

    return ai_message