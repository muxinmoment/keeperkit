from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

try:
    import fitz
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: PyMuPDF. Install it with: pip install pymupdf"
    ) from exc


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parents[0]
DEFAULT_PDF = (
    PROJECT_DIR
    / "docs"
    / "coc第七版跑团规则书"
    / "COC7th核心规则书v1.2.1.pdf"
)
DEFAULT_OUTPUT_DIR = BACKEND_DIR / "data" / "raw" / "private" / "pdf_chapters"


@dataclass(frozen=True)
class ChapterRange:
    index: int
    level: int
    title: str
    start_page: int
    end_page: int

    @property
    def filename(self) -> str:
        return f"{self.index:02d}-{slugify(self.title)}.pdf"


def main() -> None:
    args = parse_args()
    pdf_path = args.pdf.resolve()
    output_dir = args.output_dir.resolve()

    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    with fitz.open(pdf_path) as source:
        chapters = build_chapter_ranges(
            source,
            max_level=args.max_level,
            min_pages=args.min_pages,
        )

        if args.list_only:
            print_ranges(chapters)
            return

        output_dir.mkdir(parents=True, exist_ok=True)
        for chapter in chapters:
            write_chapter_pdf(source, chapter, output_dir / chapter.filename)

    print(f"Split {len(chapters)} chapter PDFs into: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split a PDF into chapter PDFs using its built-in bookmarks.",
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        default=DEFAULT_PDF,
        help=f"Source PDF path. Default: {DEFAULT_PDF}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--max-level",
        type=int,
        default=1,
        help="Use bookmarks up to this outline level. Level 1 means top-level chapters.",
    )
    parser.add_argument(
        "--min-pages",
        type=int,
        default=2,
        help="Skip bookmark ranges shorter than this many PDF pages.",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Only print detected ranges; do not write PDFs.",
    )
    return parser.parse_args()


def build_chapter_ranges(
    document: fitz.Document,
    max_level: int,
    min_pages: int,
) -> list[ChapterRange]:
    toc = document.get_toc(simple=True)
    if not toc:
        raise SystemExit("This PDF has no bookmarks / outline entries.")

    entries = [
        (level, title.strip(), page)
        for level, title, page in toc
        if level <= max_level and title.strip()
    ]
    if not entries:
        raise SystemExit(f"No bookmarks found at outline level <= {max_level}.")

    ranges: list[ChapterRange] = []
    for i, (level, title, start_page) in enumerate(entries):
        next_start = entries[i + 1][2] if i + 1 < len(entries) else document.page_count + 1
        end_page = max(start_page, next_start - 1)
        if end_page - start_page + 1 < min_pages:
            continue
        ranges.append(
            ChapterRange(
                index=len(ranges) + 1,
                level=level,
                title=title,
                start_page=start_page,
                end_page=end_page,
            )
        )

    if not ranges:
        raise SystemExit(
            "No chapter ranges survived filtering. Try lowering --min-pages."
        )
    return ranges


def write_chapter_pdf(
    source: fitz.Document,
    chapter: ChapterRange,
    output_path: Path,
) -> None:
    target = fitz.open()
    target.insert_pdf(
        source,
        from_page=chapter.start_page - 1,
        to_page=chapter.end_page - 1,
    )
    target.save(output_path, garbage=4, deflate=True)
    target.close()
    print(f"Wrote {output_path.name}: pages {chapter.start_page}-{chapter.end_page}")


def print_ranges(chapters: list[ChapterRange]) -> None:
    for chapter in chapters:
        page_count = chapter.end_page - chapter.start_page + 1
        print(
            f"{chapter.index:02d}. "
            f"level={chapter.level} "
            f"pages={chapter.start_page}-{chapter.end_page} "
            f"count={page_count} "
            f"title={chapter.title}"
        )


def slugify(title: str) -> str:
    slug = re.sub(r"[\\/:*?\"<>|]+", "-", title.strip())
    slug = re.sub(r"\s+", "-", slug)
    slug = slug.strip(".- ")
    return slug[:80] or "untitled"


if __name__ == "__main__":
    main()
