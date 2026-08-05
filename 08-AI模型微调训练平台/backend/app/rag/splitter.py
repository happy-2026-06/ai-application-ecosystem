"""Chinese-aware text chunking strategies."""
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.config import settings


def split_documents(
    documents: list[Document],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Document]:
    """Split documents into chunks using Chinese-aware separators.

    Uses a hierarchy of separators that respect Chinese punctuation:
    - Double newline (paragraph boundaries)
    - Single newline
    - Chinese period/full stop 。
    - Chinese exclamation mark ！
    - Chinese question mark ？
    - Chinese semicolon ；
    - Chinese comma ，
    - Space
    - Character-level (last resort)
    """
    if chunk_size is None:
        chunk_size = settings.CHUNK_SIZE
    if chunk_overlap is None:
        chunk_overlap = settings.CHUNK_OVERLAP

    # Chinese-aware separators: prioritize paragraph and sentence boundaries
    chinese_separators = [
        "\n\n",     # Paragraph break
        "\n",       # Line break
        "。",       # Chinese period
        "！",       # Chinese exclamation
        "？",       # Chinese question
        "；",       # Chinese semicolon
        "，",       # Chinese comma
        ". ",       # English period
        "! ",       # English exclamation
        "? ",       # English question
        "; ",       # English semicolon
        ", ",       # English comma
        " ",        # Space
        "",         # Character-level
    ]

    splitter = RecursiveCharacterTextSplitter(
        separators=chinese_separators,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )

    chunks = splitter.split_documents(documents)
    return chunks
