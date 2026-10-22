import cv2
import numpy as np
import pytesseract

#Define the threshold
def binarize(gray):
    binary=cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,
                                 blockSize=11,C=2)
    return binary

#Perform morphology
def clean_morpho(binary):
    kernel=cv2.getStructuringElement(cv2.MORPH_RECT,(2,2))
    cleaned=cv2.morphologyEx(binary,cv2.MORPH_OPEN,kernel)
    cleaned=cv2.morphologyEx(cleaned,cv2.MORPH_CLOSE,kernel)
    return cleaned

#Get the contours and define the bounding box
def extract_bounding_boxes(cleaned):
    contours,_=cv2.findContours(cleaned,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    boxes=[]
    for c in contours:
        x,y,width,height=cv2.boundingRect(c)
        if width>5 and height>5:
            boxes.append((x,y,width,height))
        return boxes

#Perform sorting by height and width
def layout_analysis(boxes):
    if not boxes:
        return []
    sorted_boxes=sorted(boxes,key=lambda b:(b[1]//15,b[0]))
    return sorted_boxes

#Process orchestration(def)
