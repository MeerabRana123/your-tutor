"""Unit test suite for Bayesian Knowledge Tracing (BKT) engine and persistence.

Validates:
1. Mathematical updates for correct answers (posterior increases)
2. Mathematical updates for incorrect answers (posterior decreases)
3. Application of learning transition P(T)
4. Parameter validation and rejection of degenerate parameters
5. Numerical stability under long sequences without underflow/overflow
6. SQLite persistence and recall of student topic mastery
"""

import pytest
from src.bkt.engine import BKTEngine, BKTParameterError
from src.core.database import Database


def test_bkt_parameter_validation():
    # Valid parameters initialize cleanly
    engine = BKTEngine(p_l0=0.20, p_t=0.15, p_g=0.20, p_s=0.10)
    assert engine.p_l0 == 0.20

    # Probability out of bounds (< 0 or > 1)
    with pytest.raises(BKTParameterError):
        BKTEngine(p_l0=-0.1)

    with pytest.raises(BKTParameterError):
        BKTEngine(p_t=1.5)

    # Degenerate parameter sum: p_g + p_s >= 0.95
    with pytest.raises(BKTParameterError):
        BKTEngine(p_g=0.50, p_s=0.50)


def test_bkt_correct_answer_increases_mastery():
    engine = BKTEngine(p_l0=0.20, p_t=0.15, p_g=0.20, p_s=0.10)
    prior = 0.20

    posterior, next_prior = engine.update_mastery(prior_p_l=prior, is_correct=True)

    # Correct observation must strictly increase mastery estimate
    assert posterior > prior, f"Posterior {posterior} must be greater than prior {prior}"
    # Next trial prior must incorporate transition P(T) and thus be >= posterior
    assert next_prior >= posterior
    assert round(posterior, 2) == 0.53
    assert round(next_prior, 2) == 0.60


def test_bkt_incorrect_answer_decreases_mastery():
    engine = BKTEngine(p_l0=0.50, p_t=0.15, p_g=0.20, p_s=0.10)
    prior = 0.50

    posterior, next_prior = engine.update_mastery(prior_p_l=prior, is_correct=False)

    # Incorrect observation must strictly decrease intermediate posterior
    assert posterior < prior, f"Posterior {posterior} must be less than prior {prior}"
    assert posterior < 0.15


def test_bkt_numerical_stability_long_sequence():
    engine = BKTEngine()
    mastery = 0.20

    # 20 consecutive correct answers should smoothly approach 1.0 without NaN/overflow
    for _ in range(20):
        _, mastery = engine.update_mastery(mastery, is_correct=True)
        assert 0.0 < mastery < 1.0

    assert mastery > 0.99

    # 20 consecutive incorrect answers should drop towards baseline transition without zero division
    for _ in range(20):
        _, mastery = engine.update_mastery(mastery, is_correct=False)
        assert 0.0 < mastery < 1.0

    assert mastery < 0.40


def test_bkt_sqlite_persistence(tmp_path):
    db_file = tmp_path / "bkt_test.db"
    db = Database(db_path=str(db_file))

    student_id = "student_alice"
    topic = "Backpropagation and the Chain Rule"

    # Initial state should be None
    assert db.get_topic_mastery(student_id, topic) is None

    # Save first correct attempt
    db.save_topic_mastery(student_id, topic, p_mastery=0.60, is_correct=True)
    assert db.get_topic_mastery(student_id, topic) == 0.60

    details = db.get_topic_mastery_details(student_id, topic)
    assert details["total_attempts"] == 1
    assert details["correct_attempts"] == 1

    # Save second incorrect attempt
    db.save_topic_mastery(student_id, topic, p_mastery=0.45, is_correct=False)
    assert db.get_topic_mastery(student_id, topic) == 0.45

    details2 = db.get_topic_mastery_details(student_id, topic)
    assert details2["total_attempts"] == 2
    assert details2["correct_attempts"] == 1

    # Check all masteries mapping
    all_m = db.get_all_topic_masteries(student_id)
    assert topic in all_m
    assert all_m[topic] == 0.45
