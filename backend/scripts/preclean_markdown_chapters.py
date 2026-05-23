from __future__ import annotations

import argparse
import re
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = BACKEND_DIR / "data" / "raw" / "private" / "markdown_chapters"
DEFAULT_OUTPUT_DIR = BACKEND_DIR / "data" / "raw" / "private" / "preclean_markdown_chapters"

PAGE_MARK_RE = re.compile(r"^<!--\s*page:\s*\d+\s*-->$")
PAGE_NUMBER_RE = re.compile(r"^\d{1,4}$")
CHAPTER_TITLE_RE = re.compile(r"^第[一二三四五六七八九十百零〇\d]+章\s+\S+")
NUMBERED_HEADING_RE = re.compile(r"^\d+(?:\.\d+)+\s+\S.{0,60}$")
HEADER_NOISE = {
    "Call of Cthulhu 7th Edition",
}


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()

    if not input_dir.exists():
        raise SystemExit(f"Input directory not found: {input_dir}")

    markdown_files = sorted(input_dir.glob("*.md"))
    if args.limit is not None:
        markdown_files = markdown_files[: args.limit]
    if not markdown_files:
        raise SystemExit(f"No Markdown files found in: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    converted = 0
    skipped = 0
    for source_path in markdown_files:
        output_path = output_dir / source_path.name
        if output_path.exists() and not args.overwrite:
            skipped += 1
            print(f"Skip existing: {output_path.name}")
            continue

        original = source_path.read_text(encoding="utf-8")
        cleaned = preclean_markdown(original, merge_lines=args.merge_lines)
        output_path.write_text(cleaned, encoding="utf-8")
        converted += 1
        print(f"Precleaned: {source_path.name} -> {output_path.name}")

    print(f"Done. converted={converted}, skipped={skipped}, output={output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Conservatively pre-clean Markdown drafts extracted from chapter PDFs.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=f"Directory containing Markdown drafts. Default: {DEFAULT_INPUT_DIR}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for pre-cleaned Markdown. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing pre-cleaned Markdown files.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N Markdown files. Useful for trial runs.",
    )
    parser.add_argument(
        "--merge-lines",
        action="store_true",
        help=(
            "Merge wrapped lines into paragraphs. Disabled by default because PDF "
            "text extraction can place short headings and list items on plain lines."
        ),
    )
    return parser.parse_args()


def preclean_markdown(markdown: str, merge_lines: bool = False) -> str:
    front_matter, body = split_front_matter(markdown)
    lines = normalize_lines(body.splitlines())
    lines = remove_mechanical_noise(lines)
    lines = promote_headings(lines)
    if merge_lines:
        lines = merge_wrapped_lines(lines)
    body = normalize_blank_lines(lines)
    return update_front_matter(front_matter) + body.strip() + "\n"


def split_front_matter(markdown: str) -> tuple[list[str], str]:
    lines = markdown.splitlines()
    if not lines or lines[0].strip() != "---":
        return [], markdown

    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return lines[: index + 1], "\n".join(lines[index + 1 :])
    return [], markdown


def update_front_matter(front_matter: list[str]) -> str:
    if not front_matter:
        return "---\nstatus: preclean\n---\n\n"

    updated: list[str] = []
    saw_status = False
    saw_precleaner = False
    for line in front_matter:
        if line.startswith("status:"):
            updated.append("status: preclean")
            saw_status = True
        elif line.startswith("precleaner:"):
            updated.append("precleaner: conservative-script")
            saw_precleaner = True
        else:
            updated.append(line)

    insert_at = max(1, len(updated) - 1)
    if not saw_status:
        updated.insert(insert_at, "status: preclean")
        insert_at += 1
    if not saw_precleaner:
        updated.insert(insert_at, "precleaner: conservative-script")

    return "\n".join(updated).strip() + "\n\n"


def normalize_lines(lines: list[str]) -> list[str]:
    return [normalize_line(line) for line in lines]


def normalize_line(line: str) -> str:
    line = line.replace("\u3000", " ")
    line = re.sub(r"[ \t]+", " ", line)
    return line.strip()


def remove_mechanical_noise(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    for line in lines:
        if line in HEADER_NOISE:
            continue
        if PAGE_NUMBER_RE.fullmatch(line):
            continue
        cleaned.append(line)
    return cleaned


def promote_headings(lines: list[str]) -> list[str]:
    promoted: list[str] = []
    seen_chapter_titles: set[str] = set()

    for line in lines:
        if not line:
            promoted.append(line)
            continue
        if PAGE_MARK_RE.fullmatch(line):
            promoted.append("")
            promoted.append(line)
            promoted.append("")
            continue

        if CHAPTER_TITLE_RE.fullmatch(line):
            if line in seen_chapter_titles:
                continue
            seen_chapter_titles.add(line)
            promoted.append(f"# {line}")
            continue

        if NUMBERED_HEADING_RE.fullmatch(line) and not line.endswith(("。", "，", "；", "：")):
            promoted.append(f"## {line}")
            continue

        promoted.append(line)

    return promoted


def merge_wrapped_lines(lines: list[str]) -> list[str]:
    merged: list[str] = []
    paragraph: list[str] = []

    def flush() -> None:
        if not paragraph:
            return
        merged.append(join_paragraph_lines(paragraph))
        paragraph.clear()

    for line in lines:
        if should_keep_as_own_line(line):
            flush()
            merged.append(line)
            continue
        if not line:
            flush()
            merged.append("")
            continue
        paragraph.append(line)

    flush()
    return merged


def should_keep_as_own_line(line: str) -> bool:
    if not line:
        return False
    return (
        line.startswith("#")
        or PAGE_MARK_RE.fullmatch(line) is not None
        or line.startswith("---")
        or line.startswith("|")
        or line.startswith("- ")
        or line.startswith("* ")
        or re.match(r"^\d+[.)]\s+", line) is not None
    )


def join_paragraph_lines(lines: list[str]) -> str:
    result = lines[0]
    for line in lines[1:]:
        if should_insert_space(result, line):
            result += " " + line
        else:
            result += line
    return result


def should_insert_space(previous: str, current: str) -> bool:
    if not previous or not current:
        return False
    return is_ascii_word_char(previous[-1]) and is_ascii_word_char(current[0])


def is_ascii_word_char(char: str) -> bool:
    return char.isascii() and (char.isalnum() or char in {"_", "%", ")"})


def normalize_blank_lines(lines: list[str]) -> str:
    output: list[str] = []
    blank_count = 0
    for line in lines:
        if not line:
            blank_count += 1
            if blank_count <= 2:
                output.append("")
            continue
        blank_count = 0
        output.append(line)
    return "\n".join(output)


if __name__ == "__main__":
    main()
