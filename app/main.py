from fastapi import FastAPI
from app.controllers.bird_detector_controller import router
from contextlib import asynccontextmanager
from app.messaging.consumer import start_consumer
from app.config.config import Config
from app.messaging.publisher import Publisher
import aio_pika


app = FastAPI()
app.include_router(router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    connection = await aio_pika.connect_robust(Config.RABBITMQ_URL)
    channel = await connection.channel()

    result_publisher = Publisher(channel)
    await start_consumer(connection)

    yield
    await connection.close()

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"Hello": "Mundo"}