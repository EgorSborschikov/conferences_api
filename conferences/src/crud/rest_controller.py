# ReST API for create, search and join conferences

from fastapi import FastAPI, APIRouter, HTTPException, WebSocket
from fastapi.responses import JSONResponse
from conferences.src.streaming.conference_state_management import active_conferences, active_streams, generate_unique_room_id
from conferences.src.streaming.signal_server import manager

router = APIRouter()

@router.post("/create_conference")
async def create_conference(name: str):
    if len(active_conferences) >= 2:
        raise HTTPException(
            status_code=400,
            detail="Limit of active conferences reached"
        )
    room_id = generate_unique_room_id()
    link = f"http://localhost/join/{room_id}"
    active_conferences[room_id] = {"name": name, "users": 0}
    return {"room_id": room_id, "link": link}

@router.get("/join_conference/{room_id}")
async def join_conference(room_id: str):
    if room_id not in active_conferences:
        raise HTTPException(
            status_code=404,
            detail="Conference not found"
        )
    active_conferences[room_id]["users"] += 1
    return {"status": "Joined successfully"}

@router.post("/leave_conference/{room_id}")
async def leave_conference(room_id: str):
    if room_id not in active_conferences:
        raise HTTPException(
            status_code=404,
            detail="Conference not found"
        )
    active_conferences[room_id]["users"] -= 1
    if active_conferences[room_id]["users"] == 0:
        del active_conferences[room_id]
    return {"status": "Left successfully"}

@router.get("/list_conferences")
async def list_conferences():
    return list(active_conferences.values())

@router.post("/rtmp/publish")
async def rtmp_publish(data: dict):
    room_id = data.get("name")
    active_streams[room_id] = data
    return JSONResponse(content={"status": "Stream started"})

@router.post("/rtmp/play")
async def rtmp_play(data: dict):
    room_id = data.get("name")
    if room_id in active_streams:
        return JSONResponse(content={"status": "Stream playing"})
    return JSONResponse(content={"status": "Stream not found"}, status_code=404)

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Room {room_id}: {data}")
    except:
        manager.disconnect(websocket)
