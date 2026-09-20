import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SAMPLES_DIR = DATA_DIR / "samples"
AUDIT_FILE = DATA_DIR / "audit.json"

# Gemini and LLM Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip() or None
_mock_env = os.getenv("USE_MOCK_LLM", "").strip().lower()
# Mock is active if explicitly requested or if no API key is provided
USE_MOCK_LLM = _mock_env in ("true", "1", "yes") or (GEMINI_API_KEY is None)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
PROMPT_VERSION = "v1"

# Target screening thresholds
DEFAULT_MAX_INTERVIEW_TURNS = 5
DEFAULT_COVERAGE_TARGET = 1.0  # 100% of must-haves
