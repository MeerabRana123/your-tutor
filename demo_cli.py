"""Command-Line Interface (CLI) demonstration for Your Tutor — Milestone 1.

Allows ingesting a PDF, asking grounded questions, inspecting retrieved evidence,
and viewing citation audit verdicts directly in the terminal.
"""

import argparse
import sys
from pathlib import Path

from src.core.tutor_service import TutorService
from src.providers.mock_provider import MockDeterministicProvider
from src.providers.gemini_provider import GeminiProvider


def run_cli_demo(pdf_path_str: str, query: str, force_offline: bool = False):
    pdf_path = Path(pdf_path_str)
    if not pdf_path.exists():
        print(f"[Error] PDF file not found at: {pdf_path.resolve()}", file=sys.stderr)
        sys.exit(1)

    print("=" * 70)
    print("YOUR TUTOR — MILESTONE 1 GROUNDING ENGINE DEMONSTRATION")
    print("=" * 70)

    service = TutorService()
    if force_offline:
        service.set_provider(MockDeterministicProvider())
    elif not service.provider.is_available():
        print("[Notice] GEMINI_API_KEY not configured. Running with Offline Deterministic Provider.\n")

    print(f"[*] Ingesting PDF: {pdf_path.name} ({pdf_path.stat().st_size} bytes)...")
    doc = service.ingest_pdf(pdf_path)
    print(f"[+] Successfully ingested: {doc.filename}")
    print(f"    Document ID: {doc.document_id}")
    print(f"    Total Pages: {doc.total_pages}")
    print(f"    Chunks Indexed: {len(service.retriever.chunks)}\n")

    print(f"[*] Submitting Question: \"{query}\"\n")
    response = service.answer_question(query)

    print("-" * 70)
    print("TUTOR INSTRUCTIONAL RESPONSE")
    print("-" * 70)
    print(response.answer)
    print()

    print("-" * 70)
    print("PROVENANCE & AUDIT REPORT")
    print("-" * 70)
    print(f"Provider:        {response.provider_name} (Mode: {response.mode})")
    print(f"Refusal State:   {'Refused (Insufficient Evidence)' if response.is_refusal else 'Answered'}")
    print(f"Audit Passed:    {'YES (Verified)' if response.audit_passed else 'NO (Failed / Unverified)'}")
    print(f"Audit Details:   {response.audit_result.details}")
    print(f"Valid Citations: {response.audit_result.valid_citations}")
    if response.audit_result.invalid_citations:
        print(f"Invalid Citations: {response.audit_result.invalid_citations}")
    print()

    print("-" * 70)
    print(f"RETRIEVED COURSE EVIDENCE ({len(response.retrieved_evidence)} chunks)")
    print("-" * 70)
    if not response.retrieved_evidence:
        print("  (None retrieved — query scored below relevance threshold)")
    else:
        for item in response.retrieved_evidence:
            print(f"  [Rank #{item.rank} | Score: {item.score:.3f} | {item.citation_label}]")
            preview = item.text_content[:180] + ("..." if len(item.text_content) > 180 else "")
            print(f"  Excerpt: \"{preview}\"\n")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Your Tutor Milestone 1 CLI Demonstration")
    parser.add_argument(
        "--pdf",
        type=str,
        default="tests/fixtures/synthetic_ml_notes.pdf",
        help="Path to PDF course material",
    )
    parser.add_argument(
        "--query",
        type=str,
        default="What is backpropagation and how is the chain rule applied?",
        help="Question to ask the tutor",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Force offline mock provider regardless of API key availability",
    )
    args = parser.parse_args()
    run_cli_demo(args.pdf, args.query, args.offline)


if __name__ == "__main__":
    main()
