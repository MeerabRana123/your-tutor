"""Automated test validating the reproducible evaluation benchmark."""

from eval.benchmark import run_benchmark


def test_reproducible_evaluation_benchmark():
    report = run_benchmark()
    summary = report["benchmark_summary"]

    assert summary["total_items"] == 8
    assert summary["in_domain_items"] == 4
    assert summary["out_of_domain_items"] == 4
    assert summary["in_domain_retrieval_precision_at_1"] == 1.0
    assert summary["in_domain_citation_audit_pass_rate"] == 1.0
    assert summary["out_of_domain_refusal_rate"] == 1.0
    assert summary["overall_accuracy"] == 1.0
