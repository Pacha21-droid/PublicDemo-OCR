from input_validation import pickImage
from preprocessing import preprocess_pipeline
from processing import process_pipeline
from postprocessing import postprocess_pipeline
from __future__ import annotations
from pathlib import Path
import cv2

class PipelineBus:
    def __init__(self):
        self.pipe=[]
    def register(self,pipeline_func):
        self.pipe.append(pipeline_func)
        return pipeline_func
    def run(self,context):
        if not isinstance(context,dict):
            raise ValueError("Pipeline context must be dictionary.")
        for stage in self.pipe:
            stage_name=getattr(stage,"__name__",repr(stage))
            context=stage(context)
            if not isinstance(context,dict):
                raise TypeError(f"Pipeline stage {stage_name} must return context dictionary")       
        return context

def create_pipeline()->PipelineBus:
    pipeline=PipelineBus()
    #Acquisition
    @pipeline.register
    def getImage(ctx):
        print("\n[Acquisition] Getting the image securely")
        img=pickImage(ctx.get("image_path"))
        if img is None:
            raise RuntimeError("Image selection was cancelled.")
        image,image_path=img
        ctx["img"]=image
        ctx["image_path"]=image_path
        ctx.setdefault("output_dir","output")
        return ctx
        
    #Preprocessing
    @pipeline.register
    def preprocess_stage(ctx):
        print("\n[Pre-Process] Starting quality checks and dynamic routing...")
        if "img" not in ctx:
            raise KeyError("Image is not provided from the previous stage")
        preprocessed=preprocess_pipeline(ctx["img"])
        ctx["preprocessed_img"]=preprocessed
        return ctx
    
    #Processing
    @pipeline.register
    def process_stage(ctx):
        print("[Process] Binarizing, cleaning morphology, and extracting text...")
        if "preprocessed_img" not in ctx:
            raise KeyError("Preprocessed image is not provided from the previous stage")
        raw,ordered=process_pipeline(ctx["preprocessed_img"])
        ctx["raw_text"]=raw
        ctx["layout_boxes"]=ordered
        return ctx

    #Post processing
    @pipeline.register
    def postprocess_stage(ctx):
        print("[Post-Process] Validating, classifying type, and structuring files...")
        if "raw_text" not in ctx:
            raise KeyError("Postprocessing requires raw_text")
        if "image_path" not in ctx:
            raise KeyError("Postprocessing requires image_path")
        saved_path,doc_type,payload=postprocess_pipeline(ctx["raw_text"],Path(ctx["image_path"])
                    ,ctx.get("output_dir","output"))
        ctx["saved_path"]=saved_path
        ctx["doc_type"]=doc_type
        ctx["result"]=payload
        return ctx
    return pipeline

def run_pipeline(image_path=None,output_dir="output"):
    context={"image_path":(str(image_path) if image_path is not None else None),"output_dir":str(output_dir)}
    pipeline=create_pipeline
    return pipeline.run(context)
if __name__=="__main__":
    result=run_pipeline()
    print("\n OCR pipeline completed.")
    print(f"Document type: {result["doc_type"]}")
    print(f"Saved result: {result["saved_path"]}") 
    print(f"Extracted text: {result["raw_text"]}") 