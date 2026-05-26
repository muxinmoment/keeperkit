import sys
from pathlib import Path
import os


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("KEEPERKIT_DISABLE_DOTENV", "1")
os.environ.setdefault("EMBEDDING_PROVIDER", "hash")
os.environ.setdefault("VECTOR_STORE_PROVIDER", "json")
os.environ.setdefault("GENERATOR_PROVIDER", "template")
os.environ.setdefault("RERANKER_PROVIDER", "simple")
