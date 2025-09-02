# from .worker import app
from mockvox.engine.v4.inference import Inferencer
from mockvox.utils import i18n
import soundfile as sf
import torch
import gc
import os
import time
from pathlib import Path
from mockvox.config import OUT_PUT_PATH
from .worker import celeryApp
from mockvox.worker.notify import notify_task


@celeryApp.task(name="inference", bind=True)
def inference_task(self,gpt_model_path:str , 
                   soVITS_model_path:str, 
                   ref_audio_path:str , 
                   ref_text:str , 
                   ref_language:str, 
                   target_text:str , 
                   target_language:str,  
                   top_p:float, 
                   top_k:int, 
                   temperature:float, 
                   speed:float,
                   version: str
):
    
    inference = Inferencer(gpt_model_path,soVITS_model_path,version)
    # Synthesize audio
    synthesis_result = inference.inference(ref_wav_path=ref_audio_path,# 参考音频 
                                prompt_text=ref_text, # 参考文本
                                prompt_language=i18n(ref_language), 
                                text=target_text, # 目标文本
                                text_language=i18n(target_language), top_p=top_p, temperature=temperature, top_k=top_k, speed=speed)
    if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            torch.cuda.ipc_collect()
            gc.collect()  
    result_list = list(synthesis_result)
    outputname = os.path.join(Path(OUT_PUT_PATH), self.request.id+".WAV")
    data = {
        "status": "fail",
        "results": {},
        "type": self.request.task,
        "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    }
    if result_list:
        last_sampling_rate, last_audio_data = result_list[-1]
        sf.write( outputname,  last_audio_data, int(last_sampling_rate))
        data = {
            "status": "success",
            "results": {},
            "type": self.request.task,
            "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        }
    # 推理暂不发送回调通知
    #notify_task.delay(self.request.id, data)
    return data