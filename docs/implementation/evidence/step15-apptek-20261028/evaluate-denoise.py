import os,json,importlib,time
from pathlib import Path
from src.agents import transcription
from src.datasets.asr_benchmark import normalize
from src.utils.audio import extract_audio_properties
from tests.conftest import make_intake_result
root=Path('.local/step15-apptek'); data=json.loads((root/'manifest.json').read_text(encoding='utf8')); ref=next(x for x in data['records'] if x['accent']=='en-US_General'); reference=normalize(' '.join(s['text'] for s in sorted(ref['segments'],key=lambda x:(x['start'],x['end'])))).split();rapid=importlib.import_module('rapidfuzz.distance.Levenshtein')
os.environ['HF_HUB_OFFLINE']='1';os.environ['WHISPER_DEVICE']='cpu';os.environ['DIARIZATION_BACKEND']='heuristic';os.environ['AUDIO_PREPROCESS_SEGMENTS']='false'
model=str(Path.home()/'.cache/huggingface/hub/models--Systran--faster-whisper-tiny/snapshots/d90ca5fe260221311c53c58e660288d3deb8d356');transcription._get_whisper_model(model)
results=[]
for file in ('denoise-clean-pcm.wav','denoise-noisy-pcm.wav','denoise-filtered-pcm.wav'):
 p=root/file;b=p.read_bytes();i=make_intake_result();i.audio_path=str(p);i.audio_properties=extract_audio_properties(b,'wav');t=time.perf_counter();out=transcription.run_transcription(i,model_size=model);hyp=normalize(out.full_text).split();results.append({'condition':file,'word_errors':rapid.distance(reference,hyp),'reference_words':len(reference),'elapsed_seconds':time.perf_counter()-t});print(file,'done',flush=True)
with (root/'denoise-wer.json').open('x',encoding='utf8') as f:json.dump({'dataset':'apptek-com/apptek_callcenter_dialogues','revision':'b98967d9946f7f59f58d08624a2a00fe98fe0219','accent':'en-US_General','noise':'seeded gaussian std=0.02','filter':'FFmpeg afftdn defaults','normalization':'NFC casefold whitespace; punctuation retained','results':results},f,indent=2)

