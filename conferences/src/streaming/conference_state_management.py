# State management of conferences
import uuid
from typing import Dict

active_conferences: Dict[str, Dict] = {}
active_streams: Dict[str, Dict] = {}

def generate_unique_room_id() -> str:
    return str(uuid.uuid4())