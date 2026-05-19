from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR))

from app.config import settings  # noqa: E402
from app.rag.retriever import RuleRetriever  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/test_retrieval.py \"your question\"")

    question = sys.argv[1]
    retriever = RuleRetriever(index_dir=settings.index_dir)
    results = retriever.retrieve(question, top_k=settings.retrieval_top_k)
    for index, result in enumerate(results, start=1):
        title_path = result.chunk.metadata.get("title_path", [])
        title = " / ".join(title_path) if isinstance(title_path, list) else title_path
        print(f"\n[{index}] score={result.score:.4f} source={result.chunk.metadata.get('source')}")
        print(f"title={title}")
        print(result.chunk.content[:360].replace("\n", " "))


if __name__ == "__main__":
    main()
