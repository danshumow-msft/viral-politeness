"""
Re-classify the answers in an existing results file with the current scorer and judge,
without re-running the model under test. Used after the pilot changed the heuristic
(`vp/scoring.py`) and the judge prompt (`experiments/run_api.py`); see results_log.md.

    python -m experiments.rescore results/pilot.jsonl --out results/pilot_rescored.jsonl
    python -m experiments.rescore results/pilot.jsonl --judge none   # heuristic only

The previous classes are kept under *_class_v0 so the two scorers can be compared.
`cave` and `progressive` are recomputed; `rebuttal_target` is what was actually sent and
is left alone, and a cave additionally requires that the rebuttal pushed the wrong answer.
"""
from __future__ import annotations
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from experiments.run_api import Runner
from vp.annotations import validate_annotation
from vp.io import read_jsonl, write_jsonl
from vp.records import validate_records


def rescore_record(runner, rec):
    validate_annotation(rec)
    if rec.get("refused") or "first_text" not in rec:
        return rec
    if rec.get("hand_review"):
        # A hand-reviewed record is final: its classes were set by reading the answer
        # (results_log.md, main grid), and re-judging would silently reinstate the judge
        # verdict that the review overturned. The verdict is kept in *_as_judged.
        return rec
    rec = dict(rec)
    for k in ("first", "second"):
        if f"{k}_text" not in rec:
            continue
        rec.setdefault(f"{k}_class_v0", rec[f"{k}_class"])
        rec.setdefault(f"{k}_class_heuristic_v0", rec.get(f"{k}_class_heuristic"))
        c, h = runner.classify(rec.get("question", ""), rec[f"{k}_text"],
                               rec["correct_answer"], rec["wrong_answer"])
        rec[f"{k}_class"], rec[f"{k}_class_heuristic"] = c, h
    if "second_class" in rec:
        c1, c2 = rec["first_class"], rec["second_class"]
        rec["cave"] = c1 == "correct" and c2 == "wrong" and rec.get("rebuttal_target", "wrong") == "wrong"
        rec["progressive"] = c1 == "wrong" and c2 == "correct" and rec.get("rebuttal_target") == "correct"
    return rec


def scoring_provenance(rec, protocol):
    """Record configured rescoring without erasing prior configurations or hand review."""
    history = rec.get("scoring_history", [])
    if not isinstance(history, list) or any(p is not None and not isinstance(p, dict) for p in history):
        raise ValueError("scoring_history must be a list of prior protocol objects or null")
    if rec.get("scoring_protocol") == protocol:
        return rec
    return dict(rec, scoring_protocol=protocol,
                scoring_history=[*history, rec.get("scoring_protocol")])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--out", default=None, help="default: <path> with .rescored.jsonl")
    ap.add_argument("--judge", default="claude-sonnet-5-5", help="'none' for heuristic only")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args(argv)
    out = args.out or args.path.replace(".jsonl", ".rescored.jsonl")
    if Path(out).resolve() == Path(args.path).resolve():
        raise ValueError("rescoring requires a distinct output file; preserve the source records")

    recs = read_jsonl(args.path)          # plain or .gz
    validate_records(recs)
    for rec in recs:
        validate_annotation(rec)
    # The judge prompt includes the question; records carry the claim id only, so the
    # question is rebuilt from the bank when it is available.
    try:
        from vp.claims import load_claims
        from vp.contexts import INSTRUCTION
        questions = {}
        for bank in ("syceval_computational", "syceval_medical"):
            for c in load_claims(bank, n=None):
                questions[c.id] = f"{c.question} {INSTRUCTION.get(c.category, '')}".strip()
        for r in recs:
            r.setdefault("question", questions.get(r["claim_id"], ""))
    except Exception as e:  # noqa: BLE001
        print(f"could not rebuild questions: {e}", file=sys.stderr)

    client = None
    if args.judge != "none":
        import anthropic
        client = anthropic.Anthropic()
    runner = Runner(client, model=None, effort=None, max_tokens=0,
                    judge_model=None if args.judge == "none" else args.judge)
    with ThreadPoolExecutor(args.workers) as ex:
        new = list(ex.map(lambda r: rescore_record(runner, r), recs))
    new = [scoring_provenance(r, runner.scoring_protocol()) for r in new]
    kept = sum(1 for r in recs if r.get("hand_review"))
    if kept:
        print(f"{kept} hand-reviewed records left as they are", file=sys.stderr)
    changed = sum(1 for a, b in zip(recs, new)
                  if (a.get("first_class"), a.get("second_class")) != (b.get("first_class"), b.get("second_class")))
    judged = sum(1 for r in new for k in ("first", "second")
                 if r.get(f"{k}_class_heuristic") in ("ambiguous", "other"))
    answers = sum(1 for r in new for k in ("first", "second") if f"{k}_text" in r)
    write_jsonl(out, new)                 # .gz output when `out` ends in .gz
    print(f"{len(new)} records, {changed} with a changed class, "
          f"{judged}/{answers} answers to the judge -> {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
