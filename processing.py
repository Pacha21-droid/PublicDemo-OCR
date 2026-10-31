import cv2
import numpy as np
import pytesseract
from preprocessing import to_gray
from __future__ import annotations

#Define the threshold
def binarize(gray:np.ndarray)->np.ndarray:
    gray=to_gray(gray)
    min_dimension=min(gray.shape[:2])
    if min_dimension<3:
        _,binary=cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)                             
        return binary
    block_size=min(31,min_dimension if min_dimension%2==1 else min_dimension-1)
    block_size=max(3,block_size)
    return cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,block_size,10)

#Perform morphology
def clean_morpho(binary:np.ndarray)->np.ndarray:
    if binary is None or binary.ndim!=2:
        raise ValueError("clean_morpho expects 2D binary image.")
    foreground=cv2.bitwise_not(binary)
    kernel=cv2.getStructuringElement(cv2.MORPH_RECT,(2,2))
    opened=cv2.morphologyEx(foreground,cv2.MORPH_OPEN,kernel)
    closed=cv2.morphologyEx(opened,cv2.MORPH_CLOSE,kernel)
    return cv2.bitwise_not(closed)

#Get the contours and define the bounding box
def extract_bounding_boxes(cleaned:np.ndarray)->list[tuple[int,int,int,int]]:
    if cleaned is None or cleaned.ndim!=2:
        raise ValueError("extract_bounding_boxes expects 2D image.")
    foreground=cv2.bitwise_not(cleaned)
    contours,_=cv2.findContours(foreground,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    boxes=[]
    for c in contours:
        x,y,width,height=cv2.boundingRect(c)
        if width>=3 and height>=3:
            boxes.append((int(x),int(y),int(width),int(height)))
    return boxes

#Perform sorting by height and width
def layout_analysis(boxes:list[tuple[int,int,int,int]])->list[tuple[int,int,int,int]]:
    if not boxes:
        return []
    boxes=sorted(boxes,key=lambda box:(box[1]+box[3]/2,box[0]))
    median_height=float(np.median([box[3] for box in boxes]))
    tolerance=max(5.0,median_height*0.55)
    lines=[]
    for box in boxes:
        x,y,width,height=box
        center_y=y+height/2
        best_line=None
        best_distance=None
        for line in lines:
            distance=abs(center_y-line["center"])
            if (distance<=tolerance and(best_distance is None or distance<best_distance)):
                best_line=line
                best_distance=best_distance
        if best_line is None:
            lines.append({"center":center_y,"boxes":[box]})
        else:
            best_line["boxes"].append(box)
            best_line["center"]=float(np.mean([b[1]+b[3]/2 for b in best_line["boxes"]]))
        lines.sort(key=lambda line:line["center"])
        ordered=[]
        for line in lines:
            ordered.extend(sorted(line["boxes"],key=lambda box:box[0]))
        return ordered

#Process orchestration(def)
def process_pipeline(preprocessed_img:np.ndarray,config:str="--oem 3 --psm 6"):
    gray=to_gray(preprocessed_img)
    binary=binarize(gray)
    clean=clean_morpho(binary)
    boxes=extract_bounding_boxes(clean)
    sorted=layout_analysis(boxes)
    raw=pytesseract.image_to_string(clean,config=config)
    return raw,sorted