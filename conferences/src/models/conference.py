# Data-class (model) for conference
from pydantic import BaseModel

class Conference(BaseModel):
    name: str
    room_id: str
    link: str
    active: bool