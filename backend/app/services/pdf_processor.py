"""PDF processing, section-aware chunking, and verifiable page pinning service.

Leverages PyMuPDF (fitz) to ingest academic PDFs, extract text tagged by page number,
detect major academic section headers, and chunk content for pgvector embedding.
"""

import re
from dataclasses import dataclass

import fitz  # PyMuPDF
import httpx


@dataclass
class ExtractedPageText:
    page_number: int
    text: str
    section_title: str | None


@dataclass
class SemanticChunk:
    chunk_index: int
    page_number: int
    section_title: str | None
    content: str


# Regex matching common scientific paper section headings
SECTION_PATTERN = re.compile(
    r"^(?:[0-9IVX]+\.?\s*)?(abstract|introduction|related work|background|methodology|methods|system design|experimental setup|experiments|results|discussion|limitations|conclusion|references)",
    re.IGNORECASE,
)


class PDFProcessorService:
    @staticmethod
    def extract_pages_from_bytes(pdf_bytes: bytes) -> list[ExtractedPageText]:
        """Extract pages from raw PDF bytes with academic section tracking."""
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages: list[ExtractedPageText] = []
        current_section = "Abstract"

        for page_idx in range(len(doc)):
            page_num = page_idx + 1
            page = doc.load_page(page_idx)
            text = page.get_text("text")

            # Simple heuristic detection of section headings in page lines
            for line in text.split("\n")[:15]:
                match = SECTION_PATTERN.match(line.strip())
                if match:
                    current_section = match.group(1).title()
                    break

            pages.append(
                ExtractedPageText(
                    page_number=page_num,
                    text=text.strip(),
                    section_title=current_section,
                )
            )

        doc.close()
        return pages

    @staticmethod
    def chunk_extracted_pages(
        pages: list[ExtractedPageText],
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> list[SemanticChunk]:
        """Create overlapping text chunks pinned to specific page numbers and sections."""
        chunks: list[SemanticChunk] = []
        chunk_idx = 0

        for p in pages:
            words = p.text.split()
            if not words:
                continue

            step = max(chunk_size - chunk_overlap, 1)
            for i in range(0, len(words), step):
                chunk_words = words[i : i + chunk_size]
                chunk_text = " ".join(chunk_words)

                chunks.append(
                    SemanticChunk(
                        chunk_index=chunk_idx,
                        page_number=p.page_number,
                        section_title=p.section_title,
                        content=chunk_text,
                    )
                )
                chunk_idx += 1

                if i + chunk_size >= len(words):
                    break

        return chunks

    @staticmethod
    async def download_and_process_pdf(pdf_url: str) -> list[SemanticChunk]:
        """Download remote PDF and convert into pinned chunks."""
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(pdf_url)
            resp.raise_for_status()
            pdf_bytes = resp.content

        pages = PDFProcessorService.extract_pages_from_bytes(pdf_bytes)
        return PDFProcessorService.chunk_extracted_pages(pages)


pdf_processor = PDFProcessorService()
