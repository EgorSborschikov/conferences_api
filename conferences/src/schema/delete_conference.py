# Модель запроса для удаления конференции
from pydantic import BaseModel


class DeleteConferenceRequest(BaseModel):
    room_id: str

# Модель ответа для удаления конференции
class DeleteConferenceResponse(BaseModel):
    room_id: str
    message: str