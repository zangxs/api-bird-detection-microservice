import io
from fastai.vision.all import load_learner, PILImage
from app.dto.request.bird_request import BirdRequest
from app.dto.response.bird_response import BirdResponse

CONFIDENCE_THRESHOLD = 0.65
MODEL_PATH = "app/ml/bird_model_latest.pkl"

class BirdDetectorService:

    def __init__(self):
        self.learn = load_learner(MODEL_PATH)
        print(self.learn.dls.vocab)

    def detect_bird(self, request: BirdRequest) -> BirdResponse:
        image = PILImage.create(io.BytesIO(request.image_bytes))

        pred_label, pred_idx, probs = self.learn.predict(image)

        bird_confidence = float(probs[self._bird_index()])
        is_bird = bird_confidence >= CONFIDENCE_THRESHOLD

        response = BirdResponse(
            image_id=request.image_id,
            is_bird=is_bird,
            confidence=round(bird_confidence, 4)
        )

        print("detection response: ", response)

        return response
        

    def _bird_index(self) -> int:
        return self.learn.dls.vocab.o2i["bird"]