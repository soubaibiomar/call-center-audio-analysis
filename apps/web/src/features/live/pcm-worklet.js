/* global AudioWorkletProcessor, registerProcessor */
// One second of mono 16 kHz PCM16LE per transferable frame; no audio persistence.
class PCMProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.frame = new ArrayBuffer(32000);
        this.view = new DataView(this.frame);
        this.position = 0;
    }
    process(inputs) {
        const samples = inputs[0]?.[0];
        if (!samples) return true;
        for (const value of samples) {
            const clipped = Math.max(-1, Math.min(1, value));
            this.view.setInt16(
                this.position * 2,
                Math.round(clipped * (clipped < 0 ? 32768 : 32767)),
                true,
            );
            this.position += 1;
            if (this.position === 16000) {
                this.port.postMessage(this.frame, [this.frame]);
                this.frame = new ArrayBuffer(32000);
                this.view = new DataView(this.frame);
                this.position = 0;
            }
        }
        return true;
    }
}
registerProcessor("project28-pcm", PCMProcessor);
