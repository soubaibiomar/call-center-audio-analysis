"""Standalone probe sent to an isolated container; imports no project secrets."""

import io
import sys


def main() -> None:
    import av

    try:
        data = sys.stdin.buffer.read(50 * 1024 * 1024 + 1)
        if not data or len(data) > 50 * 1024 * 1024:
            raise ValueError("size")
        fmt, expected = sys.argv[1], float(sys.argv[2])
        if fmt not in {"wav", "mp3", "flac", "mov"}:
            raise ValueError("format")
        seconds = 0.0
        with av.open(
            io.BytesIO(data), mode="r", format=fmt, options={"protocol_whitelist": "pipe"}
        ) as container:
            if len(container.streams.audio) != 1:
                raise ValueError("streams")
            for frame in container.decode(container.streams.audio[0]):
                if frame.sample_rate <= 0:
                    raise ValueError("rate")
                seconds += frame.samples / frame.sample_rate
                if seconds > 3600.2:
                    raise ValueError("duration")
        if seconds <= 0 or seconds < expected - max(0.2, expected * 0.02):
            raise ValueError("incomplete")
        print("ok")
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
