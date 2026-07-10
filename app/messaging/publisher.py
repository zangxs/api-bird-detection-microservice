import json
import aio_pika
from app.config.config import Config

class Publisher:
    def __init__(self, exchange: aio_pika.Exchange):
        self.exchange = exchange

    async def publish(self, image_event_id: str, is_bird: bool, confidence: float):
        
        payload = {
            "imageEventId": image_event_id,
            "isBird": is_bird,
            "confidence": confidence
        }

        print("publishing result: ", payload)

        await self.exchange.publish(
            aio_pika.Message(body=json.dumps(payload).encode()),
            routing_key=Config.RESULT_ROUTING_KEY
        )