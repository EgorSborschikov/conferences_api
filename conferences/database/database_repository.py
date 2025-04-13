import hashlib
import os
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

# Подключение к Supabase
def get_supabase() -> Client:
    return create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Хэширование идентификатора комнаты конференции
def hash_room_id(room_id: str) -> str:
    return hashlib.sha256(room_id.encode()).hexdigest()