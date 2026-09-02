import json

from google import genai
from google.genai import types

from app.core.config import settings


def analyze_user_message(user_input: str) -> dict:
    """
    Kullanıcının mesajını analiz eder.

    Gemini'den:
    - Message importance score
    - Memories
    - User interests
    - Important topics

    bilgilerini JSON formatında döndürür.
    """

    if not settings.GEMINI_API_KEY:
        return {
            "importance_score": 0.0,
            "memories": [],
            "interests": [],
            "important_topics": [],
        }

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    analysis_prompt = f"""
Analyze the following user message for a long-term AI companion memory system.

User message:
"{user_input}"

Your task is to identify information that may be useful for future conversations.

Rules:

1. importance_score:
   - Score how important this message is for remembering the user.
   - 0.0 = not useful for long-term context
   - 1.0 = highly important personal information
   - Personal preferences, strong opinions, important experiences and recurring interests
     should receive higher scores.
   - Casual greetings or temporary information should receive low scores.

2. memories:
   Extract durable personal information such as:
   - preferences
   - likes
   - dislikes
   - favorite things
   - experiences
   - opinions
   - personal facts

3. interests:
   Identify topics the user appears interested in.
   Examples:
   - movies
   - artificial intelligence
   - football
   - books
   - programming

4. important_topics:
   Identify broader topics that seem important to the user.

5. Never invent information.
   Only extract information explicitly supported by the user's message.

6. If there is nothing relevant, return empty arrays.

Return ONLY valid JSON in exactly this structure:

{{
    "importance_score": 0.0,
    "memories": [
        {{
            "memory_type": "preference",
            "key": "favorite_movie",
            "value": "Interstellar",
            "importance_score": 0.95
        }}
    ],
    "interests": [
        {{
            "topic": "sci-fi movies",
            "interest_level": 0.95
        }}
    ],
    "important_topics": [
        {{
            "topic": "movies",
            "importance_level": 0.80
        }}
    ]
}}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=analysis_prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )

        result = json.loads(response.text)

        return result

    except Exception:
        print(f"Memory Analysis Error: {str(e)}")
        return {
            "importance_score": 0.0,
            "memories": [],
            "interests": [],
            "important_topics": [],
        }