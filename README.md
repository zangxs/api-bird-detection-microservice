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
- **pillow-heif** — HEIC/HEIF decoding, registered via `register_heif_opener()` in `app/main.py` so `PILImage.create` can open iPhone-format photos

## Prerequisites

### Model File Required

The service requires a trained model file at `app/ml/bird_model_latest.pkl`.

**Download from Hugging Face** (public, no token needed):

```bash
mkdir -p app/ml
curl -L -o app/ml/bird_model_latest.pkl \
  https://huggingface.co/brayanspv/bird_detection_brayanpv/resolve/main/bird_model_latest.pkl

# verify you got the exact file that was uploaded, not something swapped in later at that URL
echo "6603ab02a38a4d5ad56b02ab472a9c51a8ac5744da13fde513ee47eb694ce86b  app/ml/bird_model_latest.pkl" | sha256sum -c
```

Repo: <https://huggingface.co/brayanspv/bird_detection_brayanpv>. The Hub's scanner flags the file
`Unsafe` (`PAIT-PYTCH-100`/`101`) because `fastai`'s `Learner.export()` pickles the whole `Learner` —
that's a near-universal false positive for fastai exports, not evidence of tampering.

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

# Install dependencies — requirements-ml.txt first (fastai/torch/torchvision, pinned to match
# the training venv), then this service's own deps
pip install -r requirements-ml.txt
pip install -r requirements.txt
```

`requirements-ml.txt` is byte-identical to `../api-bird-classification-microservice/requirements-ml.txt`
(`fastai==2.8.7`, `torch==2.13.0`, `torchvision==0.28.0` — pinned to match the venv the models were
trained in, plus `aio-pika`/`boto3`/`python-dotenv`, shared by both services). In Docker this split
lets the two images share the ~8.9GB `torch`/`fastai` layer instead of each paying for it separately
— see `../api-bird-orchestator-microservice/DOCKER.md` for the image-size breakdown.

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
| `isBird` | boolean | `true` if bird detected (confidence ≥ 0.65) |
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

**Confidence Threshold:** Hardcoded at `0.65` in `app/services/bird_detector_service.py`

**Model Path:** `app/ml/bird_model_latest.pkl` (loaded at service startup)

**Environment Variables:** See [Prerequisites](#environment-variables-env-required) — validated in `app/config/config.py`

## Running with Docker

```bash
docker build -t bird-detection-microservice .
docker run -p 8000:8000 \
  --env-file .env \
  -v "$(pwd)/app/ml:/app/app/ml" \
  bird-detection-microservice
```

The image does **not** bundle the model file (`app/ml/*.pkl` is gitignored and excluded via
`.dockerignore`) — mount it as a volume as shown above. The container fails fast on startup if it's
missing, which is the point: no silent fallback to an unloaded model.

Expect the built image to be **~9GB** — `pip install torch` pulls the default CUDA build (bundled
`nvidia-*` wheels) even though inference here runs on CPU only; that's dead weight, not something
this service's code uses. See the "Install dependencies" note above and
`../api-bird-orchestator-microservice/DOCKER.md` for why it's split into `requirements-ml.txt` and
how that lets this image share that layer with `api-bird-classification-microservice` on disk.

To run this service together with the orchestrator, classification, Postgres, and RabbitMQ via a
single `docker compose up`, see `../api-bird-orchestator-microservice/DOCKER.md` — its
`docker-compose.yml` builds this image from `../api-bird-detection-microservice`, so this repo needs
to be checked out as a sibling of the orchestrator repo.

## Common Tasks

| Task | Command |
|------|---------|
| Install deps | `pip install -r requirements-ml.txt -r requirements.txt` |
| Run dev server | `uvicorn app.main:app --reload` |
| Run prod | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |

## Notes

- **Startup time:** ~5 seconds (model loads on service instantiation) — happens twice (HTTP Depends + consumer)
- **Model format:** fastai `Learner` exported via `learn.export()`
- **Security:** `load_learner` uses pickle — only load trusted model files
- **No error handling, validation, or logging** configured
- **No CI/CD** — `Dockerfile`/`.dockerignore` exist, but nothing builds/pushes the image automatically
- `.env` contains real AWS credentials — **do not commit**
- Consumer creates its own `BirdDetectorService` instance (separate from HTTP DI)
- S3 client created at module load time — requires valid AWS creds at import