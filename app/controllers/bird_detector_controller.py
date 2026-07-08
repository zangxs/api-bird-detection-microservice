from fastapi import APIRouter, UploadFile, File, Form
from app.dto.request.bird_request import BirdRequest
from app.services.bird_detector_service import BirdDetectorService

router = APIRouter()
service = BirdDetectorService()

@router.post("/detect-test")
async def detect_bird_test(
    image: UploadFile = File(...),
    user_id: str = Form(...),
    s3_key: str = Form(default="")
):
    image_bytes = await image.read()

    request = BirdRequest(
        image_id="test-id",
        user_id=user_id,
        s3_key=s3_key,
        image_bytes=image_bytes
    )

    return service.detect_bird(request)