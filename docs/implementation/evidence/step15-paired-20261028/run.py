import os,json,time,hashlib,importlib
from datetime import date
from pathlib import Path
from src.agents import transcription
from src.datasets.asr_benchmark import normalize
from src.utils.audio import detect_audio_format,extract_audio_properties
from tests.conftest import make_intake_result
root=Path('data/datasets/unidata-preview-research-20261028').resolve(); raw=(root/'benchmark-inputs.json').read_bytes(); d=json.loads(raw)
assert d['license']=='CC-BY-NC-ND-4.0' and d['purpose']=='non-commercial preliminary evaluation' and date.today()<=date.fromisoformat(d['retention_until'])
for rec in d['records']:
 p=(root/rec['filename']).resolve(strict=True); assert p.is_relative_to(root) and rec['label_review']=='unverified_source_transcript'
 assert hashlib.sha256(p.read_bytes()).hexdigest()==rec['audio_sha256']
 assert hashlib.sha256(rec['reference'].encode()).hexdigest()==rec['reference_sha256']
rapid=importlib.import_module('rapidfuzz.distance.Levenshtein')
os.environ['HF_HUB_OFFLINE']='1';os.environ['WHISPER_DEVICE']='cpu';os.environ['DIARIZATION_BACKEND']='heuristic'
model=str(Path.home()/'.cache/huggingface/hub/models--Systran--faster-whisper-tiny/snapshots/d90ca5fe260221311c53c58e660288d3deb8d356')
transcription._get_whisper_model(model)
results=[]
for rec in d['records']:
 p=(root/rec['filename']).resolve(); data=p.read_bytes(); props=extract_audio_properties(data,detect_audio_format(data)); intake=make_intake_result();intake.audio_path=str(p);intake.audio_properties=props
 for mode in ('false','true'):
  os.environ['AUDIO_PREPROCESS_SEGMENTS']=mode; start=time.perf_counter()
  try:
   output=transcription.run_transcription(intake,model_size=model); elapsed=time.perf_counter()-start
   ref=normalize(rec['reference']).split(); hyp=normalize(output.full_text).split()
   results.append({'sample_id':rec['sample_id'],'mode':'segmented' if mode=='true' else 'baseline','duration_seconds':props.duration_seconds,'elapsed_seconds':elapsed,'word_errors':rapid.distance(ref,hyp),'reference_words':len(ref),'segments':len(output.segments)})
   print(rec['sample_id'],mode,'done',flush=True)
  except Exception as e:
   results.append({'sample_id':rec['sample_id'],'mode':'segmented' if mode=='true' else 'baseline','failed':type(e).__name__});print(rec['sample_id'],mode,'failed',type(e).__name__,flush=True)
output={'purpose':'non-commercial research; unreviewed transcripts; exploratory only','input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'model_revision':'d90ca5fe260221311c53c58e660288d3deb8d356','device':'cpu-int8','model_loading_excluded':True,'results':results}
with (root/'step15-paired-preprocessing-result.json').open('x',encoding='utf8') as f:json.dump(output,f,indent=2)
print('completed',flush=True)
