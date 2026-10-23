"""
tests/test_experiments.py

Comprehensive tests for Phase 5 Experiment Engine:
- Welch's two-sample t-test evaluator (evaluator.py)
- Deterministic hypothesis proposal (experiment_agent.py)
- API endpoints: /experiments/propose, /experiments, /experiments/{id}/assign-posts, /experiments/{id}/evaluate
- Strategy feedback loop: Conclusive experiment updates creator's strategic priorities
"""

from datetime import datetime, timezone, timedelta
from backend.experiments.evaluator import evaluate_experiment_metrics
from backend.agents.experiment_agent import run_experiment_agent


def test_evaluator_insufficient_sample_size():
    # Min sample size is 3
    a = [2.0, 2.5]
    b = [3.0, 3.5]
    result = evaluate_experiment_metrics(a, b, min_sample_size=3)

    assert result["status"] == "completed_inconclusive"
    assert result["is_significant"] is False
    assert result["winner"] is None
    assert result["p_value"] == 1.0
    assert "Sample size too small" in result["summary"]


def test_evaluator_statistically_significant():
    # Variant B clearly outperforms Variant A
    # A: ~2.0% ER, B: ~6.0% ER
    a = [1.9, 2.0, 2.1, 1.8, 2.2]
    b = [5.8, 6.1, 5.9, 6.2, 6.0]
    result = evaluate_experiment_metrics(a, b, alpha=0.05)

    assert result["status"] == "completed_conclusive"
    assert result["is_significant"] is True
    assert result["winner"] == "variant_b"
    assert result["p_value"] < 0.01
    assert result["confidence_pct"] > 99.0
    assert result["relative_difference_pct"] > 100.0
    assert "Winner: VARIANT_B" in result["summary"]


def test_evaluator_inconclusive_no_difference():
    # Two identical/similar sets with overlapping distributions
    a = [3.1, 3.2, 3.0, 3.1, 3.3]
    b = [3.15, 3.1, 3.25, 3.05, 3.2]
    result = evaluate_experiment_metrics(a, b, alpha=0.05)

    assert result["status"] == "completed_inconclusive"
    assert result["is_significant"] is False
    assert result["winner"] is None
    assert result["p_value"] > 0.05


def test_evaluator_zero_variance_cases():
    # Identical values
    a_ident = [4.0, 4.0, 4.0]
    b_ident = [4.0, 4.0, 4.0]
    res_ident = evaluate_experiment_metrics(a_ident, b_ident)
    assert res_ident["status"] == "completed_inconclusive"
    assert res_ident["is_significant"] is False

    # Distinct values, zero variance
    a_dist = [2.0, 2.0, 2.0]
    b_dist = [5.0, 5.0, 5.0]
    res_dist = evaluate_experiment_metrics(a_dist, b_dist)
    assert res_dist["status"] == "completed_conclusive"
    assert res_dist["winner"] == "variant_b"
    assert res_dist["is_significant"] is True


def test_experiment_agent_proposals():
    # Reel proposal
    reel_prop = run_experiment_agent(
        creator_id="creator_exp_test",
        top_format="reel",
        avg_er=4.2,
        best_window="Wednesday 18:00 - 21:00 UTC",
        niche="Finance & Investing",
    )
    assert "Reel Hook Retention" in reel_prop["title"]
    assert "contrarian" in reel_prop["hypothesis"].lower()
    assert reel_prop["metric_target"] == "engagement_rate"
    assert "Direct How-To Hook" in reel_prop["variant_a"]["name"]
    assert "Contrarian Myth Hook" in reel_prop["variant_b"]["name"]

    # Carousel proposal
    car_prop = run_experiment_agent(
        creator_id="creator_exp_test",
        top_format="carousel",
        avg_er=3.5,
        best_window="Sunday 12:00 - 15:00 UTC",
        niche="Design",
    )
    assert "Carousel Value Delivery" in car_prop["title"]
    assert "checklist" in car_prop["variant_a"]["name"].lower()
    assert "flowchart" in car_prop["variant_b"]["name"].lower()

    # Image/Timing proposal
    time_prop = run_experiment_agent(
        creator_id="creator_exp_test",
        top_format="image",
        avg_er=2.1,
        best_window="Monday 09:00 - 12:00 UTC",
    )
    assert "Publishing Timing Test" in time_prop["title"]
    assert time_prop["metric_target"] == "reach"


def test_experiment_api_lifecycle_and_strategy_feedback_loop(client):
    now = datetime.now(timezone.utc)
    creator_id = "creator_exp_e2e"

    # 1. Ingest 6 posts for creator: 3 control (low ER) and 3 treatment (high ER)
    payload = {
        "creator_id": creator_id,
        "raw_data": [
            # Variant A posts (control: low ER)
            {"post_id": "exp_a1", "date": (now - timedelta(days=6)).isoformat(), "type": "reel", "reach": 1000, "likes": 20, "comments": 2},
            {"post_id": "exp_a2", "date": (now - timedelta(days=5)).isoformat(), "type": "reel", "reach": 1000, "likes": 19, "comments": 1},
            {"post_id": "exp_a3", "date": (now - timedelta(days=4)).isoformat(), "type": "reel", "reach": 1000, "likes": 21, "comments": 2},
            # Variant B posts (treatment: high ER)
            {"post_id": "exp_b1", "date": (now - timedelta(days=3)).isoformat(), "type": "reel", "reach": 1000, "likes": 65, "comments": 5},
            {"post_id": "exp_b2", "date": (now - timedelta(days=2)).isoformat(), "type": "reel", "reach": 1000, "likes": 62, "comments": 4},
            {"post_id": "exp_b3", "date": (now - timedelta(days=1)).isoformat(), "type": "reel", "reach": 1000, "likes": 68, "comments": 6},
        ],
    }
    ingest_res = client.post("/data/ingest", json=payload)
    assert ingest_res.status_code == 200

    # 2. Generate a baseline Strategy for creator so feedback loop has a target
    strat_res = client.post("/strategy/generate", json={"creator_id": creator_id, "niche": "Tech"})
    assert strat_res.status_code == 200
    initial_priorities = strat_res.json()["strategic_priorities"]

    # 3. Propose experiment via POST /experiments/propose
    prop_res = client.post("/experiments/propose", json={"creator_id": creator_id, "niche": "Tech"})
    assert prop_res.status_code == 200
    exp_data = prop_res.json()
    assert exp_data["creator_id"] == creator_id
    assert exp_data["status"] == "proposed"
    assert "variant_a" in exp_data
    assert "variant_b" in exp_data
    exp_id = exp_data["id"]

    # 4. Inspect single experiment via GET /experiments/{id}
    get_res = client.get(f"/experiments/{exp_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == exp_id

    # 5. List experiments via GET /experiments
    list_res = client.get(f"/experiments?creator_id={creator_id}")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 6. Attempt evaluate before assigning posts -> should fail with 400
    eval_fail = client.post(f"/experiments/{exp_id}/evaluate")
    assert eval_fail.status_code == 400

    # 7. Assign posts via POST /experiments/{id}/assign-posts
    assign_payload = {
        "variant_a_post_ids": ["exp_a1", "exp_a2", "exp_a3"],
        "variant_b_post_ids": ["exp_b1", "exp_b2", "exp_b3"],
    }
    assign_res = client.post(f"/experiments/{exp_id}/assign-posts", json=assign_payload)
    assert assign_res.status_code == 200
    assert assign_res.json()["status"] == "active"

    # 8. Evaluate experiment via POST /experiments/{id}/evaluate
    eval_res = client.post(f"/experiments/{exp_id}/evaluate?alpha=0.05")
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["status"] == "completed_conclusive"
    eval_result = eval_data["evaluation_result"]
    assert eval_result["is_significant"] is True
    assert eval_result["winner"] == "variant_b"
    assert eval_result["confidence_pct"] >= 95.0

    # 9. Feedback Loop Verification:
    # Verify winning insight was prepended to the creator's latest strategy
    strat_check = client.get(f"/strategy/{creator_id}")
    assert strat_check.status_code == 200
    updated_priorities = strat_check.json()["strategic_priorities"]
    assert len(updated_priorities) == len(initial_priorities) + 1
    assert "Validated via Experiment" in updated_priorities[0]
    assert "outperformed" in updated_priorities[0]
