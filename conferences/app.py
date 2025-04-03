from fastapi import FastAPI
from conferences.src.crud.rest_controller import router
import uvicorn
import asyncio
import websockets

app = FastAPI()

app.include_router(router)

# Структура для хранения активных соединений
connected_clients = {}

async def handler(websoket, path):
    room_id = path.split('/')[-1]
    if room_id not in connected_clients:
        connected_clients[room_id] = []
    connected_clients[room_id].append(websoket)

    try:
        async for message in websoket:
            # Пересылка сообщения всем участникам комнаты, кроме отправителя
            for client in connected_clients[room_id]:
                if client != websoket:
                    await client.send(message)
    finally:
        connected_clients[room_id].remove(websoket)

async def start_websocket_server():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        await asyncio.Future() # Бесконечное ожидание для поддержания сервера активным

@app.on_event("startup")
async def startup_event():
    # Запуск WebSocket сервера в отдельной задаче
    asyncio.create_task(start_websocket_server())

if __name__ == "__main__":
    uvicorn.run(app, host = "0.0.0.0", port = 8000)