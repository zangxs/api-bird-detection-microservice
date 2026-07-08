from fastapi import APIRouter
from app.services.bird_detector_service import BirdDetectorService
from app.dto.request.bird_request import BirdRequest
from app.dto.response.bird_response import BirdResponse

router = APIRouter()


@router.post("/detector")
def detect_bird(request: BirdRequest, service: BirdDetectorService) -> BirdResponse:
    print("entro al controller")
    return service.detect_bird()