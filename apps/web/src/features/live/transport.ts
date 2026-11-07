import type {
    AudioReceipt,
    LiveEvent,
    LiveSessionView,
    LiveSignal,
    LiveTicket,
} from "../../lib/api/generated";
import { ApiError, sendResource } from "../../lib/api/client";
import { validateResource } from "../../lib/api/queries";

export type MediaStats = {
    packetsReceived: number;
    packetsLost: number;
    bytesReceived: number;
    localLevel: number | null;
    remoteLevel: number | null;
    concealedSamples: number | null;
    totalSamplesReceived: number | null;
    dtlsState: string | null;
    codec: string | null;
};
export type CallUpdate = {
    session?: LiveSessionView | null;
    connection?: string;
    notice?: string;
    stats?: MediaStats;
    receivedSamples?: number;
    event?: LiveEvent;
};

export function liveError(error: unknown): string {
    if (error instanceof ApiError) {
        if (error.status === 409)
            return "This call changed or is already in use. Refresh the call invitations.";
        if (error.status === 403)
            return "This call or its audio analysis is not authorized.";
        if (error.status === 429)
            return "Audio analysis cannot keep up. Analysis has stopped; the call can continue.";
    }
    return error instanceof Error
        ? error.message
        : "The call could not be connected.";
}

export class BrowserCall {
    private peer: RTCPeerConnection | null = null;
    private socket: WebSocket | null = null;
    private stream: MediaStream | null = null;
    private timer: ReturnType<typeof setInterval> | null = null;
    private disconnectTimer: ReturnType<typeof setTimeout> | null = null;
    private context: AudioContext | null = null;
    private processor: AudioWorkletNode | null = null;
    private captureAbort: AbortController | null = null;
    private captureRevision: number | null = null;
    private session: LiveSessionView | null = null;
    private pendingICE: RTCIceCandidateInit[] = [];
    private offering = false;
    private closed = false;

    constructor(
        private token: string,
        private user: string,
        private remote: HTMLAudioElement,
        private update: (update: CallUpdate) => void,
    ) {}

    private send(message: unknown) {
        if (this.socket?.readyState === WebSocket.OPEN)
            this.socket.send(JSON.stringify(message));
    }

    async connect(room: LiveSessionView, analysis: boolean): Promise<void> {
        this.session = room;
        try {
            if (!window.isSecureContext || !navigator.mediaDevices)
                throw new Error(
                    "Use HTTPS or the local loopback workspace to access a microphone.",
                );
            this.stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                },
                video: false,
            });
            if (this.closed) {
                this.stream.getTracks().forEach((t) => t.stop());
                return;
            }
            this.peer = new RTCPeerConnection({
                iceServers: [],
                bundlePolicy: "max-bundle",
            });
            this.stream.getAudioTracks().forEach((track) => {
                track.onended = () => {
                    void this.stop("Microphone access ended. Call closed.");
                };
                this.peer!.addTrack(track, this.stream!);
            });
            this.peer.ontrack = (event) => {
                this.remote.srcObject =
                    event.streams[0] ?? new MediaStream([event.track]);
                void this.remote.play().catch(() =>
                    this.update({
                        notice: "Select Enable speaker to hear the other participant.",
                    }),
                );
            };
            this.peer.onicecandidate = (event) =>
                this.send({
                    type: "signal",
                    signal: {
                        kind: "ice",
                        candidate: event.candidate?.candidate ?? null,
                        sdp_mid: event.candidate?.sdpMid ?? null,
                        sdp_mline_index: event.candidate?.sdpMLineIndex ?? null,
                    },
                });
            this.peer.onconnectionstatechange = () => {
                if (this.closed) return;
                const state = this.peer?.connectionState ?? "closed";
                this.update({ connection: state });
                this.send({ type: "connection", media_state: state });
                if (state !== "connected") this.stopCapture();
                if (this.disconnectTimer) clearTimeout(this.disconnectTimer);
                if (state === "failed" || state === "disconnected")
                    this.disconnectTimer = setTimeout(() => {
                        void this.stop(
                            "Connection lost. Reconnect starts a new consented session.",
                        );
                    }, 10000);
            };
            const ticket = validateResource<LiveTicket>(
                "LiveTicket",
                await sendResource(
                    `/api/v1/live/sessions/${room.id}/tickets`,
                    this.token,
                    "POST",
                ),
            );
            if (this.closed) return;
            const address = new URL(
                `/api/v1/live/socket/${room.id}`,
                location.origin,
            );
            address.protocol = location.protocol === "https:" ? "wss:" : "ws:";
            this.socket = new WebSocket(address);
            await new Promise<void>((resolve, reject) => {
                const deadline = setTimeout(
                    () => reject(new Error("Call signaling timed out.")),
                    8000,
                );
                this.socket!.onopen = () =>
                    this.socket!.send(
                        JSON.stringify({ ticket: ticket.ticket }),
                    );
                this.socket!.onmessage = (event) => {
                    try {
                        const data = validateResource<LiveEvent>(
                            "LiveEvent",
                            JSON.parse(String(event.data)),
                        );
                        if (data.type === "session") {
                            clearTimeout(deadline);
                            resolve();
                        }
                        void this.event(data).catch((e) => {
                            void this.stop(liveError(e));
                        });
                    } catch {
                        clearTimeout(deadline);
                        reject(new Error("Call events could not be verified."));
                        void this.stop(
                            "Invalid call event. Microphone released.",
                        );
                    }
                };
                this.socket!.onerror = () => {
                    clearTimeout(deadline);
                    reject(new Error("Call signaling failed."));
                };
                this.socket!.onclose = () => {
                    clearTimeout(deadline);
                    reject(new Error("Call signaling closed."));
                    void this.stop(
                        "Call disconnected. Microphone and capture released.",
                        false,
                    );
                };
            });
            if (this.closed) return;
            await sendResource(
                `/api/v1/live/sessions/${room.id}/consent`,
                this.token,
                "PATCH",
                { microphone: true, analysis },
            );
            this.timer = setInterval(() => {
                this.send({ type: "ping" });
                void this.readStats().catch(() => {});
            }, 3000);
            this.update({
                connection:
                    this.peer?.connectionState === "connected"
                        ? "connected"
                        : "waiting",
            });
        } catch (error) {
            const message =
                error instanceof DOMException &&
                error.name === "NotAllowedError"
                    ? "Microphone permission was denied. Allow it in your browser, then reconnect."
                    : liveError(error);
            await this.stop(message);
            throw new Error(message);
        }
    }

    private async event(event: LiveEvent) {
        if (this.closed) return;
        if (event.type === "terminated") {
            await this.stop(
                "Call ended. Microphone, capture and session cleared.",
                false,
            );
            return;
        }
        if (event.type === "session" && event.session) {
            this.session = event.session;
            this.update({
                session: event.session,
                receivedSamples:
                    event.session.participants.find(
                        (p) => p.user_id === this.user,
                    )?.accepted_samples ?? 0,
            });
            if (!event.session.capture_allowed) this.stopCapture();
            else if (
                this.captureRevision !== event.session.consent_revision &&
                this.peer?.connectionState === "connected"
            )
                void this.startCapture(event.session.consent_revision);
            if (
                !this.offering &&
                this.user === event.session.initiator_user_id &&
                event.session.participants.every(
                    (p) => p.microphone && p.socket_connected,
                )
            ) {
                this.offering = true;
                const offer = await this.peer!.createOffer();
                await this.peer!.setLocalDescription(offer);
                this.send({
                    type: "signal",
                    signal: { kind: "offer", sdp: offer.sdp },
                });
            }
        }
        if (event.type === "signal" && event.signal)
            await this.signal(event.signal);
        if (
            event.type === "transcript" &&
            event.consent_revision === this.session?.consent_revision &&
            this.session?.capture_allowed
        )
            this.update({
                event,
                notice:
                    event.transcript?.state === "failed"
                        ? "Recognition interrupted. Retrying once; interim text is not final."
                        : "",
            });
        if (event.type === "notice")
            this.update({
                notice:
                    event.code === "backpressure"
                        ? "Analysis paused because its bounded buffer filled. You may continue talking."
                        : event.code === "analysis_retrying"
                          ? "Recognition interrupted. Retrying once; interim text is not final."
                          : "Local recognition failed twice. Analysis stopped. Both participants must re-enable analysis to try again.",
            });
    }

    private async signal(signal: LiveSignal) {
        const peer = this.peer;
        if (!peer) return;
        if (signal.kind === "ice") {
            if (signal.candidate) {
                const candidate = {
                    candidate: signal.candidate,
                    sdpMid: signal.sdp_mid,
                    sdpMLineIndex: signal.sdp_mline_index,
                };
                if (peer.remoteDescription)
                    await peer.addIceCandidate(candidate);
                else this.pendingICE.push(candidate);
            }
            return;
        }
        await peer.setRemoteDescription({
            type: signal.kind,
            sdp: signal.sdp ?? "",
        });
        for (const candidate of this.pendingICE.splice(0))
            await peer.addIceCandidate(candidate);
        if (signal.kind === "offer") {
            const answer = await peer.createAnswer();
            await peer.setLocalDescription(answer);
            this.send({
                type: "signal",
                signal: { kind: "answer", sdp: answer.sdp },
            });
        }
    }

    async finalize() {
        if (!this.session?.capture_allowed) throw new ApiError(403);
        await sendResource(
            `/api/v1/live/sessions/${this.session.id}/finalize`,
            this.token,
            "POST",
            { consent_revision: this.session.consent_revision },
        );
    }

    async setAnalysis(analysis: boolean) {
        if (!analysis) this.stopCapture();
        if (!this.session) return;
        try {
            await sendResource(
                `/api/v1/live/sessions/${this.session.id}/consent`,
                this.token,
                "PATCH",
                { microphone: true, analysis },
            );
        } catch (e) {
            await this.stop(liveError(e));
        }
    }

    private stopCapture() {
        this.captureRevision = null;
        this.captureAbort?.abort();
        this.captureAbort = null;
        if (this.processor) {
            this.processor.port.onmessage = null;
            this.processor.disconnect();
            this.processor = null;
        }
        if (this.context) {
            void this.context.close().catch(() => {});
            this.context = null;
        }
    }

    private async startCapture(revision: number) {
        this.stopCapture();
        this.captureRevision = revision;
        const context = new AudioContext({ sampleRate: 16000 });
        this.context = context;
        const abort = new AbortController();
        this.captureAbort = abort;
        try {
            await context.audioWorklet.addModule(
                new URL("./pcm-worklet.js", import.meta.url),
            );
            if (
                this.closed ||
                this.captureRevision !== revision ||
                !this.stream ||
                !this.session?.capture_allowed
            )
                return;
            if (context.sampleRate !== 16000)
                throw new Error(
                    "This browser cannot capture the required 16 kHz analysis format.",
                );
            const source = context.createMediaStreamSource(this.stream);
            const processor = new AudioWorkletNode(context, "project28-pcm", {
                channelCount: 1,
                channelCountMode: "explicit",
            });
            this.processor = processor;
            const silent = context.createGain();
            silent.gain.value = 0;
            source
                .connect(processor)
                .connect(silent)
                .connect(context.destination);
            await context.resume();
            let sequence = 0,
                busy = false;
            processor.port.onmessage = (event) => {
                if (
                    this.closed ||
                    this.captureRevision !== revision ||
                    !(event.data instanceof ArrayBuffer)
                )
                    return;
                if (busy) {
                    this.update({
                        notice: "Audio upload cannot keep up. Analysis stopped to avoid unbounded buffering.",
                    });
                    void this.setAnalysis(false);
                    return;
                }
                busy = true;
                const current = sequence++;
                void this.upload(event.data, current, revision, abort.signal)
                    .then((receipt) => {
                        if (this.captureRevision === revision)
                            this.update({
                                receivedSamples: receipt.accepted_samples,
                            });
                    })
                    .catch((e) => {
                        if (!abort.signal.aborted) {
                            this.update({ notice: liveError(e) });
                            void this.setAnalysis(false);
                        }
                    })
                    .finally(() => {
                        busy = false;
                    });
            };
        } catch (e) {
            if (this.captureRevision === revision) {
                this.update({ notice: liveError(e) });
                void this.setAnalysis(false);
            }
        }
    }

    private async upload(
        frame: ArrayBuffer,
        sequence: number,
        revision: number,
        signal: AbortSignal,
    ): Promise<AudioReceipt> {
        if (!this.session) throw new ApiError(409);
        const response = await fetch(
            `/api/v1/live/sessions/${this.session.id}/audio`,
            {
                method: "POST",
                body: frame,
                signal: AbortSignal.any([signal, AbortSignal.timeout(8000)]),
                headers: {
                    Authorization: `Bearer ${this.token}`,
                    "Content-Type": "application/octet-stream",
                    "X-Audio-Sequence": String(sequence),
                    "X-Audio-Start-Sample": String(sequence * 16000),
                    "X-Consent-Revision": String(revision),
                },
                credentials: "omit",
                redirect: "error",
                cache: "no-store",
            },
        );
        if (!response.ok) throw new ApiError(response.status);
        return validateResource<AudioReceipt>(
            "AudioReceipt",
            await response.json(),
        );
    }

    private async readStats() {
        const report = await this.peer?.getStats();
        if (!report) return;
        const stats: MediaStats = {
            packetsReceived: 0,
            packetsLost: 0,
            bytesReceived: 0,
            localLevel: null,
            remoteLevel: null,
            concealedSamples: null,
            totalSamplesReceived: null,
            dtlsState: null,
            codec: null,
        };
        report.forEach((item) => {
            if (item.type === "inbound-rtp" && item.kind === "audio") {
                stats.packetsReceived += item.packetsReceived ?? 0;
                stats.packetsLost += item.packetsLost ?? 0;
                stats.bytesReceived += item.bytesReceived ?? 0;
                stats.remoteLevel = item.audioLevel ?? null;
                stats.concealedSamples = item.concealedSamples ?? null;
                stats.totalSamplesReceived = item.totalSamplesReceived ?? null;
                stats.codec = report.get(item.codecId)?.mimeType ?? null;
            }
            if (item.type === "media-source" && item.kind === "audio")
                stats.localLevel = item.audioLevel ?? null;
            if (item.type === "transport")
                stats.dtlsState = item.dtlsState ?? null;
        });
        if (!this.closed) this.update({ stats });
    }

    async stop(
        notice = "Call ended. Microphone and capture released.",
        notify = true,
    ) {
        if (this.closed) return;
        this.closed = true;
        const id = this.session?.id;
        this.stopCapture();
        if (this.timer) clearInterval(this.timer);
        if (this.disconnectTimer) clearTimeout(this.disconnectTimer);
        this.stream?.getTracks().forEach((t) => {
            t.onended = null;
            t.stop();
        });
        this.stream = null;
        this.peer?.close();
        this.peer = null;
        this.socket?.close();
        this.socket = null;
        this.remote.pause();
        this.remote.srcObject = null;
        this.pendingICE = [];
        this.session = null;
        this.update({
            session: null,
            connection: "ended",
            notice,
            receivedSamples: 0,
            stats: undefined,
        });
        if (id && notify) {
            try {
                await sendResource(
                    `/api/v1/live/sessions/${id}`,
                    this.token,
                    "DELETE",
                );
            } catch {
                /* Socket disconnect also terminates the room. */
            }
        }
    }
}
