import json

from google import genai
from google.genai import types
from pydantic import BaseModel, field_validator
from typing import List

from app.core.config import settings
from app.services.ai_router import ai_router

# --- PYDANTIC ŞEMALARI (Skorları Normalleştirmek İçin) ---
class MemoryItem(BaseModel):
    memory_type: str
    key: str
    value: str
    importance_score: float = 0.0

    @field_validator("importance_score", mode="before")
    @classmethod
    def normalize_score(cls, v):
        if v > 1.0: return min(v / 10.0, 1.0)
        return max(0.0, min(float(v), 1.0))

class InterestItem(BaseModel):
    topic: str
    interest_level: float = 0.0

    @field_validator("interest_level", mode="before")
    @classmethod
    def normalize_score(cls, v):
        if v > 1.0: return min(v / 10.0, 1.0)
        return max(0.0, min(float(v), 1.0))

class TopicItem(BaseModel):
    topic: str
    importance_level: float = 0.0

    @field_validator("importance_level", mode="before")
    @classmethod
    def normalize_score(cls, v):
        if v > 1.0: return min(v / 10.0, 1.0)
        return max(0.0, min(float(v), 1.0))

class AIAnalysisResult(BaseModel):
    importance_score: float = 0.0
    memories: List[MemoryItem] = []
    interests: List[InterestItem] = []
    important_topics: List[TopicItem] = []

    @field_validator("importance_score", mode="before")
    @classmethod
    def normalize_score(cls, v):
        if v > 1.0: return min(v / 10.0, 1.0)
        return max(0.0, min(float(v), 1.0))
# ---------------------------------------------------------

def analyze_user_message(user_input: str) -> dict:
    """
    Kullanıcının mesajını uzun dönem hafıza sistemi için analiz eder.

    Groq:
    - importance_score
    - memories
    - interests
    - important_topics

    bilgilerini JSON formatında üretir.
    """

    if not user_input or not user_input.strip():
        return AIAnalysisResult().model_dump()

    try:
        client = ai_router.get_groq()

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",

            messages=[
                {
                    "role": "system",
                    "content": """
You are the memory analysis engine of an AI companion application.

Your job is NOT to answer the user.

Your only job is to analyze the user's message and extract
information that can be useful for future conversations.

Extract:

1. importance_score
2. memories
3. interests
4. important_topics

Rules:

- Never invent information.
- Only extract information explicitly supported by the user's message.
- Casual greetings should have a very low importance score.
- Temporary information should normally not be stored as long-term memory.
- Strong preferences should have a high importance score.
- Strong likes and dislikes should have a high importance score.
- Personal experiences may be stored if they could matter in future conversations.
- Opinions may be stored if they reveal a stable preference.
- Interests should represent topics the user genuinely appears interested in.
- Important topics should represent broader subjects that may matter over time.
- Keep extracted values concise.
- Do not extract information about the AI itself.
"""
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ],

            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "arkanda_memory_analysis",
                    "strict": True,
                    "schema": {
                        "type": "object",

                        "properties": {
                            "importance_score": {
                                "type": "number"
                            },

                            "memories": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "memory_type": {
                                            "type": "string"
                                        },
                                        "key": {
                                            "type": "string"
                                        },
                                        "value": {
                                            "type": "string"
                                        },
                                        "importance_score": {
                                            "type": "number"
                                        }
                                    },
                                    "required": [
                                        "memory_type",
                                        "key",
                                        "value",
                                        "importance_score"
                                    ],
                                    "additionalProperties": False
                                }
                            },

                            "interests": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "topic": {
                                            "type": "string"
                                        },
                                        "interest_level": {
                                            "type": "number"
                                        }
                                    },
                                    "required": [
                                        "topic",
                                        "interest_level"
                                    ],
                                    "additionalProperties": False
                                }
                            },

                            "important_topics": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "topic": {
                                            "type": "string"
                                        },
                                        "importance_level": {
                                            "type": "number"
                                        }
                                    },
                                    "required": [
                                        "topic",
                                        "importance_level"
                                    ],
                                    "additionalProperties": False
                                }
                            }
                        },

                        "required": [
                            "importance_score",
                            "memories",
                            "interests",
                            "important_topics"
                        ],

                        "additionalProperties": False
                    }
                }
            },

            temperature=0.1,
            max_tokens=1000
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError("Groq returned an empty response.")

        # JSON'ı Python sözlüğüne çevir
        raw_data = json.loads(content)
        
        # Sözlüğü Pydantic modelinden geçir (8.5 gibi hatalı skorlar burada 0.85'e dönüşür)
        validated_data = AIAnalysisResult(**raw_data)
        
        # Temizlenmiş ve doğrulanmış veriyi dict olarak döndür
        return validated_data.model_dump()

    except Exception as e:

        print(f"Message analysis error: {e}")

        return AIAnalysisResult().model_dump()