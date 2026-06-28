"""
OCR fallback for scanned PDF pages using pytesseract + PIL.
Only called when a page has insufficient extractable text.
"""
import fitz
import pytesseract
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

def ocr_page(fitz_page) -> str:
    """
    Render a PyMuPDF page to image and run tesseract OCR on it.
    Returns extracted text string.
    """
    try:
        # Render at 2x scale for better OCR accuracy (300 DPI equivalent)
        mat = fitz.Matrix(2.0, 2.0)
        pix = fitz_page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        
        image = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(image, lang="eng")
        
        logger.info(f"OCR extracted {len(text)} chars")
        return text.strip()
    except Exception as e:
        logger.warning(f"OCR failed: {e}")
        return ""
