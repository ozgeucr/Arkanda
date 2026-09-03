from app.core.config import settings
from google import genai
from groq import Groq


class AIRouter:
    """
    Arkanda'daki AI servislerini görevlerine göre yönlendirir.

    Conversation  -> Gemini
    Analysis      -> Groq
    Report        -> ileride ayrı AI
    """

    def __init__(self):
        self.gemini_client = None
        self.groq_client = None

        if settings.GEMINI_API_KEY:
            self.gemini_client = genai.Client(
                api_key=settings.GEMINI_API_KEY
            )

        if settings.GROQ_API_KEY:
            self.groq_client = Groq(
                api_key=settings.GROQ_API_KEY
            )

    def get_gemini(self):
        if not self.gemini_client:
            raise RuntimeError(
                "GEMINI_API_KEY is missing in configurations!"
            )

        return self.gemini_client

    def get_groq(self):
        if not self.groq_client:
            raise RuntimeError(
                "GROQ_API_KEY is missing in configurations!"
            )

        return self.groq_client


ai_router = AIRouter()