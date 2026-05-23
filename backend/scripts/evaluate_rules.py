import argparse
import json
from pathlib import Path
import sys
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR))

from app.config import settings  # noqa: E402
from app.rag.reranker import Reranker, create_reranker  # noqa: E402
from app.rag.retriever import RuleRetriever  # noqa: E402
from app.rag.types import RetrievedChunk  # noqa: E402


DEFAULT_QUESTIONS_FILE = BACKEND_DIR / "data" / "eval" / "rules_eval_questions.json"


def main() -> None:
    args = parse_args()
    cases = load_cases(args.questions_file)
    retriever = RuleRetriever(index_dir=settings.index_dir)
    reranker = create_reranker(
        provider=settings.reranker_provider,
        model_name=settings.reranker_model,
    )

    results = [
        evaluate_case(
            case=case,
            retriever=retriever,
            reranker=reranker,
            top_k=args.top_k,
            rerank_top_k=args.rerank_top_k,
        )
        for case in cases
    ]

    print_report(results)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(
                {
                    "index_dir": str(settings.index_dir),
                    "embedding_provider": settings.embedding_provider,
                    "embedding_model": settings.embedding_model,
                    "vector_store_provider": settings.vector_store_provider,
                    "chroma_collection": settings.chroma_collection,
                    "reranker_provider": settings.reranker_provider,
                    "reranker_model": settings.reranker_model,
                    "top_k": args.top_k,
                    "rerank_top_k": args.rerank_top_k,
                    "results": results,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"\nReport written to {args.output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a fixed KeeperKit rules retrieval evaluation set.",
    )
    parser.add_argument(
        "--questions-file",
        type=Path,
        default=DEFAULT_QUESTIONS_FILE,
        help=f"Evaluation question set JSON. Default: {DEFAULT_QUESTIONS_FILE}",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=settings.retrieval_top_k,
        help=f"Retriever candidate count. Default: {settings.retrieval_top_k}",
    )
    parser.add_argument(
        "--rerank-top-k",
        type=int,
        default=settings.rerank_top_k,
        help=f"Final reranked source count. Default: {settings.rerank_top_k}",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON report path.",
    )
    return parser.parse_args()


def load_cases(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Evaluation question file does not exist: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Evaluation question file must contain a JSON array.")

    cases: list[dict[str, Any]] = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Evaluation case #{index} must be an object.")
        for field in ("id", "question", "expected_terms"):
            if field not in item:
                raise ValueError(f"Evaluation case #{index} is missing field: {field}")
        if not isinstance(item["expected_terms"], list) or not item["expected_terms"]:
            raise ValueError(f"Evaluation case #{index} expected_terms must be a non-empty array.")
        cases.append(item)
    return cases


def evaluate_case(
    case: dict[str, Any],
    retriever: RuleRetriever,
    reranker: Reranker,
    top_k: int,
    rerank_top_k: int,
) -> dict[str, Any]:
    question = str(case["question"])
    expected_terms = [str(term) for term in case["expected_terms"]]
    candidates = retriever.retrieve(question, top_k=top_k)
    selected = reranker.rerank(question, candidates, top_k=rerank_top_k)

    selected_hit = first_matching_chunk(selected, expected_terms)
    candidate_hit = first_matching_chunk(candidates, expected_terms)
    status = "PASS" if selected_hit else "CANDIDATE_ONLY" if candidate_hit else "MISS"
    top_selected = selected[0] if selected else None

    return {
        "id": case["id"],
        "question": question,
        "expected_terms": expected_terms,
        "status": status,
        "top_score": round(top_selected.score, 4) if top_selected else None,
        "top_source": source_of(top_selected) if top_selected else None,
        "top_title": title_of(top_selected) if top_selected else None,
        "matched_source": source_of(selected_hit or candidate_hit),
        "matched_title": title_of(selected_hit or candidate_hit),
        "notes": case.get("notes", ""),
    }


def first_matching_chunk(chunks: list[RetrievedChunk], expected_terms: list[str]) -> RetrievedChunk | None:
    for item in chunks:
        haystack = searchable_text(item)
        if all(term.lower() in haystack for term in expected_terms):
            return item
    return None


def searchable_text(item: RetrievedChunk) -> str:
    title_path = item.chunk.metadata.get("title_path", [])
    if isinstance(title_path, list):
        title = " / ".join(str(part) for part in title_path)
    else:
        title = str(title_path)
    source = str(item.chunk.metadata.get("source", ""))
    return f"{source}\n{title}\n{item.chunk.content}".lower()


def source_of(item: RetrievedChunk | None) -> str | None:
    if item is None:
        return None
    return str(item.chunk.metadata.get("source", "unknown"))


def title_of(item: RetrievedChunk | None) -> str | None:
    if item is None:
        return None
    title_path = item.chunk.metadata.get("title_path", [])
    if isinstance(title_path, list):
        return " / ".join(str(part) for part in title_path)
    return str(title_path)


def print_report(results: list[dict[str, Any]]) -> None:
    total = len(results)
    passed = sum(1 for result in results if result["status"] == "PASS")
    candidate_only = sum(1 for result in results if result["status"] == "CANDIDATE_ONLY")
    missed = sum(1 for result in results if result["status"] == "MISS")

    print("KeeperKit fixed rules evaluation")
    print(f"Total: {total}  PASS: {passed}  CANDIDATE_ONLY: {candidate_only}  MISS: {missed}")
    print()
    for result in results:
        print(f"[{result['status']}] {result['id']}: {result['question']}")
        print(f"  top: {result['top_source']} | {result['top_title']} | score={result['top_score']}")
        if result["status"] != "PASS":
            print(f"  matched: {result['matched_source']} | {result['matched_title']}")


if __name__ == "__main__":
    main()
