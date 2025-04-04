import hashlib
import logging
from typing import Dict
import uuid
from fastapi import APIRouter, Depends, HTTPException, WebSocket
from fastapi.responses import JSONResponse
from conferences.src.models.conference import ConferenceRequest, ConferenceResponse
from conferences.src.streaming.signal_server import manager
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Временные словари (загрушки)
active_conferences: Dict[str, Dict] = {}
active_streams: Dict[str, WebSocket] = {}

load_dotenv()

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_supabase() -> Client:
    return create_client(os.getenv("supabase_url"), os.getenv("supabase_key"))

def hash_room_id(room_id: str) -> str:
    return hashlib.sha256(room_id.encode()).hexdigest()

# Создание новой конференции
@router.post("/create_conference", response_model=ConferenceResponse)
async def create_conference(
    conference: ConferenceRequest,
    supabase: Client = Depends(get_supabase)
):
    logger.info(f"Received data: {conference}")

    try:
        # Проверка на превышение лимита активных конференций
        if len(active_conferences) > 2:
            raise HTTPException(
                status_code=400,
                detail="Достигнут лимит активных конференций"
            )

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

# Получение списка активных конференций
@router.get("/list_conferences")
async def list_conferences(supabase: Client = Depends(get_supabase)):
    try:
        # Получение списка всех активных конференций
        response = supabase.table('conferences').select("*").eq("active", True).execute()

        # Проверка наличия ошибок в ответе
        if hasattr(response, 'error') and response.error:
            raise HTTPException(status_code=500, detail=f"Ошибка при получении данных из Supabase: {response.error.message}")

        # Возврат данных конференций
        return response.data

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении списка активных конференций: {str(e)}"
        )

# Прием бинарных данных (аудио и видео) от участника и передача их остальным участникам комнаты
@router.websocket("/ws/publish/{room_id}")
async def websocket_publish(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)
    active_streams[room_id] = websocket

    try:
        while True:
            data = await websocket.receive_bytes() # Получение бинарных данных
            await manager.broadcast(room_id, data) # Передача данных всем участникам комнаты
    
    except Exception as e:
        logger.info(f"Ошибка Websocket: {e}")

    finally:
        del active_conferences[room_id]
        manager.disconnect(websocket, room_id)

# Поддержка соединения и получение данных от сервера
@router.websocket("/ws/play/{room_id}")
async def websocket_play(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)

    try:
        while True:
            await websocket.receive_text() # Ожидаем сообщения, чтобы поддерживать соединение

    except Exception as e:
        logger.info(f"Ошибка Websocket: {e}")
    
    finally:
        manager.disconnect(websocket, room_id)

# WebSocket конечная точка для обмена сообщениями в реальном времени
@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    # Подключение WebSocket клиента
    await manager.connect(websocket, room_id)
    
    try:
        # Цикл для получения сообщений от клиента
        while True:
            data = await websocket.receive_text()

            # Трансляция сообщения всем участникам комнаты
            await manager.broadcast(room_id, f"Комната {room_id}: {data}")

    except Exception as e:
        # Логирование ошибки и отключение WebSocket клиента
        print(f"Ошибка WebSocket: {e}")

    finally:
        manager.disconnect(websocket, room_id)