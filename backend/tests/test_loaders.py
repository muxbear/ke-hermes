"""Tests for document loaders in src.core.rag.loaders."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from langchain_core.documents import Document

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.rag.loaders import (
    CSVLoaderStrategy,
    DocxLoaderStrategy,
    DocumentLoaderRegistry,
    FallbackLoaderStrategy,
    HTMLLoaderStrategy,
    ImageLoaderStrategy,
    JSONLoaderStrategy,
    MarkdownLoaderStrategy,
    OpenDataLoaderPDFStrategy,
    PyPDFLoaderStrategy,
    PythonPPTXLoaderStrategy,
    TextLoaderStrategy,
    UnstructuredExcelStrategy,
    UnstructuredPPTStrategy,
    create_default_loader_registry,
)

FIXTURES = Path(__file__).parent / "fixtures"

PDF_PATH = str(FIXTURES / "sample.pdf")
DOCX_PATH = str(FIXTURES / "sample.docx")
XLSX_PATH = str(FIXTURES / "sample.xlsx")
PPTX_PATH = str(FIXTURES / "sample.pptx")
CSV_PATH = str(FIXTURES / "sample.csv")
JSON_PATH = str(FIXTURES / "sample.json")
MD_PATH = str(FIXTURES / "sample.md")
HTML_PATH = str(FIXTURES / "sample.html")
TXT_PATH = str(FIXTURES / "sample.txt")
PNG_PATH = str(FIXTURES / "sample.png")
MISSING_PATH = str(FIXTURES / "nonexistent.xyz")


# ==================== PyPDFLoaderStrategy ====================


def test_pypdf_loader_loads_documents():
    strategy = PyPDFLoaderStrategy()
    docs = strategy.load(PDF_PATH)
    assert isinstance(docs, list)
    assert len(docs) > 0
    assert all(isinstance(d, Document) for d in docs)
    assert any("Test PDF" in d.page_content for d in docs)


def test_pypdf_loader_file_not_found():
    strategy = PyPDFLoaderStrategy()
    with pytest.raises(Exception):
        strategy.load(MISSING_PATH)


# ==================== OpenDataLoaderPDFStrategy ====================


@pytest.mark.skip(
    reason="Hand-crafted test PDF is not a valid PDF (rejected by Java CLI). "
    "The fallback chain (OpenDataLoaderPDF → PyPDFLoader) is tested "
    "via test_default_registry_load_pdf and test_default_registry_load_all_working_types."
)
def test_opendataloader_pdf_loads_documents():
    strategy = OpenDataLoaderPDFStrategy()
    docs = strategy.load(PDF_PATH)
    assert isinstance(docs, list)
    assert len(docs) > 0
    assert all(isinstance(d, Document) for d in docs)
    assert any("Test PDF" in d.page_content for d in docs)


def test_opendataloader_pdf_missing_file_raises():
    """FIXED: now raises FileNotFoundError for missing files."""
    strategy = OpenDataLoaderPDFStrategy()
    with pytest.raises(FileNotFoundError, match="not found"):
        strategy.load(MISSING_PATH)


# ==================== DocxLoaderStrategy ====================


def test_docx_loader_loads_documents():
    strategy = DocxLoaderStrategy()
    docs = strategy.load(DOCX_PATH)
    assert isinstance(docs, list)
    assert len(docs) > 0
    assert all(isinstance(d, Document) for d in docs)
    contents = " ".join(d.page_content for d in docs)
    assert "Test Document" in contents
    assert "test Word document" in contents


def test_docx_loader_file_not_found():
    strategy = DocxLoaderStrategy()
    with pytest.raises(Exception):
        strategy.load(MISSING_PATH)


# ==================== UnstructuredExcelStrategy ====================


def test_excel_loader_loads_documents():
    strategy = UnstructuredExcelStrategy()
    docs = strategy.load(XLSX_PATH)
    assert isinstance(docs, list)
    assert len(docs) > 0
    assert all(isinstance(d, Document) for d in docs)


def test_excel_loader_file_not_found():
    strategy = UnstructuredExcelStrategy()
    with pytest.raises(Exception):
        strategy.load(MISSING_PATH)


# ==================== PythonPPTXLoaderStrategy ====================


def test_pptx_loader_loads_documents():
    strategy = PythonPPTXLoaderStrategy()
    docs = strategy.load(PPTX_PATH)
    assert isinstance(docs, list)
    assert len(docs) > 0
    assert all(isinstance(d, Document) for d in docs)
    contents = " ".join(d.page_content for d in docs)
    assert "Test Presentation" in contents


def test_pptx_loader_file_not_found():
    strategy = PythonPPTXLoaderStrategy()
    with pytest.raises(Exception):
        strategy.load(MISSING_PATH)


# ==================== UnstructuredPPTStrategy ====================

@pytest.mark.skip(
    reason="UnstructuredPowerPointLoader crashes on Windows (python-magic segfault)"
)
def test_unstructured_ppt_raises_on_windows():
    strategy = UnstructuredPPTStrategy()
    docs = strategy.load(PPTX_PATH)
    assert isinstance(docs, list)
    assert len(docs) > 0


# ==================== CSVLoaderStrategy ====================


def test_csv_loader_loads_documents():
    strategy = CSVLoaderStrategy()
    docs = strategy.load(CSV_PATH)
    assert isinstance(docs, list)
    assert len(docs) > 0
    assert all(isinstance(d, Document) for d in docs)
    contents = " ".join(d.page_content for d in docs)
    assert "Alice" in contents


def test_csv_loader_file_not_found():
    strategy = CSVLoaderStrategy()
    with pytest.raises(Exception):
        strategy.load(MISSING_PATH)


# ==================== JSONLoaderStrategy ====================


def test_json_loader_loads_documents():
    strategy = JSONLoaderStrategy()
    docs = strategy.load(JSON_PATH)
    assert isinstance(docs, list)
    assert len(docs) > 0
    assert all(isinstance(d, Document) for d in docs)
    contents = " ".join(d.page_content for d in docs)
    assert "Test Document" in contents


def test_json_loader_file_not_found():
    strategy = JSONLoaderStrategy()
    with pytest.raises(Exception):
        strategy.load(MISSING_PATH)


# ==================== MarkdownLoaderStrategy ====================


def test_markdown_loader_loads_documents():
    strategy = MarkdownLoaderStrategy()
    docs = strategy.load(MD_PATH)
    assert isinstance(docs, list)
    assert len(docs) > 0
    assert all(isinstance(d, Document) for d in docs)
    contents = " ".join(d.page_content for d in docs)
    assert "Test Markdown" in contents


def test_markdown_loader_mode_elements():
    strategy = MarkdownLoaderStrategy()
    docs = strategy.load(MD_PATH)
    assert len(docs) >= 1


# ==================== HTMLLoaderStrategy ====================


def test_html_loader_loads_documents():
    strategy = HTMLLoaderStrategy()
    docs = strategy.load(HTML_PATH)
    assert isinstance(docs, list)
    assert len(docs) > 0
    assert all(isinstance(d, Document) for d in docs)
    contents = docs[0].page_content
    # BSHTMLLoader extracts clean text, no raw HTML tags
    assert "Hello World" in contents
    assert "test HTML file" in contents
    # Should NOT contain raw tags
    assert "<h1>" not in contents
    assert "<body>" not in contents


def test_html_loader_extracts_title():
    """FIXED: BSHTMLLoader extracts <title> into metadata."""
    strategy = HTMLLoaderStrategy()
    docs = strategy.load(HTML_PATH)
    assert docs[0].metadata.get("title") == "Test Page"


# ==================== TextLoaderStrategy ====================


def test_text_loader_loads_documents():
    strategy = TextLoaderStrategy()
    docs = strategy.load(TXT_PATH)
    assert isinstance(docs, list)
    assert len(docs) > 0
    assert all(isinstance(d, Document) for d in docs)
    assert "plain text test file" in docs[0].page_content


def test_text_loader_file_not_found():
    strategy = TextLoaderStrategy()
    with pytest.raises(Exception):
        strategy.load(MISSING_PATH)


# ==================== ImageLoaderStrategy ====================


def test_image_loader_no_tesseract_raises():
    """FIXED: raises RuntimeError when Tesseract is not available."""
    strategy = ImageLoaderStrategy()
    with pytest.raises(RuntimeError, match="Tesseract"):
        strategy.load(PNG_PATH)


# ==================== FallbackLoaderStrategy ====================


class _FakeSuccessStrategy(PyPDFLoaderStrategy):
    def load(self, file_path: str) -> list[Document]:
        return [Document(page_content="success")]


class _FakeFailStrategy(PyPDFLoaderStrategy):
    def load(self, file_path: str) -> list[Document]:
        raise RuntimeError("intentional failure")


def test_fallback_uses_first_success():
    strategy = FallbackLoaderStrategy([
        _FakeSuccessStrategy(),
        _FakeFailStrategy(),
    ])
    docs = strategy.load("dummy.txt")
    assert len(docs) == 1
    assert docs[0].page_content == "success"


def test_fallback_skips_failures():
    strategy = FallbackLoaderStrategy([
        _FakeFailStrategy(),
        _FakeSuccessStrategy(),
    ])
    docs = strategy.load("dummy.txt")
    assert len(docs) == 1
    assert docs[0].page_content == "success"


def test_fallback_all_fail_raises_valueerror():
    strategy = FallbackLoaderStrategy([
        _FakeFailStrategy(),
        _FakeFailStrategy(),
    ])
    with pytest.raises(ValueError, match="All loaders failed"):
        strategy.load("dummy.txt")


def test_fallback_empty_list_raises():
    strategy = FallbackLoaderStrategy([])
    with pytest.raises(ValueError, match="All loaders failed"):
        strategy.load("dummy.txt")


# ==================== DocumentLoaderRegistry ====================


def test_registry_register_and_get():
    registry = DocumentLoaderRegistry()
    fake = _FakeSuccessStrategy()
    registry.register("test", fake)
    assert registry.get_strategy("test") is fake


def test_registry_unsupported_type_raises():
    registry = DocumentLoaderRegistry()
    with pytest.raises(ValueError, match="Unsupported file type"):
        registry.get_strategy("unknown_type")


def test_registry_load_delegates():
    registry = DocumentLoaderRegistry()
    registry.register("fake", _FakeSuccessStrategy())
    docs = registry.load("dummy.txt", "fake")
    assert docs[0].page_content == "success"


# ==================== create_default_loader_registry ====================


def test_default_registry_has_all_types():
    registry = create_default_loader_registry()
    expected_types = [
        "pdf", "docx", "xlsx", "pptx", "csv", "json",
        "md", "html", "txt", "png", "jpg", "jpeg", "image",
    ]
    for ft in expected_types:
        strategy = registry.get_strategy(ft)
        assert strategy is not None, f"Missing strategy for type: {ft}"


def test_default_registry_pdf_is_fallback():
    registry = create_default_loader_registry()
    strategy = registry.get_strategy("pdf")
    assert isinstance(strategy, FallbackLoaderStrategy)
    assert len(strategy._strategies) == 2
    assert isinstance(strategy._strategies[0], OpenDataLoaderPDFStrategy)
    assert isinstance(strategy._strategies[1], PyPDFLoaderStrategy)


def test_default_registry_pptx_is_fallback():
    """FIXED: PPTX now uses PythonPPTXLoaderStrategy + UnstructuredPPTStrategy fallback."""
    registry = create_default_loader_registry()
    strategy = registry.get_strategy("pptx")
    assert isinstance(strategy, FallbackLoaderStrategy)
    assert len(strategy._strategies) == 2
    assert isinstance(strategy._strategies[0], PythonPPTXLoaderStrategy)
    assert isinstance(strategy._strategies[1], UnstructuredPPTStrategy)


def test_default_registry_load_pdf():
    registry = create_default_loader_registry()
    docs = registry.load(PDF_PATH, "pdf")
    assert isinstance(docs, list)
    assert len(docs) > 0
    assert all(isinstance(d, Document) for d in docs)


def test_default_registry_load_all_working_types():
    """Verifies all types load correctly via the default registry."""
    registry = create_default_loader_registry()
    tests = {
        "pdf": PDF_PATH,
        "docx": DOCX_PATH,
        "xlsx": XLSX_PATH,
        "pptx": PPTX_PATH,
        "csv": CSV_PATH,
        "json": JSON_PATH,
        "md": MD_PATH,
        "html": HTML_PATH,
        "txt": TXT_PATH,
    }
    for ft, path in tests.items():
        docs = registry.load(path, ft)
        assert isinstance(docs, list), f"{ft}: expected list, got {type(docs)}"
        assert len(docs) > 0, f"{ft}: returned 0 documents"
        assert all(isinstance(d, Document) for d in docs), \
            f"{ft}: not all items are Document"
