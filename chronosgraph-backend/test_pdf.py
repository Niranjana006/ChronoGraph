import fitz
import os
from app.ingestion.parser import chunk_text

UPLOAD_DIR = "/app/uploads"
files = os.listdir(UPLOAD_DIR)
for file in files:
    if file.endswith(".pdf"):
        file_path = os.path.join(UPLOAD_DIR, file)
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text("text") + "\n"
            chunks = chunk_text(text)
        except Exception as e:
            print(f"Error processing {file}: {e}")
