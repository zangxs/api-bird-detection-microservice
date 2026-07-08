from pydantic import BaseModel

class BirdRequest(BaseModel):
    userId: str
    s3Key: str