import json,os,time
from pathlib import Path
import soundfile as sf
from src.agents.transcription import run_transcription
from tests.conftest import make_intake_result
root=Path('.local/step15-benchmark')
x,sr=sf.read('.local/step14-voxconverse-20261028/wdvva.wav',dtype='float32')
path=root/'asr-eight-second.wav'; sf.write(path,x[:sr*8],sr)
intake=make_intake_result();intake.audio_path=str(path)
model=str(Path.home()/'.cache/huggingface/hub/models--Systran--faster-whisper-tiny/snapshots/d90ca5fe260221311c53c58e660288d3deb8d356')
os.environ['HF_HUB_OFFLINE']='1';os.environ['WHISPER_DEVICE']='cpu';os.environ['DIARIZATION_BACKEND']='heuristic'
import src.agents.transcription as tr
tr._get_whisper_model(model)
results=[]
for mode in ('false','true'):
 os.environ['AUDIO_PREPROCESS_SEGMENTS']=mode
 t=time.perf_counter(); result=run_transcription(intake,model_size=model);elapsed=time.perf_counter()-t
 results.append({'segmented':mode=='true','seconds':elapsed,'rtf':elapsed/8,'segment_count':len(result.segments),'valid_timestamps':all(0<=s.start_time<=s.end_time<=8 for s in result.segments)})
output={'audio_seconds':8,'device':'cpu','model':'faster-whisper-tiny','model_revision':'d90ca5fe260221311c53c58e660288d3deb8d356','model_loading_excluded':True,'results':results}
(root/'asr-result.json').write_text(json.dumps(output,indent=2));print(json.dumps(output,indent=2))
