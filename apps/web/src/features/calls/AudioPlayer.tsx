import { useEffect, useRef, useState, type RefObject } from "react";
import WaveSurfer from "wavesurfer.js";
import type { Report } from "../../lib/api/generated";
import { safeSeek, timeLabel } from "../workspace/shared";

export function buildWebVtt(
    segments: Report["transcription"]["segments"],
): string {
    function stamp(seconds: number) {
        const milliseconds = Math.round(seconds * 1000);
        return `${Math.floor(milliseconds / 3600000)
            .toString()
            .padStart(2, "0")}:${Math.floor((milliseconds / 60000) % 60)
            .toString()
            .padStart(2, "0")}:${Math.floor((milliseconds / 1000) % 60)
            .toString()
            .padStart(
                2,
                "0",
            )}.${(milliseconds % 1000).toString().padStart(3, "0")}`;
    }
    return (
        "WEBVTT\n\n" +
        segments
            .filter(
                (s) =>
                    Number.isFinite(s.start_time) &&
                    Number.isFinite(s.end_time) &&
                    s.start_time >= 0 &&
                    Math.round(s.end_time * 1000) >
                        Math.round(s.start_time * 1000),
            )
            .map(
                (s) =>
                    `${stamp(s.start_time)} --> ${stamp(s.end_time)}\n${s.text
                        .replaceAll("&", "&amp;")
                        .replaceAll("<", "&lt;")
                        .replaceAll(">", "&gt;")
                        .replace(/\n\s*\n/g, "\n")}\n`,
            )
            .join("\n")
    );
}
export function AudioPlayer({
    audioRef,
    onReady,
    segments,
    onFileSelected,
    registeredSource = false,
}: {
    audioRef: RefObject<HTMLAudioElement | null>;
    onReady: (ready: boolean) => void;
    segments: Report["transcription"]["segments"];
    onFileSelected?: (file: File | null) => void;
    registeredSource?: boolean;
}) {
    const container = useRef<HTMLDivElement>(null);
    const track = useRef<HTMLTrackElement>(null);
    const [file, setFile] = useState<File | null>(null);
    const [error, setError] = useState("");
    const [duration, setDuration] = useState(0);
    const [position, setPosition] = useState(0);
    useEffect(() => {
        const url = URL.createObjectURL(
            new Blob([buildWebVtt(segments)], { type: "text/vtt" }),
        );
        if (track.current) track.current.src = url;
        return () => URL.revokeObjectURL(url);
    }, [segments]);
    useEffect(() => {
        const media = audioRef.current;
        if (!file || !container.current || !media) return;
        onReady(false);
        setError("");
        setDuration(0);
        setPosition(0);
        const wave = WaveSurfer.create({
            container: container.current,
            media,
            waveColor: "#BBCBBD",
            progressColor: "#1D5B49",
            cursorColor: "#1D5B49",
            height: 72,
            interact: true,
        });
        let active = true;
        wave.on("ready", (seconds) => {
            if (!active) return;
            if (!Number.isFinite(seconds) || seconds <= 0 || seconds > 1800) {
                setError("Select a valid recording of up to 30 minutes.");
                media.pause();
                onReady(false);
                return;
            }
            setDuration(seconds);
            onReady(true);
        });
        wave.on("timeupdate", (seconds) => {
            if (active) setPosition(seconds);
        });
        void wave.loadBlob(file).catch(() => {
            if (active) {
                setError(
                    "This recording could not be decoded. Select a supported local file.",
                );
                onReady(false);
            }
        });
        return () => {
            active = false;
            wave.destroy();
            media.pause();
            media.removeAttribute("src");
            media.load();
        };
    }, [file, audioRef, onReady]);
    function choose(candidate?: File) {
        onReady(false);
        setFile(null);
        onFileSelected?.(null);
        setDuration(0);
        if (!candidate) return;
        if (
            candidate.size > 25 * 1024 * 1024 ||
            !/\.(wav|mp3)$/i.test(candidate.name)
        ) {
            setError("Choose a WAV or MP3 recording no larger than 25 MB.");
            return;
        }
        setFile(candidate);
        onFileSelected?.(candidate);
    }
    return (
        <section className="panel audio-panel">
            <div className="section-title">
                <div>
                    <p className="eyebrow">PRIVATE LOCAL PLAYBACK</p>
                    <h2>Listen to the evidence</h2>
                </div>
                <span className="pill caution">
                    {registeredSource
                        ? "Administrator-attested source"
                        : "Source not verified"}
                </span>
            </div>
            <p className="muted">
                Select the corresponding recording on your laptop. It stays in
                this tab; it is not uploaded.{" "}
                {registeredSource
                    ? "The review checks its checksum against the registered source."
                    : "This app cannot verify that a selected file belongs to this report."}
            </p>
            <label className="file-picker">
                Local recording
                <input
                    type="file"
                    accept=".wav,.mp3,audio/wav,audio/mpeg"
                    onChange={(event) => choose(event.target.files?.[0])}
                />
            </label>
            <div ref={container} aria-hidden="true" />
            <audio
                ref={audioRef}
                controls
                aria-label="Selected local call recording"
                aria-describedby="transcript-heading"
            >
                <track
                    ref={track}
                    kind="captions"
                    srcLang="und"
                    label="Model transcript (unverified)"
                    default
                />
            </audio>
            <label className="seek-control">
                Playback position · {timeLabel(position)} /{" "}
                {timeLabel(duration)}
                <input
                    type="range"
                    min={0}
                    max={duration || 1}
                    step={0.1}
                    value={Math.min(position, duration || 0)}
                    disabled={!duration || Boolean(error)}
                    onChange={(event) => {
                        const target = safeSeek(
                            Number(event.target.value),
                            duration,
                        );
                        if (target !== null && audioRef.current)
                            audioRef.current.currentTime = target;
                    }}
                />
            </label>
            {file && <p className="field-hint">Selected: {file.name}</p>}
            {error && (
                <p role="alert" className="error-message">
                    {error}
                </p>
            )}
        </section>
    );
}
