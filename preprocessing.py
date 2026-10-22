import cv2
import numpy as np

img=''
gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

#Detecting blurry image and applying unsharp masking to the blurry ones
def check_blur(gray,thresh=1000.00):
    var=cv2.Laplacian(gray,cv2.CV_64F).var()
    blurry=var<thresh
    return blurry,var

def fix_blur(gray,sigma=1.0,strength=1.5):
    blurred=cv2.GaussianBlur(gray,(0,0),sigma)
    sharpened=cv2.addWeighted(gray,1.0+strength,blurred,-strength,0)
    return sharpened

#Checking overall contrast and fixing uneven lightning combined with noise removal
def analyze_hist(gray,min_dyn_range=50):
    p1,p99=np.percentile(gray,(1,99))
    dyn_range=p99-p1
    needs_contrast=dyn_range<min_dyn_range
    mean_intensity = np.mean(gray)
    total_pixels =(gray).size
    shadows = np.sum(gray < 10) / total_pixels 
    highlights = np.sum(gray > 245) / total_pixels 
    too_dark = mean_intensity < 85 and shadows > 0.25
    too_bright = mean_intensity > 170 and highlights > 0.25
    return needs_contrast,dyn_range,too_bright,too_dark

def fix_contrast(gray,report):
    if report["needs_contrast"]:
        clahe=cv2.createCLAHE(clipLimit=2.0,titleGridSize=(8,8))
        return clahe.apply(gray),True
    if report["too_dark"] or report["too_bright"]:
        normalized=cv2.normalize(gray,None,0,255,norm_type=cv2.NORM_MINMAX)
        return normalized,True
    return gray,False

def fix_noise(gray,d=9,sigma_color=75,sigma_space=75):
    denoised=cv2.bilateralFilter(gray,d,sigma_color,sigma_space)
    return denoised

#Projection profile analysis and deskewing
def check_skew(gray,angle_range=(-15,15),step=0.5):
    height,width=gray.shape
    scale=0.5
    small=cv2.resize(gray,(int(width*scale),int(height*scale)),interpolation=cv2.INTER_AREA)
    _,thresh=cv2.threshold(small,0,255,cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    best_angle=0.0
    max_var=0.0
    angles=np.arange(angle_range[0],angle_range[1]+step,step)
    for angle in angles:
        center=(small.shape[1]//2,small.shape[0]//2)
        m=cv2.getRotationMatrix2D(center=center,angle=angle,scale=1.0)
        rotated=cv2.warpAffine(thresh,m,(small.shape[1],small.shape[0]),flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT)
        projection=np.sum(rotated,axis=1)
        variance=np.var(projection)
        if variance>max_var:
            max_var=variance
            best_angle=angle
    needs_deskew=abs(best_angle)>0.3
    return needs_deskew,best_angle

def fix_skew(img,angle):
    if abs(angle)<=0.3:
        return img
    height,width=img.shape[:2]
    center=(width//2,height//2)
    m=cv2.getRotationMatrix2D(center=center,angle=angle,scale=1.0)
    deskewed=cv2.warpAffine(img, m, (width, height), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return deskewed

#For overall test
def evaluate_img(gray):
    blurry,blur_val=check_blur(gray)
    needs_contrast,contrast_val,bright,dark=analyze_hist(gray)
    needs_skew,skew_angle=check_skew(gray)
    flags={"FixBlur":blurry,"Enhance":needs_contrast,"Deskew":needs_skew}
    scores={"Blur":blur_val,"Contrast":contrast_val,"Angle":skew_angle,"Bright":bright,"Dark":dark}
    return flags,scores