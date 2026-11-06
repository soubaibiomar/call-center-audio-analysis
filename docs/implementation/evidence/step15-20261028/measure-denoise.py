import json
from pathlib import Path
import numpy as np
import soundfile as sf
root=Path('.local/step15-benchmark')
a={}
for name in ('clean','noisy','clean-denoised','noisy-denoised'):
 x,sr=sf.read(root/(name+'.wav'),dtype='float32'); assert sr==16000; a[name]=x
# Estimate filter latency using the clean reference and its processed version.
nfft=1<<(len(a['clean'])+len(a['clean-denoised'])-1).bit_length()
c=np.fft.irfft(np.fft.rfft(a['clean-denoised'],nfft)*np.conj(np.fft.rfft(a['clean'],nfft)),nfft)
idx=int(np.argmax(c[:5000])); delay=idx
n=min(len(a['clean']),len(a['noisy']),len(a['clean-denoised'])-delay,len(a['noisy-denoised'])-delay)
clean=a['clean'][:n]
def mse(x,y): return float(np.mean((x-y)**2))
power=float(np.mean(clean**2))
err_before=mse(clean,a['noisy'][:n]);err_after=mse(clean,a['noisy-denoised'][delay:delay+n]);err_clean=mse(clean,a['clean-denoised'][delay:delay+n])
result={'compared_duration_seconds':n/16000,'sample_rate':16000,'estimated_filter_delay_samples':delay,'input_noise_mse':err_before,'denoised_noise_mse':err_after,'clean_denoised_distortion_mse':err_clean,'snr_before_db':float(10*np.log10(power/err_before)),'snr_after_db':float(10*np.log10(power/err_after)),'filter':'FFmpeg afftdn default; clean-reference estimated delay compensated; 15s media speech plus seeded white noise'}
(root/'denoise-result.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
