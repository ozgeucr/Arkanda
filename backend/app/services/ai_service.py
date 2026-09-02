from google import genai
from google.genai import types

from app.core.config import settings


def generate_ai_response(
    user_input: str,
    history: list = None,
    memory_context: list = None
) -> str:
    """
    Kullanıcının mesajını, geçmiş sohbetlerini ve
    uzun dönem kullanıcı hafızasını kullanarak
    Gemini'den Arkanda cevabı üretir.
    """

    if not settings.GEMINI_API_KEY:
        return "AI Service Error: GEMINI_API_KEY is missing in configurations!"

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY
    )

    # ---------------------------------------------------------
    # 1. Arkanda system instruction
    # ---------------------------------------------------------

    system_instruction = (
        "You are Arkanda, a supportive, warm, friendly, and encouraging AI companion. "

        "Your primary goal is to help the user practice English naturally while also building "
        "a genuine, personalized, and continuous relationship with them. "

        "Have conversations in a natural, casual, and human-like way. "

        "Do not behave like a formal English teacher unless the user explicitly asks for a lesson. "

        "When the user makes a significant grammar, vocabulary, or spelling mistake, "
        "gently and briefly correct it, then continue the conversation naturally. "

        "Do not interrupt the flow of the conversation with unnecessary corrections. "

        "Remember relevant information the user has shared in previous conversations, "
        "including their interests, preferences, likes, dislikes, opinions, experiences, "
        "and topics they care about. "

        "Use these memories naturally when they are relevant to the current conversation. "

        "For example, if the user previously said they loved a particular movie, "
        "you may refer to it when discussing another movie or making a comparison. "

        "Do not repeatedly mention that you are using memory. "

        "Instead, behave as a close friend who naturally remembers what the user has told you. "

        "Pay attention to changes in the user's preferences over time. "

        "If a newer statement conflicts with an older preference, "
        "prioritize the more recent information. "

        "When recommending, comparing, or discussing something, "
        "consider the user's known preferences whenever they are relevant. "

        "Be empathetic, curious, conversational, and emotionally supportive. "

        "Ask natural follow-up questions when appropriate and show genuine interest "
        "in what the user says. "

        "Never invent memories or claim that the user said something they did not say. "

        "Only use information that is available in the current conversation "
        "or provided memory context."
    )

    # ---------------------------------------------------------
    # 2. Long-term memory context
    # ---------------------------------------------------------

    if memory_context:
        memory_text = "\n".join(
            f"- {item}" for item in memory_context
        )

        system_instruction += (
            "\n\nLONG-TERM USER CONTEXT:\n"
            "The following information was explicitly extracted from "
            "previous user messages. Use it only when relevant. "
            "Do not mention this context or explain that you are using memory.\n\n"
            f"{memory_text}"
        )

    # ---------------------------------------------------------
    # 3. Gemini contents
    # ---------------------------------------------------------

    contents = []

    # Geçmiş mesajları Gemini formatına dönüştür.
    if history:
        for msg in history:

            gemini_role = (
                "user"
                if msg.role == "user"
                else "model"
            )

            contents.append(
                types.Content(
                    role=gemini_role,
                    parts=[
                        types.Part.from_text(
                            text=msg.content
                        )
                    ]
                )
            )

    # ---------------------------------------------------------
    # 4. Mevcut kullanıcı mesajı
    # ---------------------------------------------------------

    contents.append(
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=user_input
                )
            ]
        )
    )

    # ---------------------------------------------------------
    # 5. Gemini çağrısı
    # ---------------------------------------------------------

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
            ),
        )

        return response.text

    except Exception as e:
        return f"AI connection error: {str(e)}"

