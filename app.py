import logging
import threading
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from conferences.src.repository.rest_controller import router
from conferences.src.streaming.signal_server import ConnectionManager
import uvicorn
from technical_support_bot.bot import run_telegram_bot

app = FastAPI()

app.include_router(router)

manager = ConnectionManager()

logger = logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# WebSocket конечная точка для обмена сообщениями в реальном времени
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    # Подключаем клиента к комнате
    await manager.connect(websocket, room_id)

    try:
        while True:
            try:
                # Получаем данные от клиента
                data = await websocket.receive_bytes()
                logger.info(f"Получено {len(data)} байт из комнаты {room_id}")
                # Широковещательная передача данных в комнату
                await manager.broadcast(room_id, data)
                logger.info(f"Передано {len(data)} байт в комнату {room_id}")
            except Exception as e:
                # Логируем ошибку при получении данных
                logger.error(f"Ошибка при получении данных: {e}")
                break

    except WebSocketDisconnect:
        # Логируем отключение клиента
        logger.info(f"Клиент отключился от комнаты {room_id}")
        manager.disconnect(websocket, room_id)

    except Exception as e:
        # Логируем ошибку WebSocket
        logger.error(f"Ошибка WebSocket: {e}")
        manager.disconnect(websocket, room_id)

if __name__ == "__main__":
    # Запуск FastAPI в основном потоке
    fastapi_thread = threading.Thread(target=uvicorn.run, args=(app,), kwargs={"host": "0.0.0.0", "port": 8000, "log_level": "info"})
    fastapi_thread.start()

    # Запуск Telegram-бота в отдельном потоке
    telegram_bot_thread = threading.Thread(target=run_telegram_bot)
    telegram_bot_thread.start()