# from PIL import Image
# import pytesseract
# import fitz  # PyMuPDF
# import os

# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# def extract_text(file_path):
#     ext = os.path.splitext(file_path)[1].lower()
    
#     if ext == '.pdf':
#         text = extract_text_from_pdf(file_path)
#         if not text.strip():  # If empty, try OCR
#             text = ocr_pdf(file_path)
#         return text
#     elif ext in ['.jpg', '.jpeg', '.png']:
#         return extract_text_from_image(file_path)
#     else:
#         return "Unsupported file type."

# def extract_text_from_pdf(path):
#     text = ""
#     with fitz.open(path) as doc:
#         for page in doc:
#             text += page.get_text()
#     return text

# def ocr_pdf(path):
#     text = ""
#     with fitz.open(path) as doc:
#         for page_num in range(len(doc)):
#             pix = doc[page_num].get_pixmap()
#             img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
#             text += pytesseract.image_to_string(img)
#     return text

# def extract_text_from_image(path):
#     return pytesseract.image_to_string(Image.open(path))

# app/utils/__init__.py

from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import os
import platform
import shutil

# --- Cross-Platform Tesseract Configuration ---
def configure_tesseract():
    """
    Finds the Tesseract executable path based on the operating system
    and sets the pytesseract command.
    """
    system = platform.system()
    tesseract_path = None

    # 1. Best Case: Tesseract is in the system's PATH
    # This is common on Linux and macOS, and for Windows users who check the "Add to PATH" option.
    if shutil.which("tesseract"):
        tesseract_path = shutil.which("tesseract")
        
    # 2. Fallback: Check common default installation locations
    else:
        if system == "Windows":
            # Default path for Tesseract on Windows
            windows_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            if os.path.exists(windows_path):
                tesseract_path = windows_path
        
        elif system == "Darwin":  # macOS
            # Common paths for Homebrew installations on Apple Silicon and Intel Macs
            mac_paths = [
                "/opt/homebrew/bin/tesseract",  # For Apple Silicon (M1/M2/M3)
                "/usr/local/bin/tesseract"      # For Intel Macs
            ]
            for path in mac_paths:
                if os.path.exists(path):
                    tesseract_path = path
                    break

    # 3. Set the command or print a warning if not found
    if tesseract_path:
        print(f"✅ Tesseract executable found at: {tesseract_path}")
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    else:
        print("❌ WARNING: Tesseract executable not found.")
        print("Please do the following:")
        print("1. Install Tesseract-OCR on your system. You can find installers here: https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. Ensure the Tesseract installation directory is in your system's PATH environment variable.")
        print("   (The OCR feature for image and scanned PDF uploads will not work until this is resolved).")

# Run the configuration logic when the module is loaded
configure_tesseract()


# --- Original Functions from the File ---

def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        text = extract_text_from_pdf(file_path)
        if not text.strip():  # If empty, try OCR
            text = ocr_pdf(file_path)
        return text
    elif ext in ['.jpg', '.jpeg', '.png']:
        return extract_text_from_image(file_path)
    else:
        return "Unsupported file type."

def extract_text_from_pdf(path):
    text = ""
    try:
        with fitz.open(path) as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        print(f"Error extracting text from PDF with PyMuPDF: {e}")
    return text

def ocr_pdf(path):
    text = ""
    try:
        with fitz.open(path) as doc:
            for page_num in range(len(doc)):
                pix = doc[page_num].get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text += pytesseract.image_to_string(img)
    except Exception as e:
        print(f"Error performing OCR on PDF: {e}")
    return text

def extract_text_from_image(path):
    try:
        return pytesseract.image_to_string(Image.open(path))
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return ""