"""PDF processing, section-aware chunking, verifiable page pinning, and visual bounding-box highlighting."""

import base64
import re
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF
import httpx

MAX_PDF_BYTES = 50 * 1024 * 1024  # 50 MB limit
UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads" / "papers"


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


SECTION_PATTERN = re.compile(
    r"^(?:[0-9IVX]+\.?\s*)?(abstract|introduction|related work|background|methodology|methods|system design|experimental setup|experiments|results|discussion|limitations|conclusion|references)",
    re.IGNORECASE,
)


class PDFProcessorService:
    @staticmethod
    def validate_and_save_pdf(
        pdf_bytes: bytes,
        *,
        owner_id: str,
        project_id: str,
        paper_id: str,
    ) -> Path:
        """Validate PDF magic header + size cap and save isolated inside project folder."""
        if not pdf_bytes or len(pdf_bytes) > MAX_PDF_BYTES:
            raise ValueError("PDF file is empty or exceeds 50MB limit.")
        if not pdf_bytes.lstrip().startswith(b"%PDF-"):
            raise ValueError("Invalid file content: missing %PDF- header.")

        target_dir = UPLOAD_ROOT / owner_id / project_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{paper_id}.pdf"
        target_path.write_bytes(pdf_bytes)
        return target_path

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
    def get_evidence_highlight_data(
        pdf_path: Path,
        page_num: int,
        quote_text: str,
        *,
        render_image: bool = True,
    ) -> dict:
        """Locate normalized bounding boxes [0, 1] for `quote_text` on `page_num` and render PNG."""
        if not pdf_path.exists():
            return {"page": page_num, "boxes": [], "page_image_base64": None}

        doc = fitz.open(str(pdf_path))
        try:
            if page_num < 1 or page_num > len(doc):
                return {"page": page_num, "boxes": [], "page_image_base64": None}

            page = doc[page_num - 1]
            norm_text = re.sub(r"\s+", " ", quote_text).strip()
            quads = page.search_for(quote_text, quads=True) if quote_text else []
            if not quads and norm_text:
                quads = page.search_for(norm_text, quads=True)
            if not quads and norm_text:
                words = norm_text.split()
                for i in range(0, len(words), 6):
                    sub = " ".join(words[i : i + 6])
                    if len(sub) > 10:
                        quads.extend(page.search_for(sub, quads=True))

            pw = max(page.rect.width, 1.0)
            ph = max(page.rect.height, 1.0)
            boxes = [
                {
                    "x": round(q.rect.x0 / pw, 4),
                    "y": round(q.rect.y0 / ph, 4),
                    "width": round(q.rect.width / pw, 4),
                    "height": round(q.rect.height / ph, 4),
                }
                for q in quads
            ]

            image_b64 = None
            if render_image:
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                image_b64 = base64.b64encode(pix.tobytes("png")).decode("ascii")

            return {
                "page": page_num,
                "total_pages": len(doc),
                "boxes": boxes,
                "page_image_base64": image_b64,
            }
        finally:
            doc.close()

    @staticmethod
    async def download_pdf_bytes(pdf_url: str) -> bytes:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(pdf_url)
            resp.raise_for_status()
            return resp.content

    @staticmethod
    async def download_and_process_pdf(pdf_url: str) -> list[SemanticChunk]:
        """Download remote PDF and convert into pinned chunks."""
        pdf_bytes = await PDFProcessorService.download_pdf_bytes(pdf_url)
        pages = PDFProcessorService.extract_pages_from_bytes(pdf_bytes)
        return PDFProcessorService.chunk_extracted_pages(pages)


pdf_processor = PDFProcessorService()
