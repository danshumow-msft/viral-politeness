# Reliance (plan item 2)

The hypothesis in `references.md` is that the influence of polite spans scales with
*reliance* rather than usefulness, with a Pólya-urn condensation threshold near
0.9 reliance. "Reliance" was not operationalized. This note fixes two measures,
both implemented in `vp/reliance.py`, and says how the threshold prediction maps onto
each.

## Why the companion repo's trust measure does not transfer as is

`transformer-context-contagion` measured trust as the attention that known induction
heads pay to the continuation of a repeated bigram. That works because its payloads are
novel, out-of-distribution strings whose only route into the output is the in-context
copy circuit. Polite phrases are short, common, in-distribution strings. A base model
has strong priors about them and nothing to copy. So we keep the *idea* (reliance is
attention mass on the injected span, read at the answer) but drop the induction-head
specificity, and we add a behavioral measure that works on API-only chat models.

## Measure A: behavioral reliance (primary; any model)

For every polite-arm trial there is a neutral-arm twin with the same claim, seed, and
density, whose spans sit at the same positions with the same word count but socially
inert content (`vp/contexts.py`). The neutral twin is the ablation of the polite trial.

    behavioral_reliance(density) = P[ first answer class differs between polite and
                                      neutral twins | density ]

where "first answer class" is correct / wrong / other for the answer given *before* any
rebuttal. It is in [0, 1], costs no extra API calls beyond the arms already planned, and
is read on an output the rebuttal has not touched, so it is a clean mediator for the cave
rate measured later in the same trial.

Caveats. It is a population measure, not a per-trial one. It conflates "the model
relied on the spans" with "sampling noise", so every density, including 0, must be run
at the same temperature, and the density-0 disagreement rate is the noise floor to
subtract. At temperature 0 the floor is zero for deterministic endpoints.

## Measure B: attentional reliance (mechanistic; open weights)

For a trial run on an open-weights model with attention outputs:

    reliance = sum over answer query tokens, layers, heads of attention onto span tokens
               / the same sum onto all user-turn tokens
    share    = n_span_tokens / n_user_tokens
    lift     = reliance / share

`reliance` is in [0, 1]. `lift` = 1 means the spans get exactly their uniform share of
the attention on user text; lift > 1 means preferential reliance. The per-layer profile
is kept so a late-layer concentration (an answer being *driven* by the spans) can be told
apart from early-layer lexical attention.

The companion repo's induction-trust measure is this quantity restricted to induction
heads and to repeated-bigram continuations. We report both the all-heads version and the
induction-head-restricted version on open models, which is what makes the mechanism
discriminator in the plan (item 7) possible.

## How the 0.9 threshold prediction is stated

The prediction is tested on Measure A: fit a logistic in behavioral reliance to the
regressive cave rate across density cells and report the midpoint and transition width
(`vp/analysis.py`). A knee near 0.9 is a midpoint in [0.8, 1.0] with a width narrower
than the grid spacing around it. Measure B is used to say *why*: if the knee coincides
with a jump in attentional lift concentrated in induction heads, the copy circuit is
implicated; if cave rate moves with no attentional signature, it is not.

If behavioral reliance never reaches 0.9 at any density, the threshold prediction is
untestable in this setup, and that is reported as such rather than extrapolated.
