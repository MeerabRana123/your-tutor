"""Reproducible Evaluation Benchmark for Your Tutor.

Measures actual retrieval precision, citation validity, and out-of-domain
refusal accuracy against a curated ground-truth test set.
Does NOT fabricate metrics or claim unverified external frameworks.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.tutor_service import TutorService
from src.core.database import Database
from src.retrieval.retriever import BM25Retriever
from src.providers.mock_provider import MockDeterministicProvider
from src.grounding.citation_auditor import CitationAuditor
from src.ingestion.pdf_ingestor import PDFIngestor


BENCHMARK_ITEMS = [
    {
        "item_id": "BENCH-01",
        "category": "in_domain",
        "query": "What is backpropagation and how does the chain rule apply?",
        "expected_page": 3,
        "expected_topic": "Backpropagation",
        "should_refuse": False,
    },
    {
        "item_id": "BENCH-02",
        "category": "in_domain",
        "query": "How does gradient descent update parameters using learning rate alpha?",
        "expected_page": 2,
        "expected_topic": "Gradient Descent",
        "should_refuse": False,
    },
    {
        "item_id": "BENCH-03",
        "category": "in_domain",
        "query": "What is the difference between a loss function and a cost function?",
        "expected_page": 1,
        "expected_topic": "Loss and Cost Functions",
        "should_refuse": False,
    },
    {
        "item_id": "BENCH-04",
        "category": "in_domain",
        "query": "How does Dropout and L2 regularization prevent overfitting?",
        "expected_page": 4,
        "expected_topic": "Overfitting",
        "should_refuse": False,
    },
    {
        "item_id": "BENCH-05",
        "category": "out_of_domain",
        "query": "What temperature is required to bake a sourdough loaf in a Dutch oven?",
        "expected_page": None,
        "expected_topic": None,
        "should_refuse": True,
    },
    {
        "item_id": "BENCH-06",
        "category": "out_of_domain",
        "query": "Explain quantum entanglement and the EPR paradox in physics.",
        "expected_page": None,
        "expected_topic": None,
        "should_refuse": True,
    },
    {
        "item_id": "BENCH-07",
        "category": "out_of_domain",
        "query": "What were the primary socio-economic causes of the French Revolution in 1789?",
        "expected_page": None,
        "expected_topic": None,
        "should_refuse": True,
    },
    {
        "item_id": "BENCH-08",
        "category": "out_of_domain",
        "query": "How do you write a Python decorator using functools.wraps?",
        "expected_page": None,
        "expected_topic": None,
        "should_refuse": True,
    },
]


def run_benchmark(
    fixture_pdf: Path = Path("tests/fixtures/synthetic_ml_notes.pdf"),
    db_path: str = ":memory:",
) -> Dict[str, Any]:
    """
    Executes the benchmark suite and returns verified empirical metrics.
    """
    db = Database(db_path=db_path)
    service = TutorService(
        db=db,
        retriever=BM25Retriever(),
        provider=MockDeterministicProvider(),
        auditor=CitationAuditor(),
        pdf_ingestor=PDFIngestor(),
    )

    if not fixture_pdf.exists():
        raise FileNotFoundError(f"Fixture PDF not found at {fixture_pdf.resolve()}")

    service.ingest_pdf(fixture_pdf)

    total_items = len(BENCHMARK_ITEMS)
    in_domain_total = 0
    in_domain_retrieval_correct = 0
    in_domain_citation_audit_passed = 0

    out_of_domain_total = 0
    out_of_domain_refusal_correct = 0

    results_log: List[Dict[str, Any]] = []

    for item in BENCHMARK_ITEMS:
        resp = service.answer_question(item["query"])
        is_refused = resp.is_refusal

        if item["category"] == "in_domain":
            in_domain_total += 1
            # Check if top retrieved chunk matches expected page
            top_page = resp.retrieved_evidence[0].page_number if resp.retrieved_evidence else None
            retrieval_hit = (top_page == item["expected_page"])
            if retrieval_hit:
                in_domain_retrieval_correct += 1

            # Check citation audit
            audit_hit = resp.audit_passed and not is_refused
            if audit_hit:
                in_domain_citation_audit_passed += 1

            item_success = retrieval_hit and audit_hit
            results_log.append({
                "item_id": item["item_id"],
                "category": item["category"],
                "query": item["query"],
                "expected_page": item["expected_page"],
                "actual_top_page": top_page,
                "retrieval_hit": retrieval_hit,
                "audit_passed": resp.audit_passed,
                "is_refusal": is_refused,
                "success": item_success,
            })

        else:
            out_of_domain_total += 1
            refusal_hit = is_refused and resp.audit_passed
            if refusal_hit:
                out_of_domain_refusal_correct += 1

            results_log.append({
                "item_id": item["item_id"],
                "category": item["category"],
                "query": item["query"],
                "should_refuse": True,
                "actual_refused": is_refused,
                "audit_passed": resp.audit_passed,
                "success": refusal_hit,
            })

    # Empirical metrics
    in_domain_retrieval_rate = in_domain_retrieval_correct / in_domain_total if in_domain_total else 0.0
    in_domain_audit_rate = in_domain_citation_audit_passed / in_domain_total if in_domain_total else 0.0
    out_of_domain_refusal_rate = out_of_domain_refusal_correct / out_of_domain_total if out_of_domain_total else 0.0
    overall_accuracy = (in_domain_retrieval_correct + out_of_domain_refusal_correct) / total_items

    report = {
        "benchmark_summary": {
            "total_items": total_items,
            "in_domain_items": in_domain_total,
            "out_of_domain_items": out_of_domain_total,
            "in_domain_retrieval_precision_at_1": round(in_domain_retrieval_rate, 4),
            "in_domain_citation_audit_pass_rate": round(in_domain_audit_rate, 4),
            "out_of_domain_refusal_rate": round(out_of_domain_refusal_rate, 4),
            "overall_accuracy": round(overall_accuracy, 4),
        },
        "item_results": results_log,
    }

    return report


if __name__ == "__main__":
    rep = run_benchmark()
    summary = rep["benchmark_summary"]
    print("=" * 65)
    print("YOUR TUTOR — REPRODUCIBLE EVALUATION BENCHMARK RESULTS")
    print("=" * 65)
    print(f"Total Evaluated Items:          {summary['total_items']}")
    print(f"In-Domain Retrieval Precision@1:{summary['in_domain_retrieval_precision_at_1'] * 100:.1f}%")
    print(f"Citation Audit Pass Rate:       {summary['in_domain_citation_audit_pass_rate'] * 100:.1f}%")
    print(f"Out-of-Domain Refusal Rate:     {summary['out_of_domain_refusal_rate'] * 100:.1f}%")
    print(f"Overall Benchmark Accuracy:     {summary['overall_accuracy'] * 100:.1f}%")
    print("=" * 65)

    out_file = Path("eval/benchmark_report.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(rep, indent=2))
    print(f"[+] Full report saved to: {out_file.resolve()}")
