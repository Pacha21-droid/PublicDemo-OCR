import cv2
import numpy as np
from __future__ import annotations

#Grayscale function
def to_gray(img:np.ndarray)->np.ndarray:
    if img is None or not isinstance(img,np.ndarray):
        raise ValueError("Expected the image as Numpy array")
    if img.ndim==2:
        return img.copy()
    if img.ndim==3 and img.shape[2]==3:
        return cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    if img.ndim==3 and img.shape[2]==4:
        return cv2.cvtColor(img,cv2.COLOR_BGRA2GRAY)
    raise ValueError("Image must be grayscale,bgr or bgra")


#Detecting blurry image and applying unsharp masking to the blurry ones
def check_blur(gray:np.ndarray,thresh:float=1000.00)->bool:
    gray=to_gray(gray)
    var=cv2.Laplacian(gray,cv2.CV_64F).var()
    return var<thresh

def fix_blur(gray:np.ndarray,sigma:float=1.0,strength:float=1.5)->np.ndarray:
    gray=to_gray(gray)
    blurred=cv2.GaussianBlur(gray,(0,0),sigmaX=sigma)
    sharpened=cv2.addWeighted(gray,1.0+strength,blurred,-strength,0)
    return np.clip(sharpened,0,255).astype(np.uint8)

#Checking overall contrast and fixing uneven lightning combined with noise removal
def analyze_hist(gray:np.ndarray,min_dyn_range:int=50):
    gray=to_gray(gray)
    low,high=np.percentile(gray,(2,98))
    dyn_range=float(high-low)
    mean_intensity=float(np.mean(gray))
    shadow_intensity=float(np.mean(gray<40))
    highlights=float(np.mean(gray>220))
    too_bright=(mean_intensity>190 and highlights>0.35)
    too_dark=(mean_intensity>75 and shadow_intensity>0.35)
    needs_contrast=(dyn_range<min_dyn_range or too_bright or too_dark)
    return(needs_contrast,dyn_range,too_dark,too_bright)

def fix_contrast(gray:np.ndarray,report=None)->np.ndarray:
    gray=to_gray(gray)
    if report is None:
        report=analyze_hist(gray)
    if isinstance(report,dict):
        needs_contrast=report.get("needs_contrast",True)
        too_dark=report.get("too_dark",False)
        too_bright=report.get("too_bright",False)
    else:
        report=(needs_contrast,_,too_dark,too_bright)
    if not needs_contrast:
        return gray
    clahe=cv2.createCLAHE(clipLimit=2.0,tileGridSize=(8,8))
    result=clahe.apply(gray)
    if too_bright:
        result=cv2.convertScaleAbs(result,alpha=1.08,beta=-12)
    if too_dark:
        result=cv2.convertScaleAbs(result,alpha=1.12,beta=10)
    return result

def fix_noise(gray:np.ndarray,d:int=9,sigma_color:float=75,sigma_space:float=75)->np.ndarray:
    gray=to_gray(gray)
    return cv2.bilateralFilter(gray,d,sigma_color,sigma_space)

#Projection profile analysis and deskewing
def check_skew(gray:np.ndarray,angle_range:tuple[float,float]=(-15,15),step:float=0.5)->float:
    gray=to_gray(gray)
    if step<=0:
        raise ValueError("Step must be greater than 0.")
    scale=min(1.0,1000.0/max(gray.shape))
    if scale <1.0:
        work=cv2.resize(gray,None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA)
    else:
        work=gray
    _,binary=cv2.threshold(work,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    height,width=binary.shape
    center=(width//2,height//2)
    best_angle=0.0
    best_score=-1.0
    angles=np.arange(angle_range[0],angle_range[1]+step/2,step)
    for angle in angles:
        matrix=cv2.getRotationMatrix2D(center,float(angle),1.0)
        rotated=cv2.warpAffine(binary,matrix,(width,height),flags=cv2.INTER_NEAREST,
                 borderMode=cv2.BORDER_CONSTANT,borderValue=0)
        projection=np.sum(rotated>0,axis=1).astype(np.float64)
        score=float(np.var(projection))
        if score>best_score:
            best_score=score
            best_angle=float(angle)
        return best_angle

def fix_skew(img:np.ndarray,angle:float)->np.ndarray:
    if img is None:
        raise ValueError("Image can't be None.")
    if abs(angle)<=0.3:
        return img.copy()
    height,width=img.shape[:2]
    matrix=cv2.getRotationMatrix2D((width/2,height/2),float(angle),1.0)
    cos_a=abs(matrix[0,0])
    sin_a=abs(matrix[0,1])
    new_width=int(height*sin_a+width*cos_a)
    new_height=int(height*cos_a+width*sin_a)
    matrix[0,2]+=(new_width-width)/2
    matrix[1,2]+=(new_height-height)/2
    return cv2.warpAffine(img,matrix,(new_width,new_height),flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_CONSTANT,borderValue=(255 if img.ndim==2 else(255,255,255)))

#For overall test
def evaluate_img(gray:np.ndarray)->dict:
    gray=to_gray(gray)
    (needs_contrast,dyn_range,too_bright,too_dark)=analyze_hist(gray)
    blur_score=float(cv2.Laplacian(gray,cv2.CV_64F).var())
    skew_angle=check_skew(gray)
    return{"is_blurry":blur_score < 1000.0,
        "blur_score":blur_score,
        "needs_contrast":needs_contrast,
        "dynamic_range":dyn_range,
        "too_bright":too_bright,
        "too_dark":too_dark,
        "skew_angle":skew_angle}

#Preprocess orchestration(def)
def preprocess_pipeline(img:np.ndarray)->np.ndarray:
    gray=to_gray(img)
    if check_blur(gray):
        gray=fix_blur(gray)
    angle=check_skew(gray)
    if abs(angle)>0.3:
        gray=fix_skew(gray,angle)
    report=analyze_hist(gray)
    if report[0]:
        gray=fix_contrast(gray,report)
    gray=fix_noise(gray)
    return gray