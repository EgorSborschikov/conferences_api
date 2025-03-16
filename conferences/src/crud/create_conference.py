import uuid

from fastapi import Depends, Request, Response
from app import router
import supabase

# Create Conference
@router.post("/conference")
async def create_conference(
    name: str, 
    user: User = Depends(get_current_user)
):
    room_id = str(uuid.uuid4())
    conference_link = f"rtmp://localhost/live/{room_id}"

    supabase.table("conferences").insert({
            "IDConference" : room_id,
            "ConferenceName": name,
            "ConferenceLink": conference_link,
        }).execute()
    return {"url": conference_link}

# NGinx callbacks
@router.post("/rtmp/publich/")
async def handle_publish(
    request : Request
):
    params = await request.form()
    room_id = params.get("name")

    #exist room checking
    exists = supabase.table("conferences").select("IDConference").uq("IDConference", room_id).execute()

    return Response(status_code=200 if exists.data else 403)