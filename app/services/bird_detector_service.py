from app.dto.request.bird_request import BirdRequest
from app.dto.response.bird_response import BirdResponse
class BirdDetectorService:


    def detect_bird(self, request: BirdRequest) -> BirdResponse:
        #hace algo

        print("detect_bird service")
        response = BirdResponse()
        
        return response