import fitz  # PyMuPDF
import piexif
from PIL import Image

def get_gps_from_exif(exif_dict):
    """Extracts GPS info from EXIF dictionary."""
    gps_info = {}
    if "GPS" in exif_dict:
        for tag, value in exif_dict["GPS"].items():
            tag_name = piexif.GPSIFD.TAGS.get(tag, {}).get("name", tag)
            gps_info[tag_name] = str(value)
    return gps_info if gps_info else None

def extract_rich_metadata(file_path):
    """
    Extracts rich metadata from an image or PDF file.
    This function runs locally before calling the AI.
    """
    metadata = {
        "file_path": file_path,
        "metadata": {},
        "annotations": [],
        "error": None
    }
    
    try:
        if file_path.lower().endswith(('.jpg', '.jpeg', '.tiff', '.png')):
            # --- Image Metadata Extraction ---
            img = Image.open(file_path)
            metadata["metadata"]["format"] = img.format
            metadata["metadata"]["mode"] = img.mode
            metadata["metadata"]["size"] = f"{img.width}x{img.height}"

            if "exif" in img.info:
                exif_dict = piexif.load(img.info["exif"])
                general_exif = {}
                for ifd in ("0th", "Exif", "1st"):
                    if ifd in exif_dict:
                        for tag, value in exif_dict[ifd].items():
                            tag_name = piexif.TAGS.get(ifd, {}).get(tag, {}).get("name", tag)
                            # Truncate long byte strings for readability
                            if isinstance(value, bytes) and len(value) > 50:
                                general_exif[tag_name] = str(value[:50]) + "..."
                            else:
                                general_exif[tag_name] = str(value)
                
                metadata["metadata"]["exif"] = general_exif
                gps_data = get_gps_from_exif(exif_dict)
                if gps_data:
                    metadata["metadata"]["gps"] = gps_data

        elif file_path.lower().endswith('.pdf'):
            # --- PDF Metadata and Annotation Extraction ---
            doc = fitz.open(file_path)
            metadata["metadata"] = doc.metadata
            
            for page_num, page in enumerate(doc):
                annots = page.annots()
                if annots:
                    for annot in annots:
                        metadata["annotations"].append({
                            "page": page_num + 1,
                            "type": annot.type[1],
                            "info": annot.info
                        })
            doc.close()

    except Exception as e:
        metadata["error"] = f"Failed to extract metadata: {str(e)}"

    return metadata