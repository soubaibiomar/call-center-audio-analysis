"""Offline BGE-M3 dense embeddings with a bounded local runtime."""

import hashlib
import importlib
from pathlib import Path


class BgeM3:
    dimension = 1024

    def __init__(self, path: Path, revision: str) -> None:
        if (
            not path.is_absolute()
            or not path.is_dir()
            or revision != "5617a9f61b028005a4858fdac845db406aefb181"
        ):
            raise ValueError("Pinned local model directory and revision required")
        digest = hashlib.sha256()
        with (path / "pytorch_model.bin").open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
        if digest.hexdigest() != "b5e0ce3470abf5ef3831aa1bd5553b486803e83251590ab7ff35a117cf6aad38":
            raise ValueError("Model weights differ from the approved revision")
        torch = importlib.import_module("torch")
        transformers = importlib.import_module("transformers")
        self.torch = torch
        self.revision = revision
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(
            str(path), local_files_only=True
        )
        self.model = transformers.AutoModel.from_pretrained(
            str(path), local_files_only=True, trust_remote_code=False, weights_only=True
        ).eval()

    def encode(self, texts: list[str]) -> list[list[float]]:
        if not 0 < len(texts) <= 16 or any(not t.strip() or len(t) > 8000 for t in texts):
            raise ValueError("Embedding batch exceeds bounds")
        tokens = self.tokenizer(texts, padding=True, truncation=False, return_tensors="pt")
        if tokens["input_ids"].shape[1] > 512:
            raise ValueError("Chunk exceeds the configured embedding token budget")
        with self.torch.inference_mode():
            output = self.model(**tokens).last_hidden_state[:, 0]
            vectors = self.torch.nn.functional.normalize(output, p=2, dim=1)
        if vectors.shape[1] != self.dimension:
            raise ValueError("Unexpected model dimension")
        return [[float(value) for value in row] for row in vectors.tolist()]
