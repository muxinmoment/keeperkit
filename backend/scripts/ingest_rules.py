from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR))

from app.config import settings  # noqa: E402
from app.rag.document_loader import load_documents  # noqa: E402
from app.rag.splitter import split_documents  # noqa: E402
from app.rag.vector_store import JsonVectorStore  # noqa: E402


def main() -> None:
    documents = load_documents(settings.raw_docs_dir)
    chunks = split_documents(documents)
    vector_store = JsonVectorStore(index_dir=settings.index_dir)
    vector_store.save(chunks)
    print(f"Loaded {len(documents)} documents.")
    print(f"Indexed {len(chunks)} chunks into {settings.index_dir}.")


if __name__ == "__main__":
    main()
