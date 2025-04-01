from fastapi import APIRouter, FastAPI
import uvicorn

app = FastAPI()
router = APIRouter()

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=1935)