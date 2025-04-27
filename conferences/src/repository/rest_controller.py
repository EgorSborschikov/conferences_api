import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client
from conferences.src.schema.delete_conference import DeleteConferenceRequest, DeleteConferenceResponse
from conferences.src.schema.update_conference_name import UpdateConferenceNameRequest, UpdateConferenceNameResponse
from conferences.database.database_repository import get_supabase, hash_room_id
from conferences.src.schema.create_conference import ConferenceRequest, ConferenceResponse

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание новой конференции
@router.post("/create_conference", response_model=ConferenceResponse)
async def create_conference(
    conference: ConferenceRequest,
    supabase: Client = Depends(get_supabase)
):
    logger.info(f"Received data: {conference}")

    try:
        # Генерация уникального ID для комнаты
        room_id = str(uuid.uuid4())
        hashed_room_id = hash_room_id(room_id)

        # Формирование ссылки для присоединения к конференции
        link = f"127.0.0.1/join/{hashed_room_id}"

        # Создание объекта конференции
        new_conference = ConferenceResponse(
            name=conference.name,
            room_id=hashed_room_id,
            link=link,
            active=True,
            users=1,  # Создающий пользователь сразу учитывается
            created_by=str(conference.created_by)  # Добавление created_by
        )
        logger.info(f"Конференция {room_id} создана")

        # Сохранение данных в Supabase
        response = supabase.table('conferences').insert({
            "room_id": hashed_room_id,
            "name": conference.name,
            "link": link,
            "active": True,
            "users": 1,
            "created_by": str(conference.created_by)  # Сохранение created_by
        }).execute()

        if hasattr(response, 'error') and response.error:
            raise HTTPException(
                status_code=500,
                detail="Ошибка при создании конференции в Supabase"
            )

        # Возврат данных конференции
        return new_conference
    except Exception as e:
        logger.error(f"Ошибка создания конференции: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании конференции: {str(e)}"
        )

# Изменение названия конференции
@router.put("/update_conference_name", response_model=UpdateConferenceNameResponse)
async def update_conference_name(
    update_request: UpdateConferenceNameRequest,
    supabase: Client = Depends(get_supabase)
):
    logger.info(f"Received update request: {update_request}")

    try:
        # Обновление названия конференции в Supabase
        response = supabase.table('conferences').update({
            "name": update_request.new_name
        }).eq('room_id', update_request.room_id).execute()

        if hasattr(response, 'error') and response.error:
            raise HTTPException(
                status_code=500,
                detail="Ошибка при обновлении названия конференции в Supabase"
            )

        # Возврат обновленных данных конференции
        return UpdateConferenceNameResponse(
            room_id=update_request.room_id,
            name=update_request.new_name,
            message="Название конференции успешно обновлено"
        )
    except Exception as e:
        logger.error(f"Ошибка обновления названия конференции: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обновлении названия конференции: {str(e)}"
        )
    
# Удаление конференции
@router.delete("/delete_conference", response_model=DeleteConferenceResponse)
async def delete_conference(
    delete_request: DeleteConferenceRequest,
    supabase: Client = Depends(get_supabase)
):
    logger.info(f"Received delete request: {delete_request}")

    try:
        # Удаление конференции из Supabase
        response = supabase.table('conferences').delete().eq('room_id', delete_request.room_id).execute()

        if hasattr(response, 'error') and response.error:
            raise HTTPException(
                status_code=500,
                detail="Ошибка при удалении конференции из Supabase"
            )

        # Возврат подтверждения удаления
        return DeleteConferenceResponse(
            room_id=delete_request.room_id,
            message="Конференция успешно удалена"
        )
    except Exception as e:
        logger.error(f"Ошибка удаления конференции: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при удалении конференции: {str(e)}"
        )

# Присоединение пользователя к существующей конференции
@router.get("/join_conference/{room_id}")
async def join_conference(
    room_id: str,
    supabase: Client = Depends(get_supabase)
    ):
    logger.info(f"attemping to join conference with room_id : {room_id}")

    try:
        # Проверка существования конференции
        conference = supabase.table('conferences').select("*").eq("room_id", room_id).single().execute()

        if not conference.data or not conference.data['active']:
            raise HTTPException(
                status_code = 404,
                detail = "Конференция не найдена или не активна"
            )

        response = supabase.table('conferences').update({
            "users": conference.data['users'] + 1
        }).eq("room_id", room_id).execute()

        if hasattr(response, 'error') and response.error:
            raise HTTPException(
                status_code=500,
                detail="Ошибка при обновлении данных в Supabase"
            )

        logger.info(f"User  successfully joined conference with room_id: {room_id}")
        return {"status": "Присоединение успешно"}
    
    except Exception as e:
        logger.error(f"Error joining conference: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка при присоединении к конференции: {str(e)}"
        )

# Покидание пользователем конференции
@router.post("/leave_conference/{room_id}")
async def leave_conference(
    room_id: str, 
    supabase: Client = Depends(get_supabase)
    ):

    try:
        # Проверка существования конференции
        conference = supabase.table('conferences').select("*").eq("room_id", room_id).single().execute()

        if not conference.data or not conference.data['active']:
            raise HTTPException(
                status_code=404,
                detail="Конференция не найдена или не активна"
            )
        
        # Уменьшение количества пользователей в конференции
        response = supabase.table('conferences').update({
            "users": conference.data['users'] - 1
        }).eq("room_id", room_id).execute()

        if hasattr(response, 'error') and response.error:
            raise HTTPException(
                status_code=500,
                detail="Ошибка при обновлении данных в Supabase"
            )

        # Удаление конференции, если не осталось пользователей
        if conference.data['users'] - 1 == 0:
            supabase.table('conferences').update({
                "active": False
            }).eq("room_id", room_id).execute()

        logger.info(f"User  successfully left conference with room_id: {room_id}")
        return {"status": "Выход успешен"}

    except Exception as e:
        logger.error(f"Error leaving conference: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при выходе из конференции: {str(e)}"
        )

# Получение списка активных конференций с фильтрацией по пользователю
@router.get("/list_conferences")
async def list_conferences(
    created_by: str = Query(None, description="Filter by created_by"),
    supabase: Client = Depends(get_supabase)
):
    try:
        # Логирование значения created_by
        print(f"Filtering by created_by: {created_by}")

        # Построение запроса с учетом фильтрации по created_by
        query = supabase.table('conferences').select("*").eq("active", True)

        if created_by:
            query = query.eq("created_by", created_by)

        # Логирование запроса
        print(f"Executing query: {query}")

        # Выполнение запроса
        response = query.execute()

        # Проверка наличия ошибок в ответе
        if hasattr(response, 'error') and response.error:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при получении данных из Supabase: {response.error.message}"
            )

        # Возврат данных конференций
        return response.data

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении списка активных конференций: {str(e)}"
        )