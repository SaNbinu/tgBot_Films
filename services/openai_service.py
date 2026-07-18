from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

RECOMMENDATION_CONTEXT = (
    "Ты профессиональный киноэксперт.Рекомендуй только реально существующие фильмы."
    "Если не уверен в рейтинге IMDb, не придумывай число.Не выдумывай фильмы, актеров и годы выхода."
    "Если запрос пользователя неоднозначный, подбери наиболее подходящие варианты."
    "Для каждого фильма укажи: Название, Год, Краткое описание (1–2 предложения), IMDb (только если уверен)"
)

def generate_recommendation(prompt: str):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": RECOMMENDATION_CONTEXT},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()