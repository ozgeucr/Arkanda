import re
from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.models.user_interest import UserInterest
from app.models.important_topic import ImportantTopic


def normalize_text(value: str) -> str:
    """
    Memory, interest ve topic anahtarlarını karşılaştırılabilir
    hale getirir.
    Örnek: "Favorite Movie" -> "favorite movie"
    """
    if not value:
        return ""

    value = value.strip().lower()

    # Alt çizgi ve tireleri boşluğa çevir
    value = value.replace("_", " ")
    value = value.replace("-", " ")

    # Birden fazla boşluğu teke indir
    value = re.sub(r"\s+", " ", value)

    return value


def save_memory(
    db: Session,
    user_id: str,
    memory_type: str,
    key: str,
    value: str,
    importance_score: float,
):
    """
    Kullanıcının long-term memory kaydını oluşturur veya günceller.
    Aynı kullanıcı + aynı key varsa: mevcut memory güncellenir.
    Yoksa: yeni memory oluşturulur.
    """
    normalized_key = normalize_text(key)

    if not normalized_key or not value:
        return None

    memory = (
        db.query(Memory)
        .filter(
            Memory.user_id == user_id,
            Memory.key == normalized_key,
        )
        .first()
    )

    if memory:
        # Mevcut kayıt varsa, eski verinin üzerine yazar
        memory.memory_type = memory_type
        memory.value = value.strip()
        memory.importance_score = importance_score
        return memory

    # Yoksa yeni kayıt oluşturur
    new_memory = Memory(
        user_id=user_id,
        memory_type=memory_type,
        key=normalized_key,
        value=value.strip(),
        importance_score=importance_score,
    )
    db.add(new_memory)
    return new_memory


def save_interest(
    db: Session,
    user_id: str,
    topic: str,
    interest_level: float,
):
    """
    Kullanıcının ilgisini oluşturur veya günceller.
    """
    normalized_topic = normalize_text(topic)

    if not normalized_topic:
        return None

    interest = (
        db.query(UserInterest)
        .filter(
            UserInterest.user_id == user_id,
            UserInterest.topic == normalized_topic,
        )
        .first()
    )

    if interest:
        interest.interest_level = interest_level
        return interest

    new_interest = UserInterest(
        user_id=user_id,
        topic=normalized_topic,
        interest_level=interest_level,
    )
    db.add(new_interest)
    return new_interest


def save_important_topic(
    db: Session,
    user_id: str,
    topic: str,
    importance_level: float,
):
    """
    Kullanıcının uzun vadede önemli olan konularını oluşturur veya günceller.
    """
    normalized_topic = normalize_text(topic)

    if not normalized_topic:
        return None

    important_topic = (
        db.query(ImportantTopic)
        .filter(
            ImportantTopic.user_id == user_id,
            ImportantTopic.topic == normalized_topic,
        )
        .first()
    )

    if important_topic:
        important_topic.importance_level = importance_level
        return important_topic

    new_topic = ImportantTopic(
        user_id=user_id,
        topic=normalized_topic,
        importance_level=importance_level,
    )
    db.add(new_topic)
    return new_topic


def process_analysis(
    db: Session,
    user_id: str,
    analysis: dict,
):
    """
    message_analyzer.py tarafından oluşturulan analiz sonucunu (dict)
    database'e işler. 
    Pydantic tarafından temizlenmiş verileri kabul eder.
    """
    saved_memories = []
    saved_interests = []
    saved_topics = []

    # 1. USER MEMORIES
    for memory_data in analysis.get("memories", []):
        memory = save_memory(
            db=db,
            user_id=user_id,
            memory_type=memory_data.get("memory_type", "fact"),
            key=memory_data.get("key", ""),
            value=memory_data.get("value", ""),
            importance_score=float(memory_data.get("importance_score", 0.0)),
        )
        if memory:
            saved_memories.append(memory)

    # 2. USER INTERESTS
    for interest_data in analysis.get("interests", []):
        interest = save_interest(
            db=db,
            user_id=user_id,
            topic=interest_data.get("topic", ""),
            interest_level=float(interest_data.get("interest_level", 0.0)),
        )
        if interest:
            saved_interests.append(interest)

    # 3. IMPORTANT TOPICS
    for topic_data in analysis.get("important_topics", []):
        topic = save_important_topic(
            db=db,
            user_id=user_id,
            topic=topic_data.get("topic", ""),
            importance_level=float(topic_data.get("importance_level", 0.0)),
        )
        if topic:
            saved_topics.append(topic)

    return {
        "memories": saved_memories,
        "interests": saved_interests,
        "important_topics": saved_topics,
    }