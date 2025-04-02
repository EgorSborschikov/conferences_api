from fastapi import FastAPI
from conferences.src.crud.rest_controller import router
import uvicorn

app = FastAPI()

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.0.191", port=1935)