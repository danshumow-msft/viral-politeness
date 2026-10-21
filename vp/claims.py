"""
Claim bank: questions with a known correct answer and at least one known wrong answer.

The bank is built from SycEval by scripts/build_claim_bank.py and vendored under data/.
Every source is exposed through one schema so the runners never care where a claim came
from.
"""
from __future__ import annotations
import json
import os
import random
from dataclasses import dataclass, field
from typing import Iterator

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

BANKS = {
    "syceval_computational": "syceval_computational.jsonl",
    "syceval_medical": "syceval_medical.jsonl",
}


@dataclass(frozen=True)
class Claim:
    id: str
    question: str
    correct_answer: str
    wrong_answers: tuple[str, ...]
    category: str
    sub_category: str | None = None
    sub_sub_category: str | None = None
    meta: dict = field(default_factory=dict, compare=False, hash=False)

    def wrong_answer(self, rng: random.Random | None = None) -> str:
        """One wrong answer, chosen with `rng` if more than one is known."""
        if not self.wrong_answers:
            raise ValueError(f"claim {self.id} has no wrong answer")
        if rng is None or len(self.wrong_answers) == 1:
            return self.wrong_answers[0]
        return rng.choice(self.wrong_answers)


def iter_claims(bank: str = "syceval_computational", *, require_wrong: bool = True,
                data_dir: str = DATA_DIR) -> Iterator[Claim]:
    """Yield claims from a bank in a fixed (sorted-by-id) order."""
    path = os.path.join(data_dir, BANKS[bank])
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            d = json.loads(line)
            if require_wrong and not d["wrong_answers"]:
                continue
            yield Claim(
                id=d["id"],
                question=d["question"],
                correct_answer=d["correct_answer"],
                wrong_answers=tuple(d["wrong_answers"]),
                category=d["category"],
                sub_category=d.get("sub_category"),
                sub_sub_category=d.get("sub_sub_category"),
                meta={k: d[k] for k in ("question_raw", "wrong_answer_sources",
                                        "syceval_initial_correct") if k in d},
            )


def load_claims(bank: str = "syceval_computational", *, n: int | None = None,
                seed: int = 0, **kw) -> list[Claim]:
    """Load a bank; with `n`, a seeded random subset (stable across runs)."""
    claims = list(iter_claims(bank, **kw))
    if n is not None and n < len(claims):
        claims = random.Random(seed).sample(claims, n)
        claims.sort(key=lambda c: c.id)
    return claims
