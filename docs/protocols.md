# Trial identity, protocol compatibility, and pair coverage

Implemented 2026-10-25 as the second offline M1/M2 slice. These checks protect
aggregation and resumed runs; they do not establish a valid mediator, validate
scorer correctness, or authorize new data collection.

## Identity and pooling

[Shared record validation](../vp/records.py) identifies a trial by:

```text
(model, claim_id, arm, density, seed, span_length)
```

Model, claim, and arm identifiers must be nonempty strings. Density must be finite
and in [0, 1]; seed must be a nonnegative integer. Missing `span_length` alone has the
documented legacy default `medium`. Numerically identical densities such as `0` and
`0.0` have the same identity. Missing key dimensions are not wildcards.

Duplicate full identities raise a `ValueError`, even if their data agree or one
record is refused. This prevents accidental double counting and silent loss of
ambiguous pairs. Reanalyze an original or derived version, not both at once.

Before pooling records for a model, validate equality of any recorded:

- generation `protocol` and `scoring_protocol` objects;
- turn count, effort, served-model identity, bank, token limit, judge model,
  protocol/scorer version, and sampling metadata.

Known-versus-absent values are incompatible, not matching defaults. Different
settings under the same model must be analyzed in separate invocations rather than
renaming the model to conceal the difference. Different model groups may legitimately
have different configurations because their outcome cells remain separate.

Correct and wrong reference answers must agree within each model/claim group.
Recorded span counts, positions, and phrase indices must agree across all arms with
the same claim, seed, density, and length, including the rude/social controls. When
both served-model fields are recorded, a between-call switch is rejected.

## Historical metadata is incomplete

The six committed runs have consistent recorded effort, turn count, first served
model, and span layouts, with no duplicate keys. They do not record full generation
or scoring protocol objects. Validation can check what they contain, not recover
missing judge settings, checkpoint revisions, sampling details, or a full manifest.

Each summary reports per-model `protocols.metadata` and `unverified_fields`; the CLI
also prints unverified metadata. Consistently absent legacy fields remain unknown.
Compatibility of recorded values is **not** certification that every unrecorded
parameter matched. Do not invent historical metadata to pass a check.

## Pairing and coverage

Polite/neutral twins match on the full identity without `arm`. The shared key
normalizes the legacy medium-length default without mutating the input records.

Duplicate keys and incompatible metadata raise errors before aggregation. A missing
twin is excluded, as approved by the owner, with explicit coverage counts:

| Field | Meaning |
|---|---|
| `n_matched` | Observed keys containing both arms, including later exclusions |
| `n_missing_a`, `n_missing_b` | Observed keys missing the first/second requested arm (polite/neutral by default) |
| `n_refused` | Matched pairs with either twin refused |
| `n_unscorable` | Remaining matched pairs with an unavailable comparison value, including endpoint-ineligible or unclassified outcome comparisons |
| `n_pairs` | Matched, non-refused pairs with both comparison values |
| `n_differ` | Scorable pairs whose comparison values differ |
| `reliance` | `n_differ / n_pairs`, or null with no scorable pairs |
| `pair_coverage` | `n_pairs / (n_matched + n_missing_a + n_missing_b)` |
| `sensitivity` | Best/worst disagreement assignments on observed keys with unavailable comparisons; not a confidence interval |

These counts describe **observed** keys. They cannot detect a planned key absent
from both arms; that requires a full expected-run manifest, still M4 work.
The [sensitivity note](sensitivity.md) defines the bounds and their fixed-label
assumption; they do not turn this statistic into causal reliance.

For first-answer disagreement, legacy `correct`, `wrong`, `other`, and `ambiguous`
remain valid comparison categories. Two missing classes no longer count as agreement.
Invalid classes raise errors; boolean-outcome comparisons require actual booleans.
Refusals are checked before comparing fields.

For `field="cave"` or `field="progressive"`, a stored boolean is not sufficient:
both twins must satisfy the endpoint's first-class/rebuttal eligibility and have a
classifiable second answer. These comparisons reuse the same validation as the
primary cell table; unavailable outcomes are excluded, and inconsistent/missing
flags on otherwise scorable outcomes raise an error. This does not change default
first-answer class disagreement.

`behavioral_reliance` exposes the diagnostics per requested grouping. The lower-level
`pair_arms` returns complete pairs and warns when keys have missing twins; callers
must still decide which responses are scorable. Direct grouping across multiple
models or span lengths must name those dimensions to avoid silent pooling.

On the unchanged main-run records, all seven densities have 200 matched pairs.
Density 0.9 has 2 refused pairs, leaving 198 comparison pairs; the other densities
have 200. The medical pilot has one refused pair. Previously reported first-class
disagreement values on the valid pairs are unchanged.

## New records and resume preflight

Both runners now record additive version-1 `protocol` and `scoring_protocol` objects.
The API protocol records runner/bank/context/rebuttal versions, turn count, effort,
token limit, and provider-default sampling. Open weights records its requested
checkpoint, base/chat mode, greedy decoding, generation limit, dtype, and attention
head count. Scoring metadata identifies the heuristic version and, when enabled,
the judge model, prompt hash, effort, token cap, and hand-review policy.

API records also retain the second served-model identity and phrase indices.
Open-weights records retain references, served checkpoint, positions, and phrase
indices. These are incremental provenance improvements, not the complete M4 manifest:
rendered-context hashes, immutable model/tokenizer revisions, expected trial schedules,
and tokenizer-level matching still require follow-up.

Before importing a model client or loading weights, both runners validate requested
trial identities and existing output records. A resume requires exact agreement with
the requested generation and scoring configurations. Missing legacy protocol objects
cannot be safely resumed under current code: use a new output file. Duplicate grid
entries also fail before execution. Open weights skips previously completed compatible
trials instead of blindly appending duplicates.

Rescoring validates input identity, compatibility, and any secondary source bindings
before a judge client is created. Both analysis and rescoring reject an output path
that resolves to an input record file. Original gzip records, historical summaries,
and hand-review evidence must remain untouched.
