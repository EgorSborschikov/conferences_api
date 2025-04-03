# Data-class (model) for conference
from pydantic import BaseModel

class Conference(BaseModel):
    name: str
