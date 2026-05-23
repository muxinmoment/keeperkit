from __future__ import annotations

import argparse
import json
from pathlib import Path

import fitz

try:
    import pymupdf4llm
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: pymupdf4llm. Install it with: pip install pymupdf4llm"
    ) from exc


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = BACKEND_DIR / "data" / "raw" / "private" / "pdf_chapters"
DEFAULT_OUTPUT_DIR = BACKEND_DIR / "data" / "raw" / "private" / "markdown_chapters"


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()

    if not input_dir.exists():
        raise SystemExit(f"Input directory not found: {input_dir}")

    pdf_files = sorted(input_dir.glob("*.pdf"))
    if args.limit is not None:
        pdf_files = pdf_files[: args.limit]
    if not pdf_files:
        raise SystemExit(f"No PDF files found in: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    converted = 0
    skipped = 0
    for pdf_path in pdf_files:
        output_path = output_dir / f"{pdf_path.stem}.md"
        if output_path.exists() and not args.overwrite:
            skipped += 1
            print(f"Skip existing: {output_path.name}")
            continue

        markdown = convert_pdf_to_markdown(pdf_path, method=args.method)
        output_path.write_text(
            build_markdown_file(pdf_path, markdown, converter_name(args.method)),
            encoding="utf-8",
        )
        converted += 1
        print(f"Converted: {pdf_path.name} -> {output_path.name}")

    print(f"Done. converted={converted}, skipped={skipped}, output={output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert chapter PDFs to Markdown drafts with pymupdf4llm.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=f"Directory containing chapter PDFs. Default: {DEFAULT_INPUT_DIR}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for Markdown drafts. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing Markdown files.",
    )
    parser.add_argument(
        "--method",
        choices=["auto", "layout", "simple"],
        default="auto",
        help=(
            "Conversion method. 'layout' uses pymupdf4llm layout parser; "
            "'simple' uses PyMuPDF text extraction; 'auto' falls back to simple."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Convert only the first N PDF files. Useful for trial runs.",
    )
    return parser.parse_args()


def convert_pdf_to_markdown(pdf_path: Path, method: str) -> str:
    if method == "simple":
        markdown = convert_pdf_to_simple_markdown(pdf_path)
    else:
        try:
            markdown = pymupdf4llm.to_markdown(str(pdf_path))
        except Exception:
            if method == "layout":
                raise
            print(f"Layout conversion failed, falling back to simple text: {pdf_path.name}")
            markdown = convert_pdf_to_simple_markdown(pdf_path)

    if not markdown.strip():
        raise RuntimeError(f"Empty Markdown output for: {pdf_path}")
    return markdown


def convert_pdf_to_simple_markdown(pdf_path: Path) -> str:
    parts: list[str] = []
    with fitz.open(pdf_path) as document:
        for page_index, page in enumerate(document, start=1):
            text = fix_mojibake(page.get_text("text")).strip()
            if not text:
                continue
            parts.append(f"\n\n<!-- page: {page_index} -->\n\n{text}")
    return "\n".join(parts)


def fix_mojibake(text: str) -> str:
    fixed_lines = [fix_mojibake_segment(line) for line in text.splitlines()]
    fixed = "\n".join(fixed_lines)
    if count_cjk(fixed) > count_cjk(text):
        return fixed
    return text


def fix_mojibake_segment(text: str) -> str:
    try:
        fixed = text.encode("gbk").decode("utf-8")
    except UnicodeError:
        return text
    if count_cjk(fixed) > count_cjk(text):
        return fixed
    return text


def count_cjk(text: str) -> int:
    return sum(1 for char in text if "\u4e00" <= char <= "\u9fff")


def converter_name(method: str) -> str:
    if method == "simple":
        return "pymupdf-simple"
    if method == "layout":
        return "pymupdf4llm-layout"
    return "pymupdf4llm-auto"


def build_markdown_file(pdf_path: Path, markdown: str, converter: str) -> str:
    front_matter = "\n".join(
        [
            "---",
            f"source_pdf: {json.dumps(pdf_path.name, ensure_ascii=False)}",
            f"converter: {converter}",
            "status: draft",
            "---",
            "",
        ]
    )
    return front_matter + markdown.strip() + "\n"


if __name__ == "__main__":
    main()
