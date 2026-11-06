import hashlib,importlib,json,os,time
from pathlib import Path
from src.agents import transcription
from src.datasets.asr_benchmark import normalize
from src.utils.audio_preprocessing import decode_resample,speech_chunks
from src.utils.audio import extract_audio_properties
from tests.conftest import make_intake_result
root=Path('.local/step15-apptek');raw=(root/'manifest.json').read_bytes();m=json.loads(raw)
assert m['repo']=='apptek-com/apptek_callcenter_dialogues' and m['revision']=='b98967d9946f7f59f58d08624a2a00fe98fe0219' and m['license']=='CC-BY-SA-4.0'
rapid=importlib.import_module('rapidfuzz.distance.Levenshtein')
os.environ['HF_HUB_OFFLINE']='1';os.environ['WHISPER_DEVICE']='cpu';os.environ['DIARIZATION_BACKEND']='heuristic'
model=str(Path.home()/'.cache/huggingface/hub/models--Systran--faster-whisper-tiny/snapshots/d90ca5fe260221311c53c58e660288d3deb8d356');transcription._get_whisper_model(model)
results=[]
for r in m['records']:
 p=root/(r['accent']+'.wav'); data=p.read_bytes();assert hashlib.sha256(data).hexdigest()==r['sha256']
 refs=r['segments'];audio=decode_resample(data,str(p));chunks=speech_chunks(audio)
 bounds=sorted({0.0,audio.samples.shape[1]/16000}|{float(x) for seg in refs for x in (seg['start'],seg['end'])}|{x for c in chunks for x in (c.start_seconds,c.end_seconds)})
 reference=missed=0.0
 for a,b in zip(bounds,bounds[1:]):
  mid=(a+b)/2
  if any(seg['start']<=mid<seg['end'] for seg in refs):
   reference+=b-a
   if not any(c.start_seconds<=mid<c.end_seconds for c in chunks):missed+=b-a
 props=extract_audio_properties(data,'wav');i=make_intake_result();i.audio_path=str(p);i.audio_properties=props
 ref=normalize(' '.join(s['text'] for s in sorted(refs,key=lambda x:(x['start'],x['end'])))).split()
 for mode in ('false','true'):
  os.environ['AUDIO_PREPROCESS_SEGMENTS']=mode;start=time.perf_counter();out=transcription.run_transcription(i,model_size=model);elapsed=time.perf_counter()-start
  pred=normalize(out.full_text).split()
  results.append({'accent':r['accent'],'mode':'segmented' if mode=='true' else 'baseline','duration_seconds':props.duration_seconds,'seconds':elapsed,'word_errors':rapid.distance(ref,pred),'reference_words':len(ref),'reference_speech_seconds':reference,'vad_missed_seconds':missed})
  print(r['accent'],mode,'done',flush=True)
result={'dataset':m['repo'],'revision':m['revision'],'license':m['license'],'roleplay':True,'manifest_sha256':hashlib.sha256(raw).hexdigest(),'model':'faster-whisper-tiny','device':'cpu-int8','normalization':'NFC casefold whitespace; punctuation retained','model_load_excluded':True,'results':results}
with (root/'evaluation.json').open('x',encoding='utf8') as f:json.dump(result,f,indent=2)
