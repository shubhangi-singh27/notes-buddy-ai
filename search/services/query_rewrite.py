import os
import logging
from openai import OpenAI
from django.conf import settings

logger = logging.getLogger("search")

openai_api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)
client = OpenAI(api_key=openai_api_key)

def rewrite_query(question: str) -> str:
    question = question.strip()

    if len(question.split()) >= 8:
        return question

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=50,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You rewrite short vague questions into clear, specific questions "
                        "for a knowledge retrieval system.\n"
                        "Do NOT answer the question.\n"
                        "Do NOT add new facts.\n"
                        "Only expand or clarify the question.\n"
                        "Keep it concise."
                    )
                },
                {
                    "role": "user",
                    "content": f"Original question: {question}\nRewrite:"
                }
            ]
        )

        rewritten = response.choices[0].message.content.strip()

        logger.info(f"Rewrote the question: {question} -> {rewritten}")
        
        return rewritten if rewritten else question

    except Exception as e:
        logger.error(f"Failed to rewrite question: {e}")
        return question
