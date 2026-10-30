import os
from io import BytesIO
from typing import BinaryIO
import tkinter as tk
import cv2
import numpy as np
from tkinter import filedialog
from pathlib import Path
from PIL import Image,ImageFile,ImageOps,UnidentifiedImageError

#Constants
MAX_IMG_HEIGHT=4096
MAX_IMG_WIDTH=4096
MAX_IMG_PIXELS=MAX_IMG_WIDTH*MAX_IMG_HEIGHT
MAX_FILE_SIZE=10*1024*1024
MAX_CHUNK_SIZE=8192
ALLOWED_MIME_TYPES={"images/jpeg","images/png","images/webp","images/bmp"}
ALLOWED_IMG_TYPES={
    "JPEG": (b"\xff\xd8\xff",),
    "PNG": (b"\x89PNG\r\n\x1a\n",),
    "BMP": (b"BM",),
    "WEBP": (b"RIFF",)}

Image.MAX_IMAGE_PIXELS=MAX_IMG_PIXELS
ImageFile.LOAD_TRUNCATED_IMAGES=False
def validate_header(chunk: bytes) -> bool:
    if not chunk:
        return False
    if chunk.startswith(ALLOWED_IMG_TYPES["JPEG"][0]):
        return True
    if chunk.startswith(ALLOWED_IMG_TYPES["PNG"][0]):
        return True
    if chunk.startswith(ALLOWED_IMG_TYPES["BMP"][0]):
        return True
    if(chunk.startswith(b"RIFF")
        and len(chunk)>=12
        and chunk[8:12]==b"WEBP"):
        return True
    return False

# Defining buffer for reading chunks, and checking them for anomalies
def process_chunk(file_object:BinaryIO,max_size:int=MAX_FILE_SIZE):
    total_bytes = 0
    buffer = BytesIO()
    first_chunk=True
    try:
        while True:
            chunk=file_object.read(MAX_CHUNK_SIZE)
            if not chunk:
                break
            if first_chunk:
                if not validate_header(chunk):
                    raise ValueError("Unsupported or invalid image file.")
                first_chunk=False
            total_bytes+=len(chunk)
            if total_bytes>max_size:
                raise ValueError(f"Image exceeds {max_size // (1024 * 1024)} MB size limit.")
            buffer.write(chunk)
            if total_bytes==0:
                raise ValueError("The file is empty.")
            buffer.seek(0)    
            return buffer
    except Exception():
        buffer.close()
        raise

# Get image properties
def process_image_info(buffer:BytesIO)->dict:
    try:
        buffer.seek(0)
        with Image.open(buffer) as img:
            image_format=(img.format or "").upper()
            if image_format not in ALLOWED_IMG_TYPES:
                raise ValueError("Only JPEG,PNG,BMP and WEBP supported")
            width,height=img.size
            if width<=0 or height<=0:
                raise ValueError(f"Image dimensions are invalid.")
            if(width>MAX_IMG_WIDTH or height>MAX_IMG_HEIGHT or width*height>MAX_IMG_PIXELS):
                raise ValueError(f"Image dimensions are large,they exceed safety limit: {MAX_IMG_PIXELS}.")
            img.verify()  
        buffer.seek(0)
        with Image.open(buffer) as src:
            img_decode=ImageOps.exif_transpose(src).convert("RGB")
            width,height=img_decode.size
            if(width>MAX_IMG_WIDTH or height>MAX_IMG_HEIGHT or width*height>MAX_IMG_PIXELS):
                raise ValueError(f"Oriented image dimensions are large,they exceed safety limit: {MAX_IMG_PIXELS}.")
            normalized=BytesIO()
            img_decode.save(normalized,format="PNG",optimize=True)
            normalized.seek(0)
            return{"buffer":normalized,
                   "format":image_format,"width":width,
                    "height":height,"mode":"RGB"}
    except(UnidentifiedImageError, OSError) as e:
        raise ValueError(f"Image format invalid or corrupted file: {e}") from e
    finally:
        buffer.close()

# Get image from your OS
def pickImage(filepath:str|Path|None=None):
    if filepath is None:
        root = tk.Tk()
        root.withdraw()
        downloads_path = Path.home() / "Downloads"
        file_path = filedialog.askopenfilename(
        initialdir=downloads_path,
        title="Select File",
        filetypes=[("Image Files", "*.jpg *.jpeg *.png *.webp *.bmp"), ("All Files", "*.*")])
        root.destroy()
        if not downloads_path:
         return None
        filepath=downloads_path
        if os.path.getsize(file_path)>MAX_FILE_SIZE:
            raise ValueError("File is larger than 10MB.")
    path=Path(filepath).expanduser()
    if not path.is_file():
        raise FileNotFoundError("Image does not exist.")
    with path.open("rb") as src:
        buffer=process_chunk(src)
    info=process_image_info(buffer)
    try:
        with Image.open(info["buffer"]) as pil_img:
            rgb=np.asarray(pil_img.convert("RGB"))
        img_bgr=cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR)
    finally:
        info["buffer"].close()
    return img_bgr,str(path.resolve())