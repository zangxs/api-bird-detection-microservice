from pydantic import BaseModel

class BirdResponse(BaseModel):
    isBird: bool
