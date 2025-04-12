# Модель запроса для обновления названия конференции
from pydantic import BaseModel

class UpdateConferenceNameRequest(BaseModel):
    room_id: str
    new_name: str

# Модель ответа для обновления названия конференции
class UpdateConferenceNameResponse(BaseModel):
    room_id: str
    name: str
    message: str