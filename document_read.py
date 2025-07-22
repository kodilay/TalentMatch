
from typing import Union
import PyPDF2
from docx import Document
import io

def extract_text_from_pdf_file(file_bytes: bytes) -> str:
    """
    Extracts text from a PDF file given in bytes.
    """
    try:
        memory_pdf = io.BytesIO(file_bytes)
        reader = PyPDF2.PdfReader(memory_pdf)
        full_text = ""

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"

        return full_text
    except Exception as error:
        raise Exception(f"An error occurred while reading the PDF: {str(error)}")

def extract_text_from_docx_file(file_bytes: bytes) -> str:
    """
    Extracts text from a DOCX file given in bytes.
    """
    try:
        docx_stream = io.BytesIO(file_bytes)
        document = Document(docx_stream)
        content = ""

        for paragraph in document.paragraphs:
            content += paragraph.text + "\n"

        return content
    except Exception as error:
        raise Exception(f"An error occurred while reading the DOCX file: {str(error)}")

def handle_document(file_bytes: bytes, extension: str) -> str:
    """
    Determines file type by extension and extracts text accordingly.
    Supports only PDF and DOCX formats.
    """
    extension = extension.lower()
    if extension == ".pdf":
        return extract_text_from_pdf_file(file_bytes)
    elif extension == ".docx":
        return extract_text_from_docx_file(file_bytes)
    else:
        raise ValueError("Unsupported file type. Only PDF and DOCX formats are allowed.")
