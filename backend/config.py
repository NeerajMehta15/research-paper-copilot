import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()

# Try to fetch DB_PATH from env, fallback if not found
DB_PATH = os.getenv("DB_PATH", "./chroma_store")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
