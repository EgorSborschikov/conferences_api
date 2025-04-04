from fastapi import FastAPI
from conferences.src.crud.rest_controller import router
from conferences.src.streaming.signal_server import manager
import uvicorn
import asyncio
import websockets

app = FastAPI()

app.include_router(router)

# Структура для хранения активных соединений
connected_clients = {}

# Обработка WebSocket-соединения
# Подключение клиентов к комнате и передача сообщений через ConnectionManager
async def handler(websocket, path):
    room_id = path.split('/')[-1]
    await manager.connect(websocket, room_id)

    try:
        async for message in websocket:
            await manager.broadcast(room_id, message)
    finally:
        manager.disconnect(websocket, room_id)

async def start_websocket_server():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future()  # Бесконечное ожидание для поддержания сервера активным

server_task = None

# События, управляющие запуском и отстановкой WebSocket-сервера
@app.on_event("startup")
async def startup_event():
    global server_task
    server_task = asyncio.create_task(start_websocket_server())

@app.on_event("shutdown")
async def shutdown_event():
    global server_task
    if server_task:
        server_task.cancel()
        await server_task

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)