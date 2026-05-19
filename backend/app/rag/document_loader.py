from pathlib import Path

from app.rag.types import RawDocument


SUPPORTED_SUFFIXES = {".md", ".markdown", ".txt"}


def load_documents(raw_docs_dir: Path) -> list[RawDocument]:
    if not raw_docs_dir.exists():
        raise FileNotFoundError(f"Raw docs directory does not exist: {raw_docs_dir}")

    documents: list[RawDocument] = []
    for path in sorted(raw_docs_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        documents.append(
            RawDocument(
                content=path.read_text(encoding="utf-8"),
                metadata={
                    "source": str(path.relative_to(raw_docs_dir)),
                    "suffix": path.suffix.lower(),
                },
            )
        )

    if not documents:
        raise FileNotFoundError(
            f"No Markdown or TXT documents found in {raw_docs_dir}. "
            "Put rule notes in backend/data/raw first."
        )

    return documents
