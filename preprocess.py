import cv2
import numpy as np
from pathlib import Path
from matplotlib import pyplot as plt
#Inversion
def invert(input_img):
    inverted_img=cv2.bitwise_not(input_img)
    return inverted_img

#Binarization
def grayscale(input_img):
 return cv2.cvtColor(input_img,cv2.COLOR_BGR2GRAY)

def binarize(input_img):
    grayscaled_img=grayscale(input_img)
    _,bw=cv2.threshold(grayscaled_img,210,230,cv2.THRESH_BINARY)
    return bw

#All the functions down need to receive binarized then noise removed img for better processing
#Only Missing Borders needs to receive no border img(removeBorder after the upper steps)

#Dilation/Erosion factory
def getKernel(r,c):
   kernel=np.ones((r,c),np.uint8)
   return kernel

def dilate(input_img,r,c,i):
   return cv2.dilate(input_img,getKernel(r,c),iterations=i)

def erode(input_img,r,c,i):
   return cv2.erode(input_img,getKernel(r,c),iterations=i)

#Noise cleanup
def removeNoise(input_img):
   morphed_img=cv2.morphologyEx(input_img,cv2.MORPH_CLOSE,getKernel(1,1))
   blurred_img=cv2.medianBlur(morphed_img,3)
   return blurred_img

#Thin/Thick
def thinFont(input_img):
   img=cv2.bitwise_not(input_img)
   img=erode(img,2,2,1)
   img=cv2.bitwise_not(img)
   return img
   
def thickFont(input_img):
   img=cv2.bitwise_not(input_img)
   img=dilate(img,2,2,1)
   img=cv2.bitwise_not(img)
   return img
   
#Borders
def removeBorders(input_img):
   contours,hieararchy=cv2.findContours(input_img,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
   sortedContours=sorted(contours,key=lambda x:cv2.contourArea(x))
   contour=sortedContours[-1]
   x,y,w,h=cv2.boundingRect(contour)
   crop_img=input_img[y:y+h,x:x+w]
   return crop_img

def missingBorders(input_img):
   color=[255,255,255]
   t,b,l,r=[150]*4
   img_with_border=cv2.copyMakeBorder(input_img,t,b,l,r,cv2.BORDER_CONSTANT,value=color)
   return img_with_border
 
#Save result
def saveImage(name,img):
    folder = Path("results")
    folder.mkdir(exist_ok=True)
    path = folder / f"{name}.png"
    saved_img = cv2.imwrite(str(path), img)
    return saved_img

#Display
def displayImage(img):
   dpi = 80
   im_data = img
   height, width  = im_data.shape[:2]
    # Size fit for the figure compared to the image
   figsize = width / float(dpi), height / float(dpi)
    # Create figure for display
   fig = plt.figure(figsize=figsize)
   ax = fig.add_axes([0, 0, 1, 1])
    # Hide spines and ticks
   ax.axis('off')
    # Display the image
   ax.imshow(im_data, cmap='gray')
   plt.show()