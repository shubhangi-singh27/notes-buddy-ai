import os
from pypdf import PdfReader
from docx import Document as DocxDocument

def extract_text_from_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        try:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        except Exception as e:
            continue
    
    return text.strip()

def extract_text_from_docx(path):
    doc = DocxDocument(path)
    paragraphs = [p.text for p in doc.paragraphs]
    return "\n".join(paragraphs).strip()

def extract_text_from_txt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def extract_text(path):
    ext  =os.path.splitext(path)[1].lower()

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