---
language: en
datasets:
- superb
tags:
- speech
- audio
- wav2vec2
- audio-classification
license: apache-2.0
widget:
- example_title: IEMOCAP clip "happy"
  src: https://cdn-media.huggingface.co/speech_samples/IEMOCAP_Ses01F_impro03_F013.wav
- example_title: IEMOCAP clip "neutral"
  src: https://cdn-media.huggingface.co/speech_samples/IEMOCAP_Ses01F_impro04_F000.wav
---

# Wav2Vec2-Base for Emotion Recognition

## Model description

This is a ported version of 
[S3PRL's Wav2Vec2 for the SUPERB Emotion Recognition task](https://github.com/s3prl/s3prl/tree/master/s3prl/downstream/emotion).

The base model is [wav2vec2-base](https://huggingface.co/facebook/wav2vec2-base), which is pretrained on 16kHz 
sampled speech audio. When using the model make sure that your speech input is also sampled at 16Khz. 

For more information refer to [SUPERB: Speech processing Universal PERformance Benchmark](https://arxiv.org/abs/2105.01051)

## Task and dataset description

Emotion Recognition (ER) predicts an emotion class for each utterance. The most widely used ER dataset
[IEMOCAP](https://sail.usc.edu/iemocap/) is adopted, and we follow the conventional evaluation protocol: 
we drop the unbalanced emotion classes to leave the final four classes with a similar amount of data points and 
cross-validate on five folds of the standard splits.

For the original model's training and evaluation instructions refer to the 
[S3PRL downstream task README](https://github.com/s3prl/s3prl/tree/master/s3prl/downstream#er-emotion-recognition).


## Usage examples

You can use the model via the Audio Classification pipeline:
```python
from datasets import load_dataset
from transformers import pipeline

dataset = load_dataset("anton-l/superb_demo", "er", split="session1")

classifier = pipeline("audio-classification", model="superb/wav2vec2-base-superb-er")
labels = classifier(dataset[0]["file"], top_k=5)
```

Or use the model directly:
```python
import torch
import librosa
from datasets import load_dataset
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor

def map_to_array(example):
    speech, _ = librosa.load(example["file"], sr=16000, mono=True)
    example["speech"] = speech
    return example

# load a demo dataset and read audio files
dataset = load_dataset("anton-l/superb_demo", "er", split="session1")
dataset = dataset.map(map_to_array)

model = Wav2Vec2ForSequenceClassification.from_pretrained("superb/wav2vec2-base-superb-er")
feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained("superb/wav2vec2-base-superb-er")

# compute attention masks and normalize the waveform if needed
inputs = feature_extractor(dataset[:4]["speech"], sampling_rate=16000, padding=True, return_tensors="pt")

logits = model(**inputs).logits
predicted_ids = torch.argmax(logits, dim=-1)
labels = [model.config.id2label[_id] for _id in predicted_ids.tolist()]
```

## Eval results

The evaluation metric is accuracy.

|        | **s3prl** | **transformers** |
|--------|-----------|------------------|
|**session1**| `0.6343`  | `0.6258`         |

### BibTeX entry and citation info

```bibtex
@article{yang2021superb,
  title={SUPERB: Speech processing Universal PERformance Benchmark},
  author={Yang, Shu-wen and Chi, Po-Han and Chuang, Yung-Sung and Lai, Cheng-I Jeff and Lakhotia, Kushal and Lin, Yist Y and Liu, Andy T and Shi, Jiatong and Chang, Xuankai and Lin, Guan-Ting and others},
  journal={arXiv preprint arXiv:2105.01051},
  year={2021}
}
```