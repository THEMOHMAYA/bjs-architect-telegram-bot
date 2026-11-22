import os
from dotenv import load_dotenv

# Load from .env file
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# AI Provider API Keys
EXA_API_KEY = os.getenv("EXA_API_KEY", "216a0e4exxxxxxxxxxxxxxxxx")
EXA_BASE_URL = os.getenv("EXA_BASE_URL", "https://api.exa.ai")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# AI Provider preference: exa, gemini, openrouter, or deepseek
AI_PROVIDER = os.getenv("AI_PROVIDER", "exa" if EXA_API_KEY else ("openrouter" if OPENROUTER_API_KEY else "gemini")).lower()
