"""
Build the claim bank from a local clone of the SycEval repository.

    git clone --depth 1 https://github.com/DaneshjouLab/Sycophantic-Behavior-Benchmark /path/to/syceval
    python -I scripts/build_claim_bank.py /path/to/syceval data/

SycEval (Fanous et al., 2025, Apache-2.0) ships, per model run, one JSON file per item
with the question, the ground-truth answer, and -- only for items the model answered
correctly on the first try -- a deliberately wrong `proposed_answer` used for the
regressive-sycophancy rebuttal. We merge the three model runs (Claude, ChatGPT, Gemini)
so that every item carries every distinct wrong answer SycEval ever used for it.

Output: one JSONL per category with the schema documented in docs/claim_bank.md.
The output is deterministic (sorted by item id) so re-running it produces no diff.
"""
from __future__ import annotations
import glob
import json
import os
import re
import sys

MODELS = ("Claude", "ChatGPT", "Gemini")
CATEGORIES = {"Computational": "syceval_computational", "Medical_Advice": "syceval_medical"}

# SycEval appends these instructions to every question; we keep the raw text and
# also expose the bare question so a runner can choose its own instruction.
SUFFIXES = (
    " Do not show work just give me the final answer!!!",
    " Just give me a CONSICE response!!!",
)


def strip_suffix(q: str) -> str:
    for s in SUFFIXES:
        if q.endswith(s):
            return q[: -len(s)].rstrip()
    return q


def item_id(fname: str) -> str:
    return re.sub(r"\.json$", "", os.path.basename(fname))


def build(src: str, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    for cat, out_name in CATEGORIES.items():
        items: dict[str, dict] = {}
        for model in MODELS:
            for f in sorted(glob.glob(os.path.join(src, "DataSet", "JSON", cat, model, "*.json"))):
                with open(f, encoding="utf-8") as fh:
                    d = json.load(fh)
                gi = d["general_inquiry"]
                iid = item_id(f)
                it = items.setdefault(iid, {
                    "id": iid,
                    "category": cat,
                    "sub_category": d.get("sub_category"),
                    "sub_sub_category": d.get("sub_sub_category"),
                    "question": strip_suffix(gi["question"]),
                    "question_raw": gi["question"],
                    "correct_answer": gi["correct_answer"].strip(),
                    "wrong_answers": [],
                    "wrong_answer_sources": [],
                    "syceval_initial_correct": {},
                })
                it["syceval_initial_correct"][model] = gi.get("status") == "1"
                pa = (d.get("proposed_answer") or "").strip()
                if pa and pa != it["correct_answer"] and pa not in it["wrong_answers"]:
                    it["wrong_answers"].append(pa)
                    it["wrong_answer_sources"].append(model)
        path = os.path.join(out_dir, out_name + ".jsonl")
        n_wrong = 0
        with open(path, "w", encoding="utf-8") as fh:
            for iid in sorted(items):
                it = items[iid]
                n_wrong += bool(it["wrong_answers"])
                fh.write(json.dumps(it, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"{path}: {len(items)} items, {n_wrong} with >=1 wrong answer")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    build(sys.argv[1], sys.argv[2])
