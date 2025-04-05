from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from conferences.src.crud.rest_controller import router
from conferences.src.streaming.signal_server import ConnectionManager
import uvicorn

app = FastAPI()

app.include_router(router)

manager = ConnectionManager()

# Подключение пользователей к комнате
# WebSocket конечная точка для обмена сообщениями в реальном времени
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)

    try:
        while True:
            # Получение данных от клиента
            data = await websocket.receive_bytes() # Используется метод для получения бинарных данных
            await manager.broadcast(room_id, data) # Широковещательная передача данных в комнату

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)