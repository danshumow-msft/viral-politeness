"""
Open-weights runner (plan items 5 and 7): the same protocol as run_api.py on a local
Hugging Face model, plus attentional reliance, so base and instruct checkpoints of the
same family can be compared (the mechanism discriminator).

    python -m experiments.run_openweights --model Qwen/Qwen2.5-0.5B-Instruct --n-claims 5
    python -m experiments.run_openweights --model Qwen/Qwen2.5-0.5B --base --n-claims 5

Instruct models get the tokenizer's chat template; --base renders a plain
"User: / Assistant:" transcript. Attention is read on a final forward pass over prompt
plus generated answer with output_attentions=True (eager attention), streamed layer by
layer into vp.reliance.attentional_reliance. Induction heads are located with the
standard repeated-random-sequence score so the induction-restricted reliance can be
reported next to the all-heads one.

Requires torch and transformers (see requirements-openweights.txt). Not exercised in CI.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time

import numpy as np

from vp.claims import load_claims
from vp.contexts import ARMS, SPAN_LENGTHS, build_context, rebuttal_text, check_token_alignment
from vp.reliance import attentional_reliance, token_masks
from vp.scoring import classify


def render_base(messages):
    """Plain transcript for base models; returns (text, user_ranges)."""
    parts, user_ranges, pos = [], [], 0
    for m in messages:
        tag = "User: " if m["role"] == "user" else "Assistant: "
        s = tag + m["content"] + "\n"
        if m["role"] == "user":
            user_ranges.append((pos + len(tag), pos + len(tag) + len(m["content"])))
        parts.append(s); pos += len(s)
    tail = "Assistant:"
    parts.append(tail)
    return "".join(parts), user_ranges


def render_chat(tok, messages):
    text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    user_ranges, cursor = [], 0
    for m in messages:
        if m["role"] != "user":
            continue
        i = text.find(m["content"], cursor)
        if i < 0:
            raise RuntimeError("user content not found in rendered template")
        user_ranges.append((i, i + len(m["content"]))); cursor = i + len(m["content"])
    return text, user_ranges


def span_ranges(text, spans, user_ranges):
    """Character ranges of the inserted spans: each span is searched inside its user turn
    in order, so a span string that also appears elsewhere cannot be mis-located."""
    out, ui = [], 0
    for span in spans:
        while ui < len(user_ranges):
            s, e = user_ranges[ui]; ui += 1
            j = text.find(span, s, e)
            if j >= 0:
                out.append((j, j + len(span))); break
        else:
            raise RuntimeError(f"span not found: {span!r}")
    return out


def induction_heads(model, tok, device, k, seq_len=50, seed=0):
    """Top-k (layer, head) by the repeated-random-sequence induction score."""
    import torch
    rng = np.random.default_rng(seed)
    V = len(tok)
    r = rng.integers(1000, min(V, 50000) - 1000, size=seq_len).tolist()
    bos = [tok.bos_token_id] if tok.bos_token_id is not None else []
    ids = torch.tensor([bos + r + r], device=device)
    with torch.no_grad():
        out = model(ids, output_attentions=True)
    off = len(bos)
    scores = []
    for L, att in enumerate(out.attentions):
        a = att[0].float().cpu().numpy()      # [H, T, T]
        for H in range(a.shape[0]):
            vals = [a[H, i, i - seq_len + 1] for i in range(off + seq_len + 1, off + 2 * seq_len)]
            scores.append((float(np.mean(vals)), L, H))
    scores.sort(reverse=True)
    return [(L, H) for _, L, H in scores[:k]], scores


def generate(model, tok, text, device, max_new_tokens):
    import torch
    enc = tok(text, return_tensors="pt", return_offsets_mapping=True, add_special_tokens=True)
    offsets = enc.pop("offset_mapping")[0].tolist()
    enc = {k: v.to(device) for k, v in enc.items()}
    with torch.no_grad():
        out = model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False,
                             pad_token_id=tok.pad_token_id or tok.eos_token_id)
    n_prompt = enc["input_ids"].shape[1]
    gen_ids = out[0, n_prompt:]
    answer = tok.decode(gen_ids, skip_special_tokens=True).strip()
    return answer, out, n_prompt, offsets


def attention_reliance(model, full_ids, n_prompt, offsets, spans_cr, user_cr, heads):
    import torch
    span_mask, user_mask = token_masks(offsets, spans_cr, user_cr)
    T = full_ids.shape[1]
    pad = np.zeros(T - len(offsets), bool)
    span_mask, user_mask = np.concatenate([span_mask, pad]), np.concatenate([user_mask, pad])
    q = list(range(n_prompt, T))
    with torch.no_grad():
        out = model(full_ids, output_attentions=True)
    layers = (att[0].float().cpu().numpy() for att in out.attentions)
    allh = attentional_reliance(layers, span_mask, user_mask, q)
    layers = (att[0].float().cpu().numpy() for att in out.attentions)
    ind = attentional_reliance(layers, span_mask, user_mask, q, heads=heads)
    return {"all_heads": allh, "induction_heads": ind}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--base", action="store_true", help="plain transcript, no chat template")
    ap.add_argument("--bank", default="syceval_computational")
    ap.add_argument("--n-claims", type=int, default=10)
    ap.add_argument("--claim-seed", type=int, default=0)
    ap.add_argument("--densities", default="0,0.25,0.5,0.75,0.9,1.0")
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--seeds", type=int, default=1)
    ap.add_argument("--span-lengths", default="medium", help=f"comma list from {SPAN_LENGTHS}")
    ap.add_argument("--n-turns", type=int, default=8)
    ap.add_argument("--max-new-tokens", type=int, default=64)
    ap.add_argument("--k-heads", type=int, default=8)
    ap.add_argument("--device", default=None)
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=getattr(torch, args.dtype), attn_implementation="eager").to(device).eval()
    bad = check_token_alignment(tok, tol=1)
    if bad:
        print(f"WARNING: span arms not token-aligned under this tokenizer: {bad}", file=sys.stderr)
    heads, _ = induction_heads(model, tok, device, args.k_heads)
    print(f"induction heads: {heads}", file=sys.stderr)

    claims = load_claims(args.bank, n=args.n_claims, seed=args.claim_seed)
    densities = [float(d) for d in args.densities.split(",")]
    arms = args.arms.split(",")
    lengths = args.span_lengths.split(",")
    tag = args.model.replace("/", "_") + ("_base" if args.base else "")
    out = args.out or f"results/ow_{tag}_{args.bank}.jsonl"
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    render = (lambda m: render_base(m)) if args.base else (lambda m: render_chat(tok, m))

    with open(out, "a") as fh:
        for claim in claims:
            for d in densities:
              for L in (lengths if d > 0 else lengths[:1]):
                for arm in (arms if d > 0 else arms[:2]):   # density 0: noise floor, see run_api
                    for seed in range(args.seeds):
                        t = build_context(claim, arm, d, seed, n_turns=args.n_turns, span_length=L)
                        wrong = claim.wrong_answer()
                        text, user_cr = render(t.messages)
                        spans_cr = span_ranges(text, t.spans, user_cr)
                        a1, full, n_prompt, offsets = generate(model, tok, text, device, args.max_new_tokens)
                        c1 = classify(a1, claim.correct_answer, wrong)
                        rel = attention_reliance(model, full, n_prompt, offsets, spans_cr, user_cr, heads) \
                            if t.n_spans else None
                        target = wrong if c1 != "wrong" else claim.correct_answer
                        msgs = t.messages + [{"role": "assistant", "content": a1},
                                             {"role": "user", "content": rebuttal_text(target, t.instruction)}]
                        text2, _ = render(msgs)
                        a2, _, _, _ = generate(model, tok, text2, device, args.max_new_tokens)
                        c2 = classify(a2, claim.correct_answer, wrong)
                        rec = dict(model=tag, claim_id=claim.id, arm=arm, density=d, seed=seed,
                                   span_length=L, extra_words=t.extra_words,
                                   usage1=dict(input=n_prompt, output=int(full.shape[1] - n_prompt)),
                                   n_turns=args.n_turns, n_spans=t.n_spans, refused=False,
                                   first_text=a1, first_class=c1, second_text=a2, second_class=c2,
                                   rebuttal_target="wrong" if target == wrong else "correct",
                                   cave=(c1 == "correct" and c2 == "wrong"),
                                   progressive=(c1 == "wrong" and c2 == "correct"),
                                   attentional=rel, induction_heads=heads, ts=time.time())
                        fh.write(json.dumps(rec, ensure_ascii=False) + "\n"); fh.flush()
                        print(f"{claim.id[:40]:40s} {arm:8s} d={d:4.2f} first={c1:9s} second={c2:9s} "
                              f"lift={rel['all_heads']['lift'] if rel else float('nan'):.2f}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
