"""
extract_paper.py - Extract text from PDF research papers into structured Markdown.

Usage:
    python extract_paper.py paper.pdf --output paper.md

Dependencies:
    pip install PyMuPDF
"""

import argparse
import sys
import os

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF is required. Install with: pip install PyMuPDF")
    sys.exit(1)


def detect_heading_level(span_font_size, base_font_size):
    if base_font_size == 0:
        return 0
    ratio = span_font_size / base_font_size
    if ratio > 1.8:
        return 1
    elif ratio > 1.4:
        return 2
    elif ratio > 1.15:
        return 3
    return 0


def get_base_font_size(page_blocks):
    size_counts = {}
    for block in page_blocks:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                if not text:
                    continue
                size = round(span["size"], 1)
                size_counts[size] = size_counts.get(size, 0) + len(text)
    if not size_counts:
        return 12.0
    return max(size_counts, key=size_counts.get)


def extract_page_text(page):
    blocks = page.get_text("dict", sort=True)["blocks"]
    base_size = get_base_font_size(blocks)
    lines = []

    for block in blocks:
        if block["type"] == 1:
            lines.append("\n![image]\n")
            continue

        if block["type"] != 0:
            continue

        block_text_parts = []
        block_heading = 0

        for line in block["lines"]:
            line_text = ""
            line_heading = 0
            for span in line["spans"]:
                text = span["text"]
                if not text.strip():
                    line_text += text
                    continue
                h = detect_heading_level(span["size"], base_size)
                if h > 0:
                    line_heading = max(line_heading, h)
                line_text += text

            stripped = line_text.strip()
            if stripped:
                block_text_parts.append(stripped)
                if line_heading > 0:
                    block_heading = max(block_heading, line_heading)

        if not block_text_parts:
            continue

        full_text = " ".join(block_text_parts)

        if block_heading > 0:
            prefix = "#" * block_heading
            lines.append(f"\n{prefix} {full_text}\n")
        else:
            lines.append(full_text)
            lines.append("")

    return "\n".join(lines)


def extract_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    doc = fitz.open(pdf_path)
    metadata = doc.metadata
    pages_text = []

    title = metadata.get("title", "").strip()

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = extract_page_text(page)
        pages_text.append(f"<!-- Page {page_num + 1} -->\n\n{text}")

    doc.close()

    output_parts = []
    if title:
        output_parts.append(f"# {title}\n")
    output_parts.append(f"**Source**: {os.path.basename(pdf_path)}  ")
    output_parts.append(f"**Pages**: {len(pages_text)}\n")
    output_parts.append("---\n")
    output_parts.append("\n\n".join(pages_text))

    return "\n".join(output_parts)


def main():
    parser = argparse.ArgumentParser(description="Extract text from PDF research papers")
    parser.add_argument("pdf", help="Path to the PDF file")
    parser.add_argument("--output", "-o", required=True, help="Output Markdown file path")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

    print(f"[extract] Processing: {args.pdf}")
    markdown = extract_pdf(args.pdf)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"[extract] Output written to: {args.output}")
    print(f"[extract] Size: {len(markdown)} characters")


if __name__ == "__main__":
    main()
