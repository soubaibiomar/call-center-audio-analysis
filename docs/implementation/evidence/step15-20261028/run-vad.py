import json,time
from pathlib import Path
import numpy as np
import soundfile as sf
from scripts.benchmark_diarization import read_rttm
from src.utils.audio_preprocessing import decode_resample,speech_chunks
root=Path('.local/step15-benchmark')
source=Path('.local/step14-voxconverse-20261028')
t=time.perf_counter()
audio=decode_resample((source/'wdvva.wav').read_bytes(),'wdvva.wav')
decode_sec=time.perf_counter()-t
t=time.perf_counter();chunks=speech_chunks(audio);vad_sec=time.perf_counter()-t
ref=read_rttm(source/'wdvva.rttm','wdvva')
bounds=sorted({0.0,audio.samples.shape[1]/16000}|{x for a in ref for x in (a.start,a.end)}|{x for c in chunks for x in (c.start_seconds,c.end_seconds)})
ref_sec=missed=0.0
for a,b in zip(bounds,bounds[1:]):
 mid=(a+b)/2
 if any(r.start<=mid<r.end for r in ref):
  ref_sec+=b-a
  if not any(c.start_seconds<=mid<c.end_seconds for c in chunks):missed+=b-a
result={'source':'VoxConverse wdvva, source rights caveat in STEP14','seconds':audio.samples.shape[1]/16000,'decode_seconds':decode_sec,'vad_seconds':vad_sec,'decode_vad_rtf':(decode_sec+vad_sec)/(audio.samples.shape[1]/16000),'speech_reference_seconds':ref_sec,'vad_missed_seconds':missed,'vad_missed_fraction':missed/ref_sec,'chunk_count':len(chunks)}
(root/'vad-result.json').write_text(json.dumps(result,indent=2))
# A known clean reference enables a controlled noise/distortion comparison.
clean=audio.samples[0,:16000*15]
rng=np.random.default_rng(15)
noise=rng.normal(0,0.02,len(clean)).astype('float32')
sf.write(root/'clean.wav',clean,16000,subtype='FLOAT')
sf.write(root/'noisy.wav',clean+noise,16000,subtype='FLOAT')
print(json.dumps(result,indent=2))
