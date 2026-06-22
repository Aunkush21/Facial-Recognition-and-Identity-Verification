# SENTRY — Facial Recognition & Attendance System

A production-style facial recognition and attendance platform with **liveness (anti-spoofing) detection**, **multi-frame consensus**, role-based access, a self-service **kiosk mode**, and a complete **audit trail**.

Faces are detected and embedded with InsightFace (ArcFace/RetinaFace), checked for liveness with a MiniFASNet anti-spoofing model, and matched against embeddings stored in PostgreSQL via `pgvector`. The whole thing is served by FastAPI with a server-rendered UI — no biometric images are ever written to disk.

> 🎓 **Academic project** — built as a final-year college project submission.

---

## Features

- **Live recognition** — browser webcam streams frames to the backend; each frame is liveness-checked, matched by cosine similarity, and must clear **N agreeing frames (consensus)** before attendance is recorded.
- **Anti-spoofing** — a dedicated MiniFASNet liveness gate rejects photos and screen replays *before* matching.
- **Enrollment** — register a face from the **live camera or an uploaded photo**; the same liveness gate applies, and exactly one face per image is required.
- **Kiosk mode** — a fullscreen, unattended self check-in screen for a wall-mounted tablet: continuous recognition with a friendly "Welcome, <name>" confirmation.
- **Attendance** — daily present/absent register per identity, with one-click **Excel (.xlsx) export**.
- **Operator accounts** — admins create separate logins per operator (e.g. one per subject teacher), each labelled, with activate/deactivate and password reset.
- **Audit log** — every login, enrollment, recognition, and attendance write is recorded with the acting user, result, and confidence.
- **Auth & roles** — JWT in an httpOnly, `SameSite=Strict` cookie; bcrypt-hashed passwords; `admin` and `operator` roles enforced on every route.

## Tech stack

| Layer | Technology |
|---|---|
| API / web | FastAPI, Jinja2 templates, vanilla JS (no build step) |
| Face engine | InsightFace `buffalo_l` (RetinaFace detection + ArcFace 512-d embeddings), ONNX Runtime |
| Liveness | MiniFASNet-V2 (Silent-Face anti-spoofing), ONNX |
| Database | PostgreSQL + `pgvector` (`Vector(512)`), SQLAlchemy, Alembic |
| Auth | python-jose (JWT), passlib + bcrypt |
| Tests / lint | pytest, ruff |

## How recognition works

```
webcam frame ─► detect face ─► LIVENESS gate ─► embed (ArcFace) ─► cosine match
                                   │ fail                                │ below threshold
                                   ▼                                     ▼
                            reject (spoof)                         reject (unknown)
                                                                         │ match
                                                                         ▼
                                                     consensus: N agreeing frames in a window
                                                                         │ confirmed
                                                                         ▼
                                              atomic attendance upsert  +  audit log entry
```

## Project structure

```
app/
  main.py            # FastAPI app, router wiring, model preload on startup
  core/              # settings, database engine/session
  models/            # SQLAlchemy models (identity, embedding, attendance, audit_log, user)
  schemas/           # Pydantic request/response models
  services/          # face_engine, liveness, recognition, consensus, auth, identity, attendance, audit, user
  api/routes/        # JSON API: auth, identities, enrollment, recognition, attendance, audit, users
  web/               # server-rendered page routes
  templates/         # Jinja2 templates (login, recognize, enroll, dashboard, audit, operators, kiosk)
  static/            # CSS + vanilla JS
  models_data/       # downloaded ONNX weights (gitignored)
alembic/             # database migrations
scripts/             # download_models.py, create_admin.py
tests/               # pytest suite
```

## Getting started

### Prerequisites

- **Python 3.13**
- **PostgreSQL** with the **`pgvector`** extension available
- ~600 MB disk for the ONNX model weights (downloaded, not committed)

### Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create the database** (and a dedicated role) with the required extensions:
   ```sql
   CREATE ROLE facial_app LOGIN PASSWORD '<choose-a-password>';
   CREATE DATABASE facial_recognition OWNER facial_app;
   -- as a superuser, in that database:
   CREATE EXTENSION IF NOT EXISTS vector;
   CREATE EXTENSION IF NOT EXISTS pgcrypto;
   ```

3. **Configure environment** — copy `.env.example` to `.env` and fill in real values:
   ```bash
   cp .env.example .env
   ```

4. **Download the models** (InsightFace pack + liveness model):
   ```bash
   python scripts/download_models.py
   ```

5. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Create the first admin user**:
   ```bash
   python scripts/create_admin.py <username>
   ```

7. **Run the app**:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
   Open <http://127.0.0.1:8000> and sign in.

## Configuration

All settings are read from `.env` (see `.env.example`):

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy Postgres URL | — |
| `JWT_SECRET_KEY` | secret for signing access tokens | — |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | session lifetime | `60` |
| `FACE_MODEL_PACK` | InsightFace pack | `buffalo_l` |
| `RECOGNITION_THRESHOLD` | min cosine similarity to match | `0.45` |
| `LIVENESS_THRESHOLD` | min liveness score to accept | `0.65` |
| `CONSENSUS_FRAMES_REQUIRED` | agreeing frames before recording | `5` |
| `CONSENSUS_WINDOW_SECONDS` | window those frames must fall within | `10` |

## Roles

- **Admin** — full access: manage identities, enroll, run recognition, view attendance, **manage operator accounts**, and view the **audit log**.
- **Operator** — run recognition, enroll faces, and view attendance. Cannot manage accounts or view the audit log.

Operator accounts are created by an admin from the **Operators** page (no public sign-up by design).

## Testing

```bash
# point the suite at a test database (with pgvector + pgcrypto), then:
TEST_DATABASE_URL=postgresql+psycopg2://facial_app:<pw>@localhost:5432/facial_recognition_test pytest -q
```

Pure-unit tests (auth, consensus, validation) run without a database; DB-dependent tests skip gracefully when no `TEST_DATABASE_URL` is reachable. CI runs the full suite against a `pgvector` service container.

## Security notes

- Biometric data is stored **only as numeric embeddings in the database** — no face images are written to disk.
- Liveness checking runs **before** any match, mitigating photo/screen spoofing.
- Attendance is only written after **multi-frame consensus**, not a single lucky frame.
- Passwords are **bcrypt-hashed** (one-way); a forgotten password can be reset by an admin but never recovered.
- All secrets live in `.env`, which is gitignored.

## About

This project was developed as a **final-year college project submission**.
