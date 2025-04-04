import asyncio
from collections import defaultdict
from typing import Dict, List
from fastapi import WebSocket

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
        if room_id not in self.tasks:
            self.tasks[room_id] = asyncio.create_task(self.send_messages(room_id))
    
    def disconnect(self, websocket: WebSocket, room_id: str):
        self.active_connections[room_id].remove(websocket)
        if not self.active_connections[room_id]:
            self.tasks[room_id].cancel()
            del self.tasks[room_id]

    # Асинхронный метод доставки сообщения в очередь, а не отправка их непосредственно
    async def broadcast(self, room_id: str, message: str):
        await self.message_queues[room_id].put(message)

    # Асинхронный метод запускается как отдельная задача для каждой комнаты и обрабатывает отправку сообщений с задержкой
    async def send_messages(self, room_id: str):
        while True:
            try:
                message = await self.message_queues[room_id].get()
                for connection in self.active_connections[room_id]:
                    await connection.send_bytes(message)
                await asyncio.sleep(0.5) # Симуляция задержки
            except asyncio.CancelledError:
                break

manager = ConnectionManager()