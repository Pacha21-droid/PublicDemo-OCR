from image_input import getImage
import preprocess

#Example usage-making font thicker(enhancing text detail with adding more black)
def main():
   img=getImage()
   bw=preprocess.binarize(img)
   no_noise=preprocess.removeNoise(bw)
   thickImg=preprocess.thickFont(no_noise)
   preprocess.displayImage(thickImg)
   print("Main script is runned")

if __name__ == "__main__":
    main()