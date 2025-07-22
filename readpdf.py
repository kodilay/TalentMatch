import pdfplumber

def extract_text_from_pdf(file_path):
    all_text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            all_text += page.extract_text() + "\n"
    return all_text.strip() 