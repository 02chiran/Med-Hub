import io
import re

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader


# ============================================
# HELPERS
# ============================================

def _extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from a PDF given its raw bytes."""
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages)


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 100):
    """
    Split text into overlapping word-level chunks.
    Returns a list of strings.
    """
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def _score_chunk(chunk: str, query: str) -> int:
    """
    Simple keyword relevance score:
    count how many query words appear in the chunk (case-insensitive).
    """
    query_words = set(re.findall(r'\w+', query.lower()))
    chunk_lower = chunk.lower()
    return sum(1 for word in query_words if word in chunk_lower)


# ============================================
# PUBLIC API
# ============================================

def search_pdf(file_bytes: bytes, query: str, top_k: int = 5):
    """
    Parse a PDF from raw bytes, chunk it, score chunks against the
    query, and return the top_k chunks as evidence dicts compatible
    with aggregate_medical_evidence().

    Parameters
    ----------
    file_bytes : bytes
        Raw bytes of the uploaded PDF file.
    query : str
        The user's medical question.
    top_k : int
        Number of best-matching chunks to return.

    Returns
    -------
    list[dict]  Each dict has keys: source, title, content.
    """
    text = _extract_text_from_pdf(file_bytes)

    if not text.strip():
        return [{
            "source": "PDF (Uploaded)",
            "title": "Uploaded PDF",
            "content": (
                "No extractable text found in the PDF. "
                "It may be a scanned image-only document."
            )
        }]

    chunks = _chunk_text(text)

    # Score and sort
    scored = [
        (chunk, _score_chunk(chunk, query))
        for chunk in chunks
    ]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Keep only chunks that have at least 1 keyword hit
    top_chunks = [
        chunk for chunk, score in scored[:top_k]
        if score > 0
    ]

    if not top_chunks:
        # Fall back to the first few chunks if nothing matched
        top_chunks = [chunk for chunk, _ in scored[:3]]

    results = []
    for i, chunk in enumerate(top_chunks, 1):
        results.append({
            "source": "PDF (Uploaded)",
            "title": f"Uploaded PDF — passage {i}",
            "content": chunk
        })

    return results
