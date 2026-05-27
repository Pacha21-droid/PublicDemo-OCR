import cv2
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

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

def getImage():
 return pickImage()