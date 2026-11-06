"""Convert approved local safetensors to the same FP16 CTranslate2 runtime as baseline.

Run in project28-upgrade-whisper:local without network/GPU access. No training.
"""

import hashlib
import importlib.metadata
import json
from pathlib import Path


def main():
    from ctranslate2.converters import TransformersConverter
    from transformers import WhisperTokenizerFast

    source = Path(".local/model-upgrade-20261029/darija-small")
    output = Path(".local/darija-specialist-20261029/darija-small-ct2")
    receipt = json.loads((source / "download-receipt.json").read_bytes())
    if output.exists() or receipt["revision"] != "d3c4fd5048c5f182dea49e4af8670037a699cfe6":
        raise ValueError("New output and approved source revision required")
    converter = TransformersConverter(
        str(source), copy_files=["preprocessor_config.json"], trust_remote_code=False
    )
    converter.convert(str(output), quantization="float16")
    tokenizer = WhisperTokenizerFast.from_pretrained(str(source), local_files_only=True)
    tokenizer.backend_tokenizer.save(str(output / "tokenizer.json"))
    files = []
    for path in sorted(output.iterdir()):
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        files.append({"file": path.name, "size": path.stat().st_size, "sha256": digest.hexdigest()})
    report = {
        "source_repo": receipt["repo"],
        "source_revision": receipt["revision"],
        "source_receipt": receipt,
        "operation": "CTranslate2 FP16 export, not training",
        "ctranslate2": importlib.metadata.version("ctranslate2"),
        "transformers": importlib.metadata.version("transformers"),
        "files": files,
    }
    (output / "conversion-receipt.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    Path("docs/benchmarks/evidence/darija-specialist-20261029/conversion.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print("Converted approved Darija Whisper to FP16 CTranslate2", flush=True)


if __name__ == "__main__":
    main()
