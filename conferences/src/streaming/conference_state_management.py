# State management of conferences

from typing import Dict

active_conferences: Dict[str, Dict] = {}
active_streams: Dict[str, Dict] = {}

def generate_unique_room_id() -> str:
    import uuid
    return str(uuid.uuid4())
