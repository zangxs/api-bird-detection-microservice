# Bird Detection Microservice

A FastAPI microservice for bird detection using a fast.ai vision model. Supports two processing modes:
- **HTTP endpoint**: `POST /detector` — multipart form with image file
- **Async consumer**: RabbitMQ consumer pulling from `bird_detection.pending.queue`, downloads image from S3, publishes result to `bird_detection.result` exchange

## Technologies

- **FastAPI** — Modern, fast web framework for building APIs
- **uvicorn** — ASGI server for running the app
- **fastai** — Deep learning library for model inference
- **PyTorch / torchvision** — ML backend for fastai
- **Pillow** — Image processing
- **Pydantic** — Data validation and serialization
- **python-multipart** — Multipart form data parsing
- **aio-pika** — Async RabbitMQ client
- **boto3** — AWS SDK for S3
- **python-dotenv** — .env file loading

## Prerequisites

### Model File Required

The service requires a trained model file at `app/ml/bird_detector_model.pkl`.

**Download from Kaggle:**
1. Go to: https://www.kaggle.com/code/jhoward/is-it-a-bird-creating-a-model-from-your-own-data
2. Follow the notebook to train/export a model
3. Save the exported model as `bird_detector_model.pkl`
4. Place it in: `app/ml/bird_detector_model.pkl`

The model vocabulary must be: `['bird', 'forest']` (bird class index 0).

### Environment Variables (.env required)

Create a `.env` file in the project root with:

```bash
# RabbitMQ
RABBITMQ_URL=amqp://user:password@localhost:5672/
QUEUE_DETECT_NAME=bird_detection.pending.queue
RESULT_QUEUE_NAME=bird_detection.resultado.queue
EXCHANGE_NAME=bird_detection.exchange
RESULT_ROUTING_KEY=bird_detection.result

# AWS S3
S3_BUCKET=bird-dex-bucket
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

Required variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET` (validated at startup).

## Project Structure

```
app/
├── main.py                           # FastAPI app + lifespan (RabbitMQ connection)
├── config/config.py                  # Config from .env (RabbitMQ, S3, AWS)
├── controllers/bird_detector_controller.py  # POST /detector endpoint (multipart form)
├── services/bird_detector_service.py         # ML inference with fastai
├── messaging/
│   ├── consumer.py                   # RabbitMQ consumer: S3 → detect → publish result
│   └── publisher.py                  # RabbitMQ publisher for results
└── dto/
    ├── request/bird_request.py       # Pydantic: imageId, userId, s3Key, image_bytes
    └── response/bird_response.py     # Pydantic: imageId, isBird, confidence
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

- Health check: `GET /` → `{"Hello": "Mundo"}`
- Detection (HTTP): `POST /detector` multipart: `image` (file), `user_id` (string), `s3_key` (optional string)
- Detection (async): publish to `bird_detection.pending.queue` with `{imageEventId, s3Key, userId}`; result published to `bird_detection.result` routing key

## API Endpoints

### Health Check
```
GET /
```
Response:
```json
{"Hello": "Mundo"}
```

### Bird Detection (HTTP)
```
POST /detector
Content-Type: multipart/form-data
```

**Form Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image` | file | Yes | Image file (JPEG, PNG, etc.) |
| `user_id` | string | No (default: "") | User identifier |
| `s3_key` | string | No (default: "") | Optional S3 key/path |

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

### Bird Detection (Async/RabbitMQ)

Publish to queue `bird_detection.pending.queue`:
```json
{"imageEventId": "evt-123", "s3Key": "birds/photo.jpg", "userId": "user-456"}
```

Consumer downloads from S3, runs detection, publishes result to exchange `bird_detection.exchange` with routing key `bird_detection.result`:
```json
{"imageEventId": "evt-123", "isBird": true, "confidence": 0.9421}
```

## Configuration

**Confidence Threshold:** Hardcoded at `0.80` in `app/services/bird_detector_service.py`

**Model Path:** `app/ml/bird_detector_model.pkl` (loaded at service startup)

**Environment Variables:** See [Prerequisites](#environment-variables-env-required) — validated in `app/config/config.py`

## Common Tasks

| Task | Command |
|------|---------|
| Install deps | `pip install -r requirements.txt` |
| Run dev server | `uvicorn app.main:app --reload` |
| Run prod | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |

## Notes

- **Startup time:** ~5 seconds (model loads on service instantiation) — happens twice (HTTP Depends + consumer)
- **Model format:** fastai `Learner` exported via `learn.export()`
- **Security:** `load_learner` uses pickle — only load trusted model files
- **No error handling, validation, or logging** configured
- **No CI/CD, Dockerfile, or deployment config**
- `.env` contains real AWS credentials — **do not commit**
- Consumer creates its own `BirdDetectorService` instance (separate from HTTP DI)
- S3 client created at module load time — requires valid AWS creds at import