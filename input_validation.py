import os,io
import tkinter as tk
import cv2
from tkinter import filedialog
from pathlib import Path
from PIL import Image,ImageFile,ImageOps

#Constants
MAX_IMG_HEIGHT=4096
MAX_IMG_WIDTH=4096
MAX_IMG_PIXELS=MAX_IMG_WIDTH*MAX_IMG_HEIGHT
MAX_FILE_SIZE=10*1024*1024
MAX_CHUNK_SIZE=8192
ALLOWED_MIME_TYPES={"images/jpeg","images/png","images/webp","images/bmp"}
ALLOWED_IMG_TYPES={
    b"\xff\xd8\xff":"images/jpeg",
    b"\x89PNG\r\n\x1a\n":"images/png",
    b"BM":"images/bmp"}

Image.MAX_IMAGE_PIXELS=MAX_IMG_PIXELS
ImageFile.LOAD_TRUNCATED_IMAGES=False
def validate_header(chunk: bytes) -> bool:
    chunk_lower = chunk[:128].lower()
    if b"<?xml" in chunk_lower or b"<svg" in chunk_lower or b"<! doctype svg" in chunk_lower:
        return False
    if any(chunk.startswith(signature) for signature in ALLOWED_IMG_TYPES):
        return True
    if len(chunk) >= 12 and chunk.startswith(b"RIFF") and chunk[8:12] == b"WEBP":
        return True
    return False

# Defining buffer for reading chunks, and checking them for anomalies
def process_chunk(filepath: str):
    total_bytes = 0
    buffer = io.BytesIO()
    is_validated = False
    with open(filepath, "rb") as stream:
        while True:
            chunk = stream.read(MAX_CHUNK_SIZE)
            if not chunk and total_bytes == 0: raise ValueError("File is empty")
            if not chunk:
                break
            if not is_validated:
                if not validate_header(chunk):
                    raise ValueError("File is invalid, it doesn't correspond to valid image format")
                is_validated = True
            total_bytes += len(chunk)
            if total_bytes > MAX_FILE_SIZE:
                buffer.close()
                raise ValueError("File rejected, it exceeded max limit")
            buffer.write(chunk)
    buffer.seek(0)
    return buffer

# Get image properties
def process_image_info(buffer):
    try:
        with Image.open(buffer) as img:
            image_format = img.format
            img.verify()
            width,height=img.size
            if width>MAX_IMG_WIDTH or height>MAX_IMG_HEIGHT or (width*height)>MAX_IMG_PIXELS:
                raise ValueError(f"Image dimensions are too large. They exceed safe limits: {width}x{height}")
            
        buffer.seek(0)
        with Image.open(buffer) as img_decode:
            img_decode.load()
            img_decode=ImageOps.exif_transpose(img_decode)
            clean_buffer=io.BytesIO()
            save_format="PNG" if image_format=="PNG" else "JPEG"
            if save_format=="JPEG" and img_decode.mode in ("RGBA","P"):
                img_decode=img_decode.convert("RGB")
            img_decode.save(clean_buffer,format=save_format)
            clean_buffer.seek(0)
            img_info = {
                "size_bytes": clean_buffer.getbuffer().nbytes,
                "format": save_format,
                "dimensions": img_decode.size,
                "mode": img_decode.mode,
                "buffer":clean_buffer}
            return img_info
    except Exception as e:
        raise ValueError(f"Image format invalid or corrupted file: {e}")

# Get image from your OS
def pickImage():
    root = tk.Tk()
    root.withdraw()
    downloads_path = Path.home() / "Downloads"
    file_path = filedialog.askopenfilename(
        initialdir=downloads_path,
        title="Select File",
        filetypes=[("Image Files", "*.jpg *.jpeg *.png *.webp *.bmp"), ("All Files", "*.*")])
    if not file_path:
        print("File selection error")
        return None
    if os.path.getsize(file_path)>MAX_FILE_SIZE:
        raise ValueError("File is larger than 10MB")
    print("Selected file: ",file_path)
    buffer=process_chunk(file_path)
    img_info=process_image_info(buffer)
    print("Success")
    secure_img=Image.open(img_info["buffer"])
    return secure_img    