from datetime import datetime
from pydantic import BaseModel

# Схема для создания конференции
class ConferenceCreate(BaseModel):
    conferencename: str
    iduser: int  # ID создателя конференции
    conferencelink: str | None = None

    class Config:
        from_attributes = True

# Схема ответа с данными конференции
class ConferenceResponse(ConferenceCreate):
    idconference: int
    createdat: datetime