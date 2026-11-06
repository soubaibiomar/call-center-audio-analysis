"""Local Ollama controlled-context summary comparison, synthetic labeled cases.

Unlike the separate application-default run, this uses the native API with
think=false and num_ctx=4096 for all models. It does not change saved defaults.
Resolution accuracy is narrow: it does not measure comprehensive QA accuracy.
"""

import json
import time
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import httpx

from src.agents.summarization import SYSTEM_PROMPT
from src.graph.state import SummaryResult
from src.utils.llm_factory import require_local_model

CASES = [
    (
        "en",
        "Customer: I was charged twice. Agent: I removed the duplicate "
        "charge. Customer: That resolves it.",
        "resolved",
    ),
    (
        "en",
        "Customer: My package is late. Agent: I will investigate "
        "tomorrow. Customer: The issue is still open.",
        "unresolved",
    ),
    (
        "en",
        "Customer: I cannot sign in. Agent: I am transferring your case "
        "to account support. Customer: I still need access.",
        "escalated",
    ),
    (
        "fr",
        "Client : Le paiement est en double. Agent : J'ai annulé le "
        "doublon. Client : Le problème est résolu.",
        "resolved",
    ),
    (
        "fr",
        "Client : Mon colis est en retard. Agent : Je vais enquêter "
        "demain. Client : Le problème reste ouvert.",
        "unresolved",
    ),
    (
        "fr",
        "Client : Je ne peux pas me connecter. Agent : Je transfère votre "
        "dossier au support des comptes. Client : Je n'ai toujours pas "
        "accès.",
        "escalated",
    ),
    (
        "ar",
        "العميل: تم خصم المبلغ مرتين. الموظف: ألغيت الخصم المكرر. العميل: تم حل المشكلة.",
        "resolved",
    ),
    (
        "ar",
        "العميل: تأخر طردي. الموظف: سأحقق في الأمر غدا. العميل: المشكلة لا تزال مفتوحة.",
        "unresolved",
    ),
    (
        "ar",
        "العميل: لا يمكنني تسجيل الدخول. الموظف: أحيل قضيتك إلى فريق دعم "
        "الحسابات. العميل: ما زلت بحاجة إلى الدخول.",
        "escalated",
    ),
]
MODELS = ["qwen2.5-coder:7b", "qwen3.5:4b-q4_K_M", "qwen3.5:9b-q4_K_M"]


def main():
    output = Path("docs/benchmarks/evidence/upgrade-20261029/llm-quality.json")
    if output.exists():
        raise ValueError("Output already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(trust_env=False, timeout=180) as client:
        root = "http://127.0.0.1:11434"
        inventory = {
            model["name"]: model for model in client.get(root + "/api/tags").json()["models"]
        }
        previous = client.get(root + "/api/ps").json()
        previous_names = {entry["name"] for entry in previous["models"]}
        report = {
            "synthetic": True,
            "conditions": "serial; native API; think=false; context4096; temperature0; "
            "seed42; max2048; one attempt; warmup excluded; two repetitions",
            "preexisting_loaded_at_quality_start": previous,
            "models": [],
        }
        for name in MODELS:
            require_local_model(root + "/v1", name, 10)
            rows = []
            for repeat in (-1, 0, 1):
                cases = (
                    [("warmup", "Customer: Hello. Agent: Hello.", None)] if repeat == -1 else CASES
                )
                for index, (language, text, expected) in enumerate(cases):
                    call_id = uuid5(NAMESPACE_URL, f"upgrade-{repeat}-{index}")
                    start = time.perf_counter()
                    response = client.post(
                        root + "/api/chat",
                        json={
                            "model": name,
                            "stream": False,
                            "think": False,
                            "keep_alive": "10m",
                            "format": SummaryResult.model_json_schema(),
                            "options": {
                                "num_ctx": 4096,
                                "num_predict": 2048,
                                "temperature": 0,
                                "seed": 42,
                            },
                            "messages": [
                                {
                                    "role": "system",
                                    "content": SYSTEM_PROMPT
                                    + f"\nReturn this exact call_id UUID: {call_id}.",
                                },
                                {
                                    "role": "user",
                                    "content": f"Transcript:\n[00:00-00:20] dialogue: {text}",
                                },
                            ],
                        },
                    )
                    elapsed = time.perf_counter() - start
                    response.raise_for_status()
                    raw = response.json()
                    try:
                        result = SummaryResult.model_validate_json(raw["message"]["content"])
                        valid = True
                        resolution = result.resolution_status
                    except (ValueError, KeyError):
                        valid, resolution = False, None
                    if repeat != -1:
                        rows.append(
                            {
                                "language": language,
                                "fixture": index,
                                "repeat": repeat,
                                "schema_valid": valid,
                                "expected": expected,
                                "resolution": resolution,
                                "correct_resolution": valid and resolution == expected,
                                "seconds": elapsed,
                                "timings": {
                                    key: value
                                    for key, value in raw.items()
                                    if key
                                    in [
                                        "total_duration",
                                        "load_duration",
                                        "prompt_eval_duration",
                                        "eval_duration",
                                        "prompt_eval_count",
                                        "eval_count",
                                        "done_reason",
                                    ]
                                },
                            }
                        )
                        report["models"] = [
                            entry for entry in report["models"] if entry["model"] != name
                        ] + [
                            {
                                "model": name,
                                "digest": inventory[name]["digest"],
                                "rows": rows,
                                "loaded": client.get(root + "/api/ps").json(),
                            }
                        ]
                        output.write_text(json.dumps(report, indent=2), encoding="utf-8")
                        print(
                            name,
                            language,
                            repeat,
                            index,
                            valid,
                            resolution,
                            round(elapsed, 2),
                            flush=True,
                        )
            if name not in previous_names:
                client.post(
                    root + "/api/generate", json={"model": name, "keep_alive": 0}
                ).raise_for_status()


if __name__ == "__main__":
    main()
