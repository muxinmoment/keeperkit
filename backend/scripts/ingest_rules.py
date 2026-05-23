from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR))

from app.config import settings  # noqa: E402
from app.rag.document_loader import load_documents  # noqa: E402
from app.rag.embeddings import create_embedding_model  # noqa: E402
from app.rag.splitter import split_documents  # noqa: E402
from app.rag.vector_store_factory import create_vector_store  # noqa: E402


def main() -> None:
    documents = load_documents(settings.raw_docs_dir)
    chunks = split_documents(documents)
    embedding_model = create_embedding_model(
        provider=settings.embedding_provider,
        model_name=settings.embedding_model,
    )
    vector_store = create_vector_store(
        provider=settings.vector_store_provider,
        index_dir=settings.index_dir,
        embedding_model=embedding_model,
    )
    vector_store.save(chunks)
    print(f"Loaded {len(documents)} documents.")
    print(f"Indexed {len(chunks)} chunks into {settings.index_dir}.")


if __name__ == "__main__":
    main()
