import fitz  # PyMuPDF
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts all text from a PDF file using PyMuPDF.
    """
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            page_text = page.get_text("text")
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {e}")
        raise

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """
    A simple recursive character-level chunker.
    Splits text into chunks of roughly `chunk_size` characters, 
    with `overlap` characters between consecutive chunks.
    """
    if not text:
        return []
        
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        
        # If we're not at the end of the text, try to find a nice break point (e.g. newline or period)
        if end < text_length:
            # Look backwards from `end` for a natural break
            # First try paragraph break
            break_point = text.rfind("\n\n", start, end)
            if break_point == -1:
                # Then try sentence break
                break_point = text.rfind(". ", start, end)
            if break_point == -1:
                # Fall back to word break
                break_point = text.rfind(" ", start, end)
                
            if break_point != -1 and break_point > start:
                end = break_point + 1 # Include the break character
                
        chunks.append(text[start:end].strip())
        
        # Move start pointer forward, accounting for overlap
        start = end - overlap
        
        # Prevent infinite loops if overlap >= chunk size or no progress is made
        if start <= chunks[-1].__len__() and len(chunks) > 1 and start == end - overlap:
            start = end
            
    # Filter out empty chunks
    return [c for c in chunks if c]
