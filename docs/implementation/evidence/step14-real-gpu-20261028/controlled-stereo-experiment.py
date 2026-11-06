import json, os, time
from pathlib import Path
from dataclasses import asdict
import numpy as np
import soundfile as sf
import torch
from scripts.benchmark_diarization import read_rttm
from src.agents.diarization import SpeakerTurn, load_community
from src.agents.diarization_metrics import evaluate_turns
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['PYANNOTE_METRICS_ENABLED'] = '0'
root=Path('.local/step14-voxconverse-20261028')
names=('wdvva','lubpm')
audios=[]
reference=[]
roles={}
for ch,name in enumerate(names):
    data,sr=sf.read(root / (name+'.wav'),dtype='float32',always_2d=True)
    assert sr==16000 and data.shape[1]==1
    audios.append(data[:,0])
    for t in read_rttm(root / (name+'.rttm'),name):
        sid=f'ch{ch}:{t.speaker_id}'
        reference.append(SpeakerTurn(t.start,t.end,sid,ch))
        roles[sid]=('Agent','Customer')[ch]
length=max(map(len,audios))
stereo=np.zeros((length,2),dtype='float32')
for i,a in enumerate(audios): stereo[:len(a),i]=a
path=root/'controlled-stereo.wav'
if path.exists(): raise RuntimeError('Refusing to replace existing fixture')
sf.write(path,stereo,16000,subtype='PCM_16')
model=load_community('/model')
model.pipeline.to(torch.device('cuda'))
start=time.perf_counter()
turns=model.channel_turns(str(path))
torch.cuda.synchronize()
elapsed=time.perf_counter()-start
pred_roles={t.speaker_id:('Agent','Customer')[t.channel] for t in turns}
metrics=evaluate_turns(reference,turns,duration=length/16000,reference_roles=roles,hypothesis_roles=pred_roles)
output={'fixture':'controlled stereo mix of two annotated media recordings; role assignments are experimental channel labels, not actual call-center roles','duration_seconds':length/16000,'reference_speaker_count':len(roles),'latency_seconds':elapsed,'metrics':asdict(metrics),'role_accuracy':metrics.role_accuracy,'role_coverage':metrics.role_coverage}
with (root/'controlled-stereo-result.json').open('x') as out: json.dump(output,out,indent=2,allow_nan=False)
print(json.dumps(output,indent=2))
