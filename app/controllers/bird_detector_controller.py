from fastapi import APIRouter, UploadFile, File, Form, Depends
from app.dto.request.bird_request import BirdRequest
from app.dto.response.bird_response import BirdResponse
from app.services.bird_detector_service import BirdDetectorService

router = APIRouter()


@router.post("/detector")
async def detect_bird(
    image: UploadFile = File(...),
    user_id: str = Form(...),
    s3_key: str = Form(default=""),
    service: BirdDetectorService = Depends()
) -> BirdResponse:
    image_bytes = await image.read()

    request = BirdRequest(
        image_id="test-id",
        user_id=user_id,
        s3_key=s3_key,
        image_bytes=image_bytes
    )

    return service.detect_bird(request)