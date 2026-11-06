import json, os, time
from pathlib import Path
from dataclasses import asdict
import numpy as np
import soundfile as sf
import torch
from scripts.benchmark_diarization import read_rttm
from src.agents.diarization import SpeakerTurn, load_community
from src.agents.diarization_metrics import evaluate_turns
os.environ['HF_HUB_OFFLINE']='1'
os.environ['PYANNOTE_METRICS_ENABLED']='0'
root=Path('.local/step14-voxconverse-20261028')
model=load_community('/model')
model.pipeline.to(torch.device('cuda'))
outputs=[]
for name in ('wdvva','lubpm'):
    source,sr=sf.read(root/(name+'.wav'),dtype='float32',always_2d=True)
    assert sr==16000 and source.shape[1]==1
    orig=read_rttm(root/(name+'.rttm'),name)
    speakers=sorted({t.speaker_id for t in orig})
    boundaries=sorted({0.0,len(source)/sr}|{x for t in orig for x in (t.start,t.end)})
    stereo=np.zeros((len(source),2),dtype='float32')
    reference=[]
    roles={}
    for channel,speaker in enumerate(speakers):
        sid=f'ch{channel}:{speaker}'
        roles[sid]=('Agent','Customer')[channel]
    for a,b in zip(boundaries,boundaries[1:]):
        active={t.speaker_id for t in orig if t.start <= (a+b)/2 < t.end}
        if len(active)!=1: continue
        speaker=next(iter(active)); ch=speakers.index(speaker)
        start=max(0,round(a*sr)); end=min(len(source),round(b*sr))
        stereo[start:end,ch]=source[start:end,0]
        reference.append(SpeakerTurn(a,b,f'ch{ch}:{speaker}',ch))
    target=root/(name+'-two-speaker-role-fixture.wav')
    if target.exists(): raise RuntimeError('Refusing to overwrite existing fixture')
    sf.write(target,stereo,sr,subtype='PCM_16')
    start=time.perf_counter(); turns=model.channel_turns(str(target)); torch.cuda.synchronize()
    elapsed=time.perf_counter()-start
    prediction_roles={t.speaker_id:('Agent','Customer')[t.channel] for t in turns}
    m=evaluate_turns(reference,turns,duration=len(source)/sr,reference_roles=roles,hypothesis_roles=prediction_roles)
    outputs.append({'source':name,'duration_seconds':len(source)/sr,'reference_speakers':len(speakers),'latency_seconds':elapsed,'metrics':asdict(m),'role_accuracy':m.role_accuracy,'role_coverage':m.role_coverage})
result={'description':'Controlled stereo fixtures derived from annotated two-speaker media; roles are assigned by construction, overlap removed; not real call-center roles','records':outputs}
with (root/'two-speaker-role-result.json').open('x',encoding='utf8') as f: json.dump(result,f,indent=2,allow_nan=False)
print(json.dumps(result,indent=2))
