"""One-time setup: downloads the InsightFace detection/embedding model pack and
the MiniFASNet-V2 liveness model. Run manually (`python scripts/download_models.py`)
or as a Docker build step — these binaries are gitignored, never committed.

Liveness source: garciafido/minifasnet-v2-anti-spoofing-onnx on Hugging Face Hub
(an ONNX export of minivision-ai's official Silent-Face-Anti-Spoofing MiniFASNet-V2
2.7_80x80 weights). Verify the source yourself before trusting it in production —
this script pins the exact filename/repo, but does not silently swap sources.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from huggingface_hub import hf_hub_download  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.services.face_engine import MODELS_ROOT  # noqa: E402
from app.services.liveness import MODEL_PATH as LIVENESS_MODEL_PATH  # noqa: E402

LIVENESS_REPO = "garciafido/minifasnet-v2-anti-spoofing-onnx"
LIVENESS_FILENAME = "minifasnet_v2.onnx"


def download_insightface_pack() -> None:
    from insightface.app import FaceAnalysis

    print(f"Downloading InsightFace pack '{settings.face_model_pack}' to {MODELS_ROOT} ...")
    MODELS_ROOT.mkdir(parents=True, exist_ok=True)
    app = FaceAnalysis(name=settings.face_model_pack, root=str(MODELS_ROOT), providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=-1, det_size=(640, 640))
    print("InsightFace pack ready.")


def download_liveness_model() -> None:
    if LIVENESS_MODEL_PATH.exists():
        print(f"Liveness model already present at {LIVENESS_MODEL_PATH}, skipping download.")
        return

    print(f"Downloading liveness model from huggingface.co/{LIVENESS_REPO} ...")
    LIVENESS_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    downloaded_path = hf_hub_download(repo_id=LIVENESS_REPO, filename=LIVENESS_FILENAME)
    LIVENESS_MODEL_PATH.write_bytes(Path(downloaded_path).read_bytes())
    print(f"Liveness model ready at {LIVENESS_MODEL_PATH}.")


if __name__ == "__main__":
    download_insightface_pack()
    download_liveness_model()
