"""Trial identity and compatibility checks shared by analysis and runner preflights."""
from __future__ import annotations

import json
import math
from collections.abc import Iterable

TRIAL_FIELDS = ("model", "claim_id", "arm", "density", "seed", "span_length")
PAIR_FIELDS = ("claim_id", "seed", "density", "model", "span_length")
PROFILE_FIELDS = (
    "protocol", "scoring_protocol", "n_turns", "effort", "served_model",
    "bank", "max_tokens", "judge_model", "protocol_version", "scorer_version", "sampling",
)
REQUIRED_METADATA = ("protocol", "scoring_protocol", "n_turns", "served_model")


def trial_identity(record: dict) -> tuple:
    if not isinstance(record, dict):
        raise ValueError("trial record must be a JSON object")
    for field in ("model", "claim_id", "arm"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            raise ValueError(f"trial requires a nonempty {field}")
    density, seed = record.get("density"), record.get("seed")
    if (isinstance(density, bool) or not isinstance(density, (float, int))
            or not math.isfinite(density) or not 0 <= density <= 1):
        raise ValueError(f"invalid density for {record['claim_id']}: {density!r}")
    if type(seed) is not int or seed < 0:
        raise ValueError(f"invalid seed for {record['claim_id']}: {seed!r}")
    length = record.get("span_length", "medium")
    if length not in ("short", "medium", "long"):
        raise ValueError(f"invalid span_length for {record['claim_id']}: {length!r}")
    return (record["model"], record["claim_id"], record["arm"], float(density), seed, length)


def _encoded(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def validate_records(records: Iterable[dict]) -> dict[str, dict]:
    """Reject duplicate trials and incompatible metadata within each model's pool.

    Missing metadata is allowed only when consistently absent, and is reported as
    unverified rather than guessed from a model name or the historical defaults.
    """
    seen = set()
    profiles: dict[str, dict] = {}
    claims: dict[tuple, dict] = {}
    layouts: dict[tuple, dict] = {}
    for r in records:
        identity = trial_identity(r)
        if identity in seen:
            raise ValueError(f"duplicate trial: {identity!r}")
        seen.add(identity)
        for field in ("protocol", "scoring_protocol"):
            if field in r and (not isinstance(r[field], dict)
                               or type(r[field].get("version")) is not int
                               or r[field]["version"] != 1):
                raise ValueError(f"unsupported {field} for {identity!r}")
        if "served_model2" in r and r["served_model2"] != r.get("served_model"):
            raise ValueError(f"incompatible served_model across calls for {identity!r}")
        metadata = {f: r[f] for f in PROFILE_FIELDS if f in r}
        profile = profiles.setdefault(r["model"], {
            "metadata": metadata,
            "unverified_fields": [f for f in REQUIRED_METADATA if f not in r],
        })
        for f in PROFILE_FIELDS:
            if ((f in metadata) != (f in profile["metadata"])
                    or _encoded(metadata.get(f)) != _encoded(profile["metadata"].get(f))):
                raise ValueError(f"incompatible {f} in model pool {r['model']!r}")
        claim = claims.setdefault((r["model"], r["claim_id"]), {
            f: r[f] for f in ("correct_answer", "wrong_answer") if f in r
        })
        for f in ("correct_answer", "wrong_answer"):
            if ((f in r) != (f in claim) or r.get(f) != claim.get(f)):
                raise ValueError(f"incompatible {f} for claim {r['claim_id']!r}")
        layout_key = identity[:2] + identity[3:]
        layout = layouts.setdefault(layout_key, {
            f: r[f] for f in ("n_spans", "span_positions", "phrase_indices") if f in r
        })
        for f in ("n_spans", "span_positions", "phrase_indices"):
            if ((f in r) != (f in layout) or r.get(f) != layout.get(f)):
                raise ValueError(f"incompatible {f} across arms for trial {layout_key!r}")
    return profiles


def completed_trials(records: list[dict], model: str, protocol: dict,
                     scoring_protocol: dict) -> set[tuple]:
    """Only resume records whose recorded configuration matches the requested run."""
    validate_records(records)
    for r in records:
        if r["model"] != model:
            raise ValueError("cannot resume a file containing another model")
        for field, expected in (("protocol", protocol), ("scoring_protocol", scoring_protocol)):
            if field not in r or _encoded(r[field]) != _encoded(expected):
                raise ValueError(f"cannot resume incompatible or unverified {field}; use a new output file")
    return {trial_identity(r) for r in records}
