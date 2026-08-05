"""Document loaders for various file types."""
import os
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
    UnstructuredMarkdownLoader,
    Docx2txtLoader,
)
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

    loader_map = {
        "pdf": PyPDFLoader,
        "txt": TextLoader,
        "md": UnstructuredMarkdownLoader,
        "csv": CSVLoader,
        "docx": Docx2txtLoader,
    }

    loader_cls = loader_map.get(file_type)
    if loader_cls is None:
        raise ValueError(f"不支持的文件类型: {file_type}")

    # PDF loader needs different params
    if file_type == "pdf":
        loader = loader_cls(file_path)
    elif file_type == "csv":
        loader = loader_cls(file_path, encoding="utf-8-sig")
    elif file_type == "txt":
        loader = loader_cls(file_path, encoding="utf-8")
    else:
        loader = loader_cls(file_path)

    documents = loader.load()

    # Add source metadata
    for doc in documents:
        doc.metadata["source_file"] = os.path.basename(file_path)
        doc.metadata["file_type"] = file_type

    return documents
