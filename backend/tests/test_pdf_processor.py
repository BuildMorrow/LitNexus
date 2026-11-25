"""Test suite for PDF Processing, Page Pinning, and Section Extraction."""

import fitz  # PyMuPDF

from app.services.pdf_processor import pdf_processor


def test_pdf_processor_extract_and_chunk():
    # 1. Create an in-memory test PDF with 2 pages and section headers
    doc = fitz.open()

    p1 = doc.new_page()
    p1.insert_text(
        fitz.Point(50, 72),
        "Abstract\nThis paper introduces an ultra-lightweight 1D CNN for single-lead wearable ECG.\n"
        "1. Introduction\nWearable cardiac telemetry requires micro-power computation on ambulatory patches.",
    )

    p2 = doc.new_page()
    p2.insert_text(
        fitz.Point(50, 72),
        "3. Experimental Results\nOur 1D model achieves 98.2% F1 on MIT-BIH benchmark with 18ms latency.\n"
        "4. Conclusion\nReal-time arrhythmia screening on microcontrollers is feasible.",
    )

    pdf_bytes = doc.tobytes()
    doc.close()

    # 2. Extract pages
    pages = pdf_processor.extract_pages_from_bytes(pdf_bytes)
    assert len(pages) == 2
    assert pages[0].page_number == 1
    assert pages[1].page_number == 2
    assert pages[1].section_title in ("Experimental Results", "Results", "Conclusion")

    # 3. Semantic chunking with page pinning
    chunks = pdf_processor.chunk_extracted_pages(pages, chunk_size=20, chunk_overlap=5)
    assert len(chunks) >= 2
    for ch in chunks:
        assert ch.page_number in (1, 2)
        assert len(ch.content) > 0
