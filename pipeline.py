from input_validation import pickImage
from preprocessing import preprocess_pipeline
from processing import process_pipeline
from postprocessing import postprocess_pipeline

import cv2

class PipelineBus:
    def __init__(self):
        self.pipes=[]
    def register(self,pipeline_func):
        self.pipes.append(pipeline_func)
        return self
    def run(self,context:dict)->dict:
        for pipe in self.pipes:
            context=pipe(context)
        return context

def create_pipeline():
    pipeline=PipelineBus()
    #Acquisition
    @pipeline.register
    def getImage(ctx):
        print("\n[Acquisition] Getting the image securely")
        pickImage()
        
    #Preprocessing
    @pipeline.register
    def preprocess_stage(ctx):
        print("\n[Pre-Process] Starting quality checks and dynamic routing...")
        img=ctx["img"]
        gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY) if len(img.shape)==3 else img
        preprocess_pipeline(img)
        ctx["processed_img"]=gray
        ctx["color_img"]=img
        return ctx
    
    #Processing
    @pipeline.register
    def process_stage(ctx):
        print("[Process] Binarizing, cleaning morphology, and extracting text...")
        gray = ctx["processed_img"]
        process_pipeline(gray)
        raw,ordered=process_pipeline(gray)
        ctx["raw_text"] = raw
        ctx["bounding_boxes"] = ordered
        return ctx

    #Post processing
    @pipeline.register
    def postprocess_stage(ctx):
        print("[Post-Process] Validating, classifying type, and structuring files...")
        raw_text = ctx["raw_text"]
        image_path = ctx["image_path"]
        output_dir = ctx["output_dir"]
        saved_path, doc_type, payload = postprocess_pipeline(raw_text, image_path, output_dir)
        print(f"[Post-Process] Classified as type: '{doc_type}'. Saved to: {saved_path}")
        ctx["final_payload"] = payload
        ctx["saved_path"] = saved_path
        return ctx
    return pipeline
