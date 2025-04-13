import asyncio
from collections import defaultdict
import logging
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger(__name__)

# Управление очередями сообщений для каждой комнаты
# Это позволяет буферизировать сообщения и обрабатывать их асинхронно
# Обработка бинарных потоков и передача их через очередь сообщений
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)
        self.message_queues: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        self.tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        self.active_connections[room_id].append(websocket)
        logger.info(f"Клиент подключился к комнате {room_id}")

        if room_id not in self.tasks:
            self.tasks[room_id] = asyncio.create_task(self.send_messages(room_id))
            logger.info(f"Задача для комнаты {room_id} создана")
    
    def disconnect(self, websocket: WebSocket, room_id: str):
        if websocket in self.active_connections[room_id]:
            self.active_connections[room_id].remove(websocket)
            logger.info(f"Клиент отключен от комнаты {room_id}")

        if not self.active_connections[room_id] and room_id in self.tasks:
            self.tasks[room_id].cancel()
            del self.tasks[room_id]
            logger.info(f"Задача для комнаты {room_id} остановлена")

    # Асинхронный метод доставки сообщения в очередь, а не отправка их непосредственно
    async def broadcast(self, room_id: str, message: bytes):
        # Проверка на количество участников
        if len(self.active_connections[room_id]) > 1:
            await self.message_queues[room_id].put(message)
            logger.debug(f"Сообщение добавлено в очередь комнаты {room_id}")
        else:
            logger.info(f"В комнате {room_id} только один участник. Сообщение не отправлено.")
            
    # Асинхронный метод запускается как отдельная задача для каждой комнаты и обрабатывает отправку сообщений с задержкой
    async def send_messages(self, room_id: str):
        while True:
            try:
                message = await self.message_queues[room_id].get()
                connections = self.active_connections[room_id].copy()

                logger.info(f"Началась трансляция сообщения в комнату {room_id}")
                
                # Вызов _safe_send
                await asyncio.gather(
                    *[self._safe_send(connection, message, room_id) for connection in connections],
                    return_exceptions=True
                )

            except asyncio.CancelledError:
                logger.info(f"Задача для комнаты {room_id} отменена")
                break

            except Exception as e:
                logger.error(f"Ошибка в send_messages: {e}")
    
    async def _safe_send(self, websocket: WebSocket, message: bytes, room_id: str):
        try:
            await websocket.send_bytes(message)
            
        except Exception as e:
            logger.error(f"Ошибка отправки: {e}")
            self.disconnect(websocket, room_id)