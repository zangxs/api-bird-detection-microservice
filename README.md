# Bird Detection Microservice

A FastAPI microservice for bird detection using a fast.ai vision model.

## Technologies

- **FastAPI** — Modern, fast web framework for building APIs
- **uvicorn** — ASGI server for running the app
- **fastai** — Deep learning library for model inference
- **PyTorch / torchvision** — ML backend for fastai
- **Pillow** — Image processing
- **Pydantic** — Data validation and serialization
- **python-multipart** — Multipart form data parsing

## Prerequisites

### Model File Required

The service requires a trained model file at `app/ml/bird_detector_model.pkl`.

**Download from Kaggle:**
1. Go to: https://www.kaggle.com/code/jhoward/is-it-a-bird-creating-a-model-from-your-own-data
2. Follow the notebook to train/export a model
3. Save the exported model as `bird_detector_model.pkl`
4. Place it in: `app/ml/bird_detector_model.pkl`

The model vocabulary must be: `['bird', 'forest']` (bird class index 0).

## Project Structure

```
app/
├── main.py                              # FastAPI entry point
├── controllers/bird_detector_controller.py  # POST /detector endpoint
├── services/bird_detector_service.py        # ML inference with fastai
├── dto/
│   ├── request/bird_request.py          # Pydantic: imageId, userId, s3Key, image_bytes
│   └── response/bird_response.py        # Pydantic: imageId, isBird, confidence
└── ml/
    └── bird_detector_model.pkl          # fastai learner (REQUIRED - not in repo)
```

## Installation

```bash
# Create virtual environment (if not exists)
python -m venv env

# Activate
source env/bin/activate  # Linux/macOS
# env\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

## Running the Service

```bash
# Development (auto-reload)
source env/bin/activate
uvicorn app.main:app --reload --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check
```
GET /
```
Response:
```json
{"Hello": "Mundo"}
```

### Bird Detection
```
POST /detector
```

**Content-Type:** `multipart/form-data`

**Form Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image` | file | Yes | Image file (JPEG, PNG, etc.) |
| `user_id` | string | Yes | User identifier |
| `s3_key` | string | No | Optional S3 key/path |

**Example Request:**
```bash
curl -X POST http://localhost:8000/detector \
  -F "image=@/path/to/bird.jpg" \
  -F "user_id=user123" \
  -F "s3_key=birds/bird.jpg"
```

**Example Response:**
```json
{
  "imageId": "test-id",
  "isBird": true,
  "confidence": 0.9421
}
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `imageId` | string | Identifier for the processed image |
| `isBird` | boolean | `true` if bird detected (confidence ≥ 0.80) |
| `confidence` | float | Model confidence score (0.0–1.0) |

## Configuration

**Confidence Threshold:** Hardcoded at `0.80` in `app/services/bird_detector_service.py`

**Model Path:** `app/ml/bird_detector_model.pkl` (loaded at service startup)

## Notes

- **Startup time:** ~5 seconds (model loads on first request / service instantiation)
- **Model format:** fastai `Learner` exported via `learn.export()`
- **Security:** `load_learner` uses Python pickle — only load trusted model files
- **No tests / linting / CI** configured yet