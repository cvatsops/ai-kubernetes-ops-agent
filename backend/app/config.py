
import os
from pathlib import Path

from dotenv import load_dotenv

# Resolve backend/.env relative to this file, not the working directory.
BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(ENV_FILE)


def get_required_env(name: str) -> str:
    """Return a required environment variable or raise a clear error."""
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"Required environment variable '{name}' is not configured."
        )

    return value


def get_optional_env(name: str) -> str | None:
    """Return an optional environment variable."""
    value = os.getenv(name)
    return value if value else None


# Google Cloud / Vertex AI
GOOGLE_GENAI_USE_VERTEXAI = get_required_env(
    "GOOGLE_GENAI_USE_VERTEXAI"
)
GOOGLE_CLOUD_PROJECT = get_required_env("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = get_required_env("GOOGLE_CLOUD_LOCATION")

# Firestore
FIRESTORE_PROJECT_ID = get_required_env("FIRESTORE_PROJECT_ID")
FIRESTORE_DATABASE_ID = get_required_env("FIRESTORE_DATABASE_ID")
FIRESTORE_COLLECTION_NAME = get_required_env(
    "FIRESTORE_COLLECTION_NAME"
)