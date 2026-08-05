from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

RECOMMENDATION_CONTEXT = (
    "You are a professional film expert. Recommend only real, existing movies."
    "If you are not sure about the IMDb rating, do not make up a number. Do not invent movies, actors, or release years."
    "If the user request is ambiguous, pick the most suitable options."
    "For each movie provide: Title, Year, Short description (1-2 sentences), IMDb (only if you are sure)"
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