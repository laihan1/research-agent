import os
import httpx
from dotenv import load_dotenv

load_dotenv()

class LLMUnavailable(Exception):
    pass

PROVIDERS = ["groq", "gemini", "openrouter"]

def _call_groq(prompt: str, temperature: float) -> str:
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    resp = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return resp.choices[0].message.content

def _call_gemini(prompt: str, temperature: float) -> str:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    resp = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config=types.GenerateContentConfig(temperature=temperature),
    )
    return resp.text

def _call_openrouter(prompt: str, temperature: float) -> str:
    resp = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
        json={
            "model": "openai/gpt-oss-20b:free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

_CALLERS = {
    "groq": _call_groq,
    "gemini": _call_gemini,
    "openrouter": _call_openrouter,
}

def complete(prompt: str, temperature: float = 0.2) -> str:
    errors = []
    for name in PROVIDERS:
        try:
            return _CALLERS[name](prompt, temperature)
        except Exception as e:
            errors.append(f"{name}: {e}")
    raise LLMUnavailable("; ".join(errors))