from pydantic import BaseModel, Field, ConfigDict

class BirdResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    image_id: str = Field(alias="imageId")
    is_bird: bool = Field(alias="isBird")
    confidence: float
