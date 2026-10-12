import os,io
import tkinter as tk
import cv2
from tkinter import filedialog
from pathlib import Path
from PIL import Image,ImageFile

MAX_IMG_HEIGHT=4096
MAX_IMG_WIDTH=4096
MAX_IMG_PIXELS=16000000
MAX_FILE_SIZE=10*1024*1024
MAX_CHUNK_SIZE=8192
ALLOWED_MIME_TYPES={"images/jpeg","images/png","images/webp","images/bmp"}
ALLOWED_IMG_TYPES={
    b"\xff\xd8\xff":"images/jpeg",
    b"\x89PNG\r\n\x1a\n":"images/png",
    b"BM":"images/bmp"}

Image.MAX_IMAGE_PIXELS=MAX_IMG_PIXELS
ImageFile.LOAD_TRUNCATED_IMAGES=False

def validate_header(chunk:bytes)->bool:
    chunk_lower=chunk[:128].lower()
    if(b"<?xml" in chunk_lower or b"<svg" in chunk_lower or b"<! doctype svg" in chunk_lower):
        return False
    if any(chunk.startswith(signature) for signature in ALLOWED_IMG_TYPES):
        return True
    if len(chunk)>=12 and chunk.startswith(b"RIFF") and chunk[8:12]==b"WEBP":
        return True
    return False

def process_input(filepath:str):
    if os.path.getsize(filepath)>MAX_FILE_SIZE:
        raise ValueError("File is larger than 10MB")

total_bytes=0
buffer=io.BytesIO()
filepath=""

with open (filepath,"rb") as stream:
    first_chunk=stream.read(MAX_CHUNK_SIZE)
    if not first_chunk:
        raise ValueError("File is empty")
    if not validate_header(first_chunk):
        raise ValueError("File is invalid,it doesn't correspond to valid image format")
    total_bytes+=len(first_chunk)
    buffer.write(first_chunk)
    while True:
        chunk=stream.read(MAX_CHUNK_SIZE)
        if not chunk:
            break
        total_bytes+=len(chunk)
        if total_bytes>MAX_FILE_SIZE:
            buffer.close()
            raise ValueError("File rejected,it exceeded max limit")
        buffer.write(chunk)
buffer.seek(0)

#Get image from your OS
def pickImage():
    root=tk.Tk()
    root.withdraw()
    downloads_path=Path.home()/"Downloads"
    file_path=filedialog.askopenfilename(
    initialdir=downloads_path,
    title="Select File",
    filetypes=[("Image Files","*.jpg *.jpeg *.png *.webp *.bmp"),("All Files","*.*")])
    if file_path:
        print("Selected file:", file_path)
        img = cv2.imread(file_path)
        print("Success")
        return img
    print("Error getting the image!")
    return None

try:
 with Image.open(buffer) as img:
    image_format=img.format
    img.verify()
    buffer.seek(0)
 with Image.open(buffer) as img_decode:
    img_decode.load()
    #ImageOps.exif_transpose(img_decode)
 img_info={
     "size_bytes": total_bytes,
     "format":image_format,
     "dimensions": img_decode.size,
     "mode": img_decode.mode,}
except Exception as e:
    raise ValueError(f"Image format invalid or corrupted file: {e}")