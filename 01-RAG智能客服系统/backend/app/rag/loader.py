"""Document loaders for various file types.

Avoids spaCy dependency by using simple text reading when possible
(UnstructuredMarkdownLoader pulls in spaCy which can't install in Docker).
"""
import os
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document


def load_document(file_path: str, file_type: str) -> list[Document]:
    """Load a document based on its file type.

    Args:
        file_path: Absolute path to the document file
        file_type: One of 'pdf', 'txt', 'md', 'csv', 'docx'

    Returns:
        List of LangChain Document objects
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # ── Markdown / TXT — simple text read, no spaCy ──────────────
    if file_type in ("txt", "md"):
        for enc in ["utf-8-sig", "utf-8", "gbk", "gb2312", "latin-1"]:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read()
                if content.strip():
                    break
            except (UnicodeDecodeError, UnicodeError):
                content = ""
        if not content:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        doc = Document(
            page_content=content,
            metadata={"source_file": os.path.basename(file_path), "file_type": file_type},
        )
        return [doc]

    # ── PDF ──────────────────────────────────────────────────────
    if file_type == "pdf":
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(file_path)

    # ── CSV ──────────────────────────────────────────────────────
    elif file_type == "csv":
        from langchain_community.document_loaders import CSVLoader
        loader = CSVLoader(file_path, encoding="utf-8-sig")

    # ── DOCX ─────────────────────────────────────────────────────
    elif file_type == "docx":
        from langchain_community.document_loaders import Docx2txtLoader
        loader = Docx2txtLoader(file_path)

    else:
        raise ValueError(f"不支持的文件类型: {file_type}")

    documents = loader.load()

    # Add source metadata
    for doc in documents:
        doc.metadata["source_file"] = os.path.basename(file_path)
        doc.metadata["file_type"] = file_type

    return documents
