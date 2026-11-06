"""Synthetic multilingual retrieval fixture: BGE-M3 versus top-5 reranking.

Offline CPU evaluation only; authorization filtering is assumed before ranking.
This does not alter the production grounded-answer abstention policy.
"""

import hashlib
import json
import time
from pathlib import Path

DOCUMENTS = [
    "Refunds for a delivered product must be requested within thirty "
    "days of delivery. Return postage is paid by the customer.",
    "Orders cancelled before dispatch receive an automatic refund "
    "within five working days. No parcel needs to be returned.",
    "Duplicate card charges are reversed by billing after verifying "
    "the two transaction identifiers. Do not cancel the customer's "
    "order.",
    "Unrecognized card purchases require a fraud investigation. "
    "Freeze the payment method and escalate; never promise an "
    "immediate refund.",
    "Password reset: send a reset link to the verified email. The "
    "link expires after fifteen minutes. Never ask for the existing "
    "password.",
    "A locked account needs identity verification before support "
    "removes the lock. Resetting a password alone will not remove the "
    "lock.",
    "Lost two-factor device: use a recovery code or complete identity "
    "verification. Support must never disable verification based only "
    "on a phone request.",
    "Late delivery: check the tracking status and open a carrier "
    "investigation after seven days without an update.",
    "A parcel marked delivered but not received needs proof of "
    "delivery and an address check before a carrier claim is opened.",
    "Damaged item: request photographs of the damage and packaging. "
    "Offer replacement after validating the claim; do not use the "
    "late delivery procedure.",
    "Changing a delivery address is possible only before dispatch. "
    "After dispatch, contact the carrier for possible redirection.",
    "Subscription cancellation stops the next renewal but does not "
    "automatically refund the current subscription period.",
]
# Fixed labels were authored before any retrieval scores were observed.
QUERIES = [
    ("en", "How long do I have to return something that has arrived?", 0),
    ("en", "I cancelled before shipping; when does the money come back?", 1),
    ("en", "The same purchase was billed twice. Should the order be cancelled?", 2),
    ("en", "Changing my password did not unlock my account. What is required?", 5),
    ("en", "Tracking says delivered but I have no parcel. What evidence is needed?", 8),
    ("en", "Does cancelling renewal reimburse this month's subscription?", 11),
    ("fr", "Quel est le délai de retour pour un article déjà livré ?", 0),
    ("fr", "Ma commande annulée avant expédition sera remboursée quand ?", 1),
    ("fr", "Deux prélèvements pour le même achat : quelle procédure suivre ?", 2),
    ("fr", "Le changement de mot de passe ne débloque pas mon compte.", 5),
    ("fr", "Le colis est indiqué livré mais je ne l'ai pas reçu.", 8),
    ("fr", "Annuler le renouvellement rembourse-t-il le mois en cours ?", 11),
    ("ar", "ما هي مهلة إرجاع منتج تم تسليمه؟", 0),
    ("ar", "ألغيت طلبي قبل الشحن، متى يعود المبلغ؟", 1),
    ("ar", "تم خصم ثمن نفس الطلب مرتين، ما الإجراء؟", 2),
    ("ar", "غيرت كلمة المرور لكن حسابي لا يزال مقفلا، ماذا أفعل؟", 5),
    ("ar", "التتبع يقول تم التسليم لكن الطرد لم يصلني.", 8),
    ("ar", "هل إلغاء تجديد الاشتراك يعيد رسوم الشهر الحالي؟", 11),
]


def metrics(rank, relevant):
    position = rank.index(relevant) + 1 if relevant in rank else None
    return {
        "top1": int(position == 1),
        "recall5": int(position is not None and position <= 5),
        "reciprocal_rank": 1 / position if position else 0,
    }


def main():
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    from services.knowledge.embeddings import BgeM3

    torch.set_num_threads(4)
    root = Path(".local/model-upgrade-20261029")
    output = Path("docs/benchmarks/evidence/upgrade-20261029/retrieval.json")
    if output.exists():
        raise ValueError("Output already exists")
    fixture = {"documents": DOCUMENTS, "queries": QUERIES}
    fixture_raw = json.dumps(fixture, ensure_ascii=False, sort_keys=True).encode()
    output.with_name("retrieval-fixture.json").write_bytes(fixture_raw)
    start = time.perf_counter()
    encoder = BgeM3(
        Path(".local/step17-bge-m3").resolve(), "5617a9f61b028005a4858fdac845db406aefb181"
    )
    load_embed_seconds = time.perf_counter() - start
    start = time.perf_counter()
    vectors = torch.tensor(encoder.encode(DOCUMENTS))
    index_seconds = time.perf_counter() - start
    path = root / "reranker"
    tokenizer = AutoTokenizer.from_pretrained(str(path), local_files_only=True)
    start = time.perf_counter()
    reranker = AutoModelForSequenceClassification.from_pretrained(
        str(path), local_files_only=True, trust_remote_code=False
    ).eval()
    load_rerank_seconds = time.perf_counter() - start
    # Same warmup shapes as measured requests, without benchmark questions.
    encoder.encode(["warmup"])
    with torch.inference_mode():
        reranker(**tokenizer([["warmup", "warmup"]], return_tensors="pt"))
    rows = []
    for repeat in range(2):
        for index, (language, question, relevant) in enumerate(QUERIES):
            start = time.perf_counter()
            query = torch.tensor(encoder.encode([question])[0])
            rank = torch.argsort(vectors @ query, descending=True).tolist()
            dense_seconds = time.perf_counter() - start
            top = rank[:5]
            start = time.perf_counter()
            tokens = tokenizer(
                [[question, DOCUMENTS[j]] for j in top],
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )
            with torch.inference_mode():
                scores = reranker(**tokens).logits.view(-1)
            reranked = [top[j] for j in torch.argsort(scores, descending=True).tolist()]
            rows.append(
                {
                    "query": index,
                    "language": language,
                    "repeat": repeat,
                    "dense_seconds": dense_seconds,
                    "rerank_additional_seconds": time.perf_counter() - start,
                    "dense": metrics(rank[:5], relevant),
                    "reranked": metrics(reranked, relevant),
                    "dense_order": top,
                    "reranked_order": reranked,
                }
            )
            output.with_suffix(".partial.json").write_text(
                json.dumps(
                    {
                        "complete": False,
                        "fixture_sha256": hashlib.sha256(fixture_raw).hexdigest(),
                        "observations": rows,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            print("retrieval", repeat, index, flush=True)
    output.write_text(
        json.dumps(
            {
                "synthetic": True,
                "fixture_sha256": hashlib.sha256(fixture_raw).hexdigest(),
                "device": "cpu-float32",
                "torch_threads": 4,
                "index_seconds": index_seconds,
                "load_embed_seconds": load_embed_seconds,
                "load_rerank_seconds": load_rerank_seconds,
                "observations": rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
