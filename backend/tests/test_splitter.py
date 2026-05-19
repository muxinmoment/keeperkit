from app.rag.splitter import split_documents
from app.rag.types import RawDocument


def test_splitter_keeps_heading_metadata() -> None:
    docs = [RawDocument(content="# A\n\nText\n\n## B\n\nMore", metadata={"source": "x.md"})]
    chunks = split_documents(docs)
    assert chunks
    assert chunks[0].metadata["source"] == "x.md"
    assert chunks[-1].metadata["title_path"] == ["A", "B"]
