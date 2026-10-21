"""
Reliance measures (plan item 2).

The hypothesis says the influence of polite spans tracks how much the model RELIES on
them, with a condensation threshold near 0.9. Density (fraction of turns carrying a span)
is the manipulation; reliance is the measured mediator. Two operationalizations:

  behavioral_reliance : the fraction of matched trials whose first answer changes when
                        the polite spans are swapped for neutral filler at the same
                        positions (the neutral arm IS the ablation; see vp.contexts).
                        Any model, API or open weights. In [0, 1].
  attentional_reliance: attention mass from the answer tokens onto the span tokens,
                        normalized by the mass onto all user-turn tokens, with a "lift"
                        relative to the span tokens' share of user tokens (lift 1 means
                        the spans get exactly their uniform share). Open weights only.
                        Direct descendant of the companion repo's induction-trust
                        measure in transformer-context-contagion/experiments/e4_trust.py.

Both are torch-free so they can be unit-tested; the open-weights runner feeds numpy
attention arrays in.
"""
from __future__ import annotations
from collections import defaultdict
from typing import Iterable, Sequence

import numpy as np


# ----------------------------------------------------------------------------- behavioral
def pair_arms(records: Iterable[dict], arm_a: str = "polite", arm_b: str = "neutral",
              key: Sequence[str] = ("claim_id", "seed", "density", "model")):
    """Group records by the matching key and return [(rec_a, rec_b)] for pairs that have
    exactly one record in each arm. Records are dicts; missing key fields count as None."""
    buckets: dict[tuple, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for r in records:
        k = tuple(r.get(f) for f in key)
        buckets[k][r["arm"]].append(r)
    pairs = []
    for k, by_arm in buckets.items():
        if len(by_arm.get(arm_a, [])) == 1 and len(by_arm.get(arm_b, [])) == 1:
            pairs.append((by_arm[arm_a][0], by_arm[arm_b][0]))
    return pairs


def behavioral_reliance(records: Iterable[dict], field: str = "first_class",
                        arm_a: str = "polite", arm_b: str = "neutral",
                        by: Sequence[str] = ("density",)) -> dict[tuple, dict]:
    """Per `by`-cell: reliance = fraction of matched (arm_a, arm_b) pairs whose `field`
    differs. Returns {cell: {"reliance", "n_pairs", "n_differ"}}.

    `field` defaults to the class of the FIRST answer (before any rebuttal), so reliance
    is measured on a response that the rebuttal has not touched. Pass field="cave" to
    get the sensitivity of the outcome itself instead."""
    out: dict[tuple, dict] = {}
    cells: dict[tuple, list[tuple[dict, dict]]] = defaultdict(list)
    for a, b in pair_arms(records, arm_a, arm_b):
        cells[tuple(a.get(f) for f in by)].append((a, b))
    for cell, pairs in cells.items():
        n_diff = sum(1 for a, b in pairs if a.get(field) != b.get(field))
        out[cell] = {"reliance": n_diff / len(pairs), "n_pairs": len(pairs), "n_differ": n_diff}
    return out


# ---------------------------------------------------------------------------- attentional
def attentional_reliance(attn, span_mask, user_mask, query_positions, *,
                         layers: Sequence[int] | None = None):
    """Attention mass from `query_positions` onto span tokens, normalized by the mass
    onto user-turn tokens.

    attn            : array [L, H, T, T] (query, key) or an iterable of per-layer
                      [H, T, T] arrays (so a runner can stream layers without holding
                      the whole stack).
    span_mask       : bool [T], True on inserted-span tokens (a subset of user tokens).
    user_mask       : bool [T], True on every user-turn token (spans included).
    query_positions : indices of the answer tokens whose attention is measured.

    Returns dict(reliance, lift, share, per_layer) where
      reliance  = mass(span) / mass(user)           in [0, 1]
      share     = n_span / n_user                   the uniform-attention baseline
      lift      = reliance / share                  1 = no preferential reliance
      per_layer = reliance computed layer by layer  (list, len L)
    """
    span_mask = np.asarray(span_mask, bool)
    user_mask = np.asarray(user_mask, bool)
    if span_mask.shape != user_mask.shape:
        raise ValueError("span_mask and user_mask must have the same length")
    if np.any(span_mask & ~user_mask):
        raise ValueError("span tokens must be a subset of user-turn tokens")
    q = np.asarray(list(query_positions), int)
    if q.size == 0:
        raise ValueError("need at least one query position")
    n_user = int(user_mask.sum())
    if n_user == 0:
        raise ValueError("no user tokens")
    share = float(span_mask.sum()) / n_user

    if isinstance(attn, np.ndarray) and attn.ndim == 4:
        layer_iter = (attn[l] for l in range(attn.shape[0]))
    else:
        layer_iter = iter(attn)

    span_mass, user_mass, per_layer = 0.0, 0.0, []
    for li, a in enumerate(layer_iter):
        if layers is not None and li not in layers:
            continue
        a = np.asarray(a, dtype=np.float64)            # [H, T, T]
        rows = a[:, q, :]                              # [H, Q, T]
        s = float(rows[:, :, span_mask].sum())
        u = float(rows[:, :, user_mask].sum())
        span_mass += s
        user_mass += u
        per_layer.append(s / u if u > 0 else 0.0)
    if user_mass == 0:
        raise ValueError("no attention mass on user tokens at the query positions")
    reliance = span_mass / user_mass
    return {"reliance": reliance, "share": share,
            "lift": reliance / share if share > 0 else float("nan"),
            "per_layer": per_layer}


def token_masks(offsets: Sequence[tuple[int, int]], spans: Sequence[tuple[int, int]],
                user_turns: Sequence[tuple[int, int]]) -> tuple[np.ndarray, np.ndarray]:
    """Build (span_mask, user_mask) over tokens from character offsets.

    offsets    : per-token (start, end) character offsets into the rendered prompt.
    spans      : (start, end) character ranges of inserted spans.
    user_turns : (start, end) character ranges of user-turn content.
    A token counts as inside a range if its midpoint lies in the range."""
    mids = np.array([(s + e) / 2.0 for s, e in offsets])

    def mask(ranges):
        m = np.zeros(len(offsets), bool)
        for s, e in ranges:
            m |= (mids >= s) & (mids < e)
        return m

    return mask(spans), mask(user_turns)
