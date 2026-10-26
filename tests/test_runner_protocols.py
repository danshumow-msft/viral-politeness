from types import SimpleNamespace

import pytest

from experiments.run_api import Runner, main as api_main
from experiments.run_openweights import main as openweights_main
from vp.claims import Claim, load_claims
from vp.io import write_jsonl
from vp.records import validate_records
from vp.scoring import scoring_protocol


def _response(text, model="served", stop="end_turn"):
    return SimpleNamespace(model=model, stop_reason=stop,
                           content=[SimpleNamespace(type="text", text=text)],
                           usage=SimpleNamespace(input_tokens=100, output_tokens=10))


def test_api_runner_records_generation_scoring_layout_and_both_served_models():
    answers = iter([_response("7"), _response("5")])
    client = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: next(answers)))
    runner = Runner(client, "requested", "medium", 64, bank="test-bank")
    claim = Claim("c", "Question?", "7", ("5",), "Computational")
    rec = runner.run_trial(claim, "polite", 0.5, 0, 8)
    assert rec["protocol"] == runner.protocol(8)
    assert rec["scoring_protocol"] == scoring_protocol()
    assert rec["protocol"]["bank"] == "test-bank" and rec["protocol"]["max_tokens"] == 64
    assert rec["served_model"] == rec["served_model2"] == "served"
    assert len(rec["phrase_indices"]) == len(rec["span_positions"]) == 4
    assert rec["cave"] is True
    assert validate_records([rec])["requested"]["unverified_fields"] == []


def test_api_runner_rejects_a_model_switch_between_calls():
    answers = iter([_response("7", "a"), _response("5", "b")])
    client = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: next(answers)))
    runner = Runner(client, "requested", "medium", 64)
    claim = Claim("c", "Question?", "7", ("5",), "Computational")
    with pytest.raises(ValueError, match="served_model"):
        runner.run_trial(claim, "polite", 0.5, 0, 8)


def _existing(model, protocol=None, scoring=None):
    c = load_claims(n=1)[0]
    r = dict(model=model, claim_id=c.id, arm="polite", density=0.5, seed=0, span_length="medium")
    if protocol is not None:
        r["protocol"] = protocol
    if scoring is not None:
        r["scoring_protocol"] = scoring
    return r


def test_api_resume_checks_legacy_protocol_before_importing_anthropic(tmp_path):
    out = tmp_path / "old.jsonl"
    write_jsonl(out, [_existing("claude-opus-5-5")])
    with pytest.raises(ValueError, match="unverified protocol"):
        api_main(["--n-claims", "1", "--densities", "0.5", "--arms", "polite", "--out", str(out)])


def test_api_completed_run_needs_no_client_or_more_calls(tmp_path):
    out = tmp_path / "complete.jsonl.gz"
    runner = Runner(None, "claude-opus-5-5", "medium", 2048, bank="syceval_computational")
    write_jsonl(out, [_existing(runner.model, runner.protocol(8), runner.scoring_protocol())])
    assert api_main(["--n-claims", "1", "--densities", "0.5", "--arms", "polite",
                     "--judge", "none", "--out", str(out)]) == 0


def test_duplicate_requested_grid_is_rejected_before_calls():
    with pytest.raises(ValueError, match="duplicate"):
        api_main(["--dry-run", "--n-claims", "1", "--densities", "0.5", "--arms", "polite,polite"])


@pytest.mark.parametrize("runner,args", [
    (api_main, ["--dry-run", "--n-claims", "0"]),
    (openweights_main, ["--model", "Demo/Small", "--seeds", "0"]),
])
def test_empty_requested_grid_is_not_a_successful_completed_run(runner, args):
    with pytest.raises(ValueError, match="at least one trial"):
        runner(args)


def test_openweights_resume_checks_before_importing_or_downloading_weights(tmp_path):
    out = tmp_path / "old.jsonl"
    write_jsonl(out, [_existing("Demo_Small")])
    with pytest.raises(ValueError, match="unverified protocol"):
        openweights_main(["--model", "Demo/Small", "--n-claims", "1", "--densities", "0.5",
                          "--arms", "polite", "--out", str(out)])


def test_openweights_completed_run_needs_no_torch_or_weight_download(tmp_path):
    out = tmp_path / "complete.jsonl"
    protocol = dict(version=1, runner="openweights", bank="syceval_computational", context_version=1,
                    rebuttal="syceval-simple-v1", n_turns=8, base=False, max_new_tokens=64,
                    sampling="greedy", dtype="bfloat16", k_heads=8, checkpoint="Demo/Small")
    write_jsonl(out, [_existing("Demo_Small", protocol, scoring_protocol())])
    assert openweights_main(["--model", "Demo/Small", "--n-claims", "1", "--densities", "0.5",
                             "--arms", "polite", "--out", str(out)]) == 0


def test_judge_protocol_requires_reproducible_configuration():
    with pytest.raises(ValueError, match="requires"):
        scoring_protocol(judge_model="judge")
    runner = Runner(None, "m", "medium", 64, judge_model="judge")
    profile = runner.scoring_protocol()
    assert profile["judge_model"] == "judge" and len(profile["judge_prompt_sha256"]) == 64
    assert profile["judge_effort"] == "low" and profile["judge_max_tokens"] == 4096
