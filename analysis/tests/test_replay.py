import json

import config
import replay


def test_replay_totals_reconcile_with_member_key():
    m = replay.main()
    assert m["disclaimer"] == config.DISCLAIMER
    assert m["key"]["reconciles_with_replay"]
    assert abs(m["scam"]["dollars_attempted"] - m["key"]["dollars_attempted"]) < 0.01
    assert m["payments_initiated"] == 764
    df = replay.pd.read_csv(replay.OUT / "member_summary.csv")
    assert abs(df.scam_dollars_attempted.sum() - df.key_dollars_attempted.sum()) < 0.01
    assert (df.scam_dollars_attempted - df.key_dollars_attempted).abs().max() < 0.01


def test_outputs_carry_disclaimer_and_callouts():
    replay.main()
    met = json.loads((replay.OUT / "metrics.json").read_text())
    assert met["callouts"]["miss"]["payment_id"] and met["callouts"]["false_positive"]["payment_id"]
    assert config.DISCLAIMER in (replay.OUT / "walkthroughs.md").read_text()
    for f in ("decisions.csv", "member_summary.csv"):
        df = replay.pd.read_csv(replay.OUT / f)
        assert (df.disclaimer == config.DISCLAIMER).all()


def test_cancel_rate_sensitivity_is_monotonic():
    by = replay.main()["scam"]["expected_dollars_stopped_by_cancel_rate"]
    assert by["0.5"] <= by["0.8"] <= by["1.0"]
