import os
import fitz
import logging
from docx import Document as DocxDocument

logger = logging.getLogger("documents")

def extract_text_from_pdf(path):
    text = ""
    
    try:
        doc = fitz.open(path)
        for page in doc:
            blocks = page.get_text("blocks")
            logger.info(f"Text: {blocks}")
            width = page.rect.width
            
            full_width_blocks = []
            left_blocks = []
            right_blocks = []

            for b in blocks:
                x0, y0, x1, y1, block_text = b[:5]
                block_width = x1 - x0

                # logger.info(f"coords: {x0}, {y0}, {x1}, {y1}, {block_text}")

                if not block_text.strip():
                    continue

                if block_width > width*0.7:
                    full_width_blocks.append((y0, block_text))
                else:
                    x_center = (x0 + x1)/2
                    if x_center < width / 2:
                        left_blocks.append((y0, block_text))
                    else:
                        right_blocks.append((y0, block_text))

            full_width_blocks = sorted(full_width_blocks, key=lambda x: x[0])
            left_blocks = sorted(left_blocks, key=lambda x: x[0])
            right_blocks = sorted(right_blocks, key=lambda x: x[0])

            ordered_blocks = []

            ordered_blocks.extend(full_width_blocks)
            ordered_blocks.extend(left_blocks)
            ordered_blocks.extend(right_blocks)

            for b in ordered_blocks:
                block_text = b[1].strip()
                if block_text:
                    text += block_text + "\n"
                    
    except Exception as e:
        logger.exception("PDF extraction failed", exc_info=True)
        return ""
    
    return text.strip()

def extract_text_from_docx(path):
    doc = DocxDocument(path)
    paragraphs = [p.text for p in doc.paragraphs]
    return "\n".join(paragraphs).strip()

def extract_text_from_txt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def extract_text(path):
    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(path)
    elif ext == ".docx":
        return extract_text_from_docx(path)
    elif ext == ".txt":
        return extract_text_from_txt(path)
    else:
        return ""

def save_extracted_text(doc, text: str):
    output_path = doc.extracted_text_path()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

    return output_path