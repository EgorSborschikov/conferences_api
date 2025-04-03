import hashlib
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, WebSocket
from fastapi.responses import JSONResponse
from conferences.src.models.conference import ConferenceRequest, ConferenceResponse
from conferences.src.streaming.conference_state_management import active_conferences, active_streams, generate_unique_room_id
from conferences.src.streaming.signal_server import manager
from supabase import create_client, Client
import os
from dotenv import load_dotenv

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
        logger.info(f"Конференция {room_id} записана как созданная пользователем")
    
        # Добавление новой конференции в список активных
        active_conferences[hashed_room_id] = new_conference.dict()

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
async def join_conference(room_id: str):
    logger.info(f"attemping to join conference with room_id : {room_id}")

    # Проверка существования конференции
    try:
        if room_id not in active_conferences:
            logger.error(f"Conference not found for room_id: {room_id}")
            raise HTTPException(
                status_code=404,
                detail="Конференция не найдена"
            )

        # Увеличение количества пользователей в конференции
        active_conferences[room_id]["users"] += 1
        logger.info(f"Successfully joined conference with room_id : {room_id}")
        # Возврат статуса успешного присоединения
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
    # Проверка существования конференции
    try:
        if room_id not in active_conferences:
            raise HTTPException(
                status_code=404,
                detail="Конференция не найдена"
            )
        
        # Уменьшение количества пользователей в конференции
        active_conferences[room_id]["users"] -= 1

        # Удаление конференции, если не осталось пользователей
        if active_conferences[room_id]["users"] == 0:
            del active_conferences[room_id]
            # Обновление статуса конференции в Supabase
            response = supabase.table('conferences').update({
                "active" : False
            }).eq("room_id", room_id).execute()
            if response.error:
                raise HTTPException(
                    status_code=500, 
                    detail="Ошибка при обновлении данных в Supabase"
                )

        # Возврат статуса успешного выхода
        return {"status": "Выход успешен"}
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка при выходе из конференции: {str(e)}"
        )

# Получение списка активных конференций
@router.get("/list_conferences")
async def list_conferences(
    supabase: Client = Depends(get_supabase)
    ):
    try:
        # Возврат списка всех активных конференций
        response = supabase.table('conferences').select("*").eq("active", True).execute()
        if response.error:
            raise HTTPException(status_code=500, detail="Ошибка при получении данных из Supabase")
        return response.data
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении списка активных конференций: {str(e)}"
        )

# Публикация потока данных
@router.post("/rtmp/publish")
async def rtmp_publish(data: dict):
    try:
        # Получение ID комнаты из данных
        room_id = data.get("name")

        # Проверка наличия имени комнаты в данных
        if not room_id:
            raise HTTPException(
                status_code=400,
                detail="Не указано имя комнаты"
            )
        
        # Добавление потока в список активных
        active_streams[room_id] = data

        # Возврат статуса начала трансляции
        return JSONResponse(content={"status": "Трансляция начата"})
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка при публикации потока: {str(e)}"
        )

# Воспроизведение потока данных
@router.post("/rtmp/play")
async def rtmp_play(data: dict):
    try:
        # Получение ID комнаты из данных
        room_id = data.get("name")

        # Проверка наличия имени комнаты в данных
        if not room_id:
            raise HTTPException(
                status_code=400,
                detail="Не указано имя комнаты"
            )
        
        # Проверка существования потока
        if room_id in active_streams:
            return JSONResponse(content={"status": "Трансляция воспроизводится"})
        
        # Возврат статуса, если поток не найден
        return JSONResponse(content={"status": "Трансляция не найдена"}, status_code=404)
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка при воспроизведении потока: {str(e)}"
        )

# WebSocket конечная точка для обмена сообщениями в реальном времени
@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    # Подключение WebSocket клиента
    await manager.connect(websocket)
    
    try:
        # Цикл для получения сообщений от клиента
        while True:
            data = await websocket.receive_text()

            # Трансляция сообщения всем участникам комнаты
            await manager.broadcast(f"Комната {room_id}: {data}")
    except Exception as e:
        # Логирование ошибки и отключение WebSocket клиента
        print(f"Ошибка WebSocket: {e}")
        manager.disconnect(websocket)