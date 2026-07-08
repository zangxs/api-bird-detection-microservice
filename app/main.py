from fastapi import FastAPI
from app.controllers.bird_detector_controller import router

app = FastAPI()
app.include_router(router)

@app.get("/")
def read_root():
    return {"Hello": "Mundo"}