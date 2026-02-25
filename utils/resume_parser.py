import fitz  # PyMuPDF
import docx2txt
import os
import re


def clean_text(text: str) -> str:
    """
    Normalize resume text for ATS + LLM.
    """
    if not text:
        return ""

    # Normalize bullets
    text = re.sub(r"[•●▪■]", "-", text)

    # Remove page numbers like "Page 1 of 2"
    text = re.sub(r"page\s*\d+\s*(of\s*\d+)?", "", text, flags=re.I)

    # Collapse whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)

    return text.strip()


def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from PDF or DOCX safely.
    Always returns a string.
    """
    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    try:
        if ext == ".pdf":
            with fitz.open(file_path) as pdf:
                pages = [p.get_text("text") for p in pdf]
                text = "\n".join(pages)

        elif ext == ".docx":
            text = docx2txt.process(file_path)

        else:
            return ""

    except Exception:
        return ""

    return clean_text(text)