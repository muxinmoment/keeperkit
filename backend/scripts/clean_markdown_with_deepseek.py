from __future__ import annotations

import argparse
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = BACKEND_DIR / "data" / "raw" / "private" / "preclean_markdown_chapters"
DEFAULT_OUTPUT_DIR = BACKEND_DIR / "data" / "raw" / "private" / "clean_markdown_chapters"

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-pro"
TARGET_CHUNK_CHARS = 18000


SYSTEM_PROMPT = """你是规则书 Markdown 清洗器。

你只能整理格式，不能总结、不能改写规则含义、不能新增规则。

硬性要求：
1. 保留全部规则文本、数值、骰子表达式、技能名、伤害值、规则条件。
2. 不要删除规则内容；如果遇到疑似噪声但不确定，保留。
3. 删除页眉、页脚、孤立页码、重复版权噪声。
4. 保留 <!-- page: n --> 页码注释。
5. 修复 PDF 抽取导致的断行，把同一段落合并。
6. 将章节标题、小节标题整理为 #、##、###。
7. 表格尽量转成 Markdown 表格；无法可靠还原时，用列表逐行保留。
8. 不要输出解释、说明、前后缀，只输出 Markdown 正文。
"""


USER_PROMPT_TEMPLATE = """请清洗下面这个 Markdown 片段。

这是同一个章节的第 {chunk_index}/{chunk_total} 个片段。请只处理当前片段，不要补写其他片段内容。

待清洗 Markdown：

{content}
"""


def main() -> None:
    args = parse_args()
    load_dotenv(BACKEND_DIR / ".env")

    api_key = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL)
    model = os.getenv("LLM_MODEL", DEFAULT_MODEL)
    if not api_key or api_key == "replace-me":
        raise SystemExit(
            "Missing DeepSeek API key. Create backend/.env and set LLM_API_KEY=your_key."
        )

    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    if not input_dir.exists():
        raise SystemExit(f"Input directory not found: {input_dir}")

    markdown_files = select_markdown_files(input_dir, args.files, args.limit)
    if not markdown_files:
        raise SystemExit(f"No Markdown files selected from: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    client = OpenAI(api_key=api_key, base_url=base_url)

    converted = 0
    skipped = 0
    for source_path in markdown_files:
        output_path = output_dir / source_path.name
        if output_path.exists() and not args.overwrite:
            skipped += 1
            print(f"Skip existing: {output_path.name}")
            continue

        markdown = source_path.read_text(encoding="utf-8")
        cleaned = clean_document(
            client=client,
            model=model,
            markdown=markdown,
            target_chunk_chars=args.chunk_chars,
            temperature=args.temperature,
            sleep_seconds=args.sleep,
        )
        output_path.write_text(cleaned, encoding="utf-8")
        converted += 1
        print(f"Cleaned: {source_path.name} -> {output_path.name}")

    print(f"Done. converted={converted}, skipped={skipped}, output={output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean pre-cleaned Markdown chapters with DeepSeek.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=f"Directory containing pre-cleaned Markdown. Default: {DEFAULT_INPUT_DIR}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for DeepSeek-cleaned Markdown. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="Specific Markdown filenames to clean, e.g. 07-第五章-游戏系统.md",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Clean only the first N Markdown files after sorting.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing cleaned Markdown files.",
    )
    parser.add_argument(
        "--chunk-chars",
        type=int,
        default=TARGET_CHUNK_CHARS,
        help="Approximate maximum characters per model call.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Model temperature. Keep 0 for deterministic cleaning.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.3,
        help="Seconds to sleep between model calls.",
    )
    return parser.parse_args()


def select_markdown_files(
    input_dir: Path,
    filenames: list[str] | None,
    limit: int | None,
) -> list[Path]:
    if filenames:
        selected = [input_dir / filename for filename in filenames]
        missing = [path for path in selected if not path.exists()]
        if missing:
            raise SystemExit(
                "Missing selected files: " + ", ".join(str(path) for path in missing)
            )
        return selected

    selected = sorted(input_dir.glob("*.md"))
    if limit is not None:
        selected = selected[:limit]
    return selected


def clean_document(
    client: OpenAI,
    model: str,
    markdown: str,
    target_chunk_chars: int,
    temperature: float,
    sleep_seconds: float,
) -> str:
    front_matter, body = split_front_matter(markdown)
    chunks = split_by_page_marks(body, target_chunk_chars)
    cleaned_chunks: list[str] = []

    for index, chunk in enumerate(chunks, start=1):
        cleaned = clean_chunk(
            client=client,
            model=model,
            content=chunk,
            chunk_index=index,
            chunk_total=len(chunks),
            temperature=temperature,
        )
        cleaned_chunks.append(strip_code_fences(cleaned).strip())
        if sleep_seconds > 0 and index < len(chunks):
            time.sleep(sleep_seconds)

    cleaned_body = "\n\n".join(part for part in cleaned_chunks if part).strip()
    return update_front_matter(front_matter) + cleaned_body + "\n"


def clean_chunk(
    client: OpenAI,
    model: str,
    content: str,
    chunk_index: int,
    chunk_total: int,
    temperature: float,
) -> str:
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    chunk_index=chunk_index,
                    chunk_total=chunk_total,
                    content=content,
                ),
            },
        ],
    )
    text = response.choices[0].message.content
    if not text:
        raise RuntimeError(f"Empty model output for chunk {chunk_index}/{chunk_total}")
    return text


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
        return "---\nstatus: clean\ncleaner: deepseek\n---\n\n"

    updated: list[str] = []
    saw_status = False
    saw_cleaner = False
    for line in front_matter:
        if line.startswith("status:"):
            updated.append("status: clean")
            saw_status = True
        elif line.startswith("cleaner:"):
            updated.append("cleaner: deepseek")
            saw_cleaner = True
        else:
            updated.append(line)

    insert_at = max(1, len(updated) - 1)
    if not saw_status:
        updated.insert(insert_at, "status: clean")
        insert_at += 1
    if not saw_cleaner:
        updated.insert(insert_at, "cleaner: deepseek")

    return "\n".join(updated).strip() + "\n\n"


def split_by_page_marks(body: str, target_chunk_chars: int) -> list[str]:
    pages = re.split(r"(?=^<!--\s*page:\s*\d+\s*-->)", body, flags=re.MULTILINE)
    pages = [page.strip() for page in pages if page.strip()]
    if not pages:
        return [body]

    chunks: list[str] = []
    current: list[str] = []
    current_size = 0
    for page in pages:
        page_size = len(page)
        if current and current_size + page_size > target_chunk_chars:
            chunks.append("\n\n".join(current))
            current = [page]
            current_size = page_size
        else:
            current.append(page)
            current_size += page_size

    if current:
        chunks.append("\n\n".join(current))
    return chunks


def strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:markdown|md)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped


if __name__ == "__main__":
    main()
