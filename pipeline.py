

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
    
