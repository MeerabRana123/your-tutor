"""Minimal Streamlit Application for Your Tutor — Milestone 1.

Demonstrates PDF ingestion, page-aware retrieval, grounded instructional responses,
and independent citation auditing.
"""

from pathlib import Path
import streamlit as st

from src.core.tutor_service import TutorService
from src.providers.mock_provider import MockDeterministicProvider
from src.providers.gemini_provider import GeminiProvider


st.set_page_config(
    page_title="Your Tutor — Grounding Engine",
    page_icon="🎓",
    layout="wide",
)

# Initialize TutorService in Streamlit session state
if "tutor_service" not in st.session_state:
    st.session_state.tutor_service = TutorService()
    st.session_state.active_doc_name = None
    st.session_state.last_response = None

service: TutorService = st.session_state.tutor_service

st.title("🎓 Your Tutor — Grounding Engine (Milestone 1)")
st.caption("Multimodal AI Hackathon 2026 — Track D: Personalized Tutoring & Adaptive Learning")

# Sidebar: Ingestion and Configuration
with st.sidebar:
    st.header("📂 Course Material Ingestion")

    # Provider status
    gemini_avail = GeminiProvider().is_available()
    provider_choice = st.radio(
        "Model Provider:",
        options=["Offline Deterministic Engine", "Google Gemini"],
        index=1 if gemini_avail else 0,
        help="Offline mode requires zero API keys and works deterministically.",
    )

    if provider_choice == "Google Gemini":
        if gemini_avail:
            service.set_provider(GeminiProvider())
            st.success("🟢 Gemini Provider Active")
        else:
            st.warning("⚠️ GEMINI_API_KEY not found. Defaulting to Offline Mode.")
            service.set_provider(MockDeterministicProvider())
    else:
        service.set_provider(MockDeterministicProvider())
        st.info("ℹ️ Offline Deterministic Engine Active")

    st.divider()

    # Source file selection
    sample_pdf_path = Path("tests/fixtures/synthetic_ml_notes.pdf")
    uploaded_file = st.file_uploader("Upload Course PDF", type=["pdf"])

    use_sample = False
    if sample_pdf_path.exists():
        use_sample = st.checkbox("Or use Synthetic ML Notes fixture", value=True)

    if st.button("🚀 Ingest Document", type="primary", use_container_width=True):
        try:
            target_path = None
            if uploaded_file is not None:
                save_dir = Path("data/uploads")
                save_dir.mkdir(parents=True, exist_ok=True)
                target_path = save_dir / uploaded_file.name
                target_path.write_bytes(uploaded_file.getbuffer())
            elif use_sample and sample_pdf_path.exists():
                target_path = sample_pdf_path

            if target_path:
                with st.spinner(f"Extracting and indexing {target_path.name}..."):
                    doc = service.ingest_pdf(target_path)
                    st.session_state.active_doc_name = doc.filename
                    st.success(f"Ingested '{doc.filename}' ({doc.total_pages} pages, {len(service.retriever.chunks)} chunks)")
            else:
                st.error("Please upload a PDF or check the synthetic fixture.")
        except Exception as e:
            st.error(f"Ingestion failed: {e}")

    # Active corpus stats
    if st.session_state.active_doc_name:
        st.divider()
        st.write(f"**Active Document:** `{st.session_state.active_doc_name}`")
        st.write(f"**Indexed Chunks:** `{len(service.retriever.chunks)}`")

# Main Interface: Question Answering
st.subheader("💬 Grounded Tutor Q&A")

sample_queries = [
    "What is backpropagation and how does the chain rule apply?",
    "Explain the three variants of gradient descent.",
    "What is overfitting and how does L2 regularization combat it?",
    "How do I bake a sourdough loaf in a Dutch oven?",  # Out of domain query
]

selected_sample = st.selectbox("Quick Sample Questions:", [""] + sample_queries)
user_query = st.text_input(
    "Ask a question based on your course materials:",
    value=selected_sample if selected_sample else "",
    placeholder="e.g., Explain the parameter update equation for gradient descent.",
)

if st.button("Submit Question", type="primary"):
    if not user_query.strip():
        st.warning("Please enter a question.")
    elif len(service.retriever.chunks) == 0:
        st.error("No course materials indexed yet. Please ingest a PDF from the sidebar first.")
    else:
        with st.spinner("Retrieving evidence and synthesizing grounded response..."):
            resp = service.answer_question(user_query)
            st.session_state.last_response = resp

# Display Results
if st.session_state.last_response:
    resp = st.session_state.last_response

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Provider", resp.provider_name)
    with col2:
        st.metric("Mode", resp.mode)
    with col3:
        if resp.audit_passed:
            st.metric("Citation Audit", "PASSED ✅")
        else:
            st.metric("Citation Audit", "FAILED ❌")

    st.markdown("### 📝 Tutor Response")
    st.info(resp.answer)

    # Provenance and Audit Details
    with st.expander("🔍 Citation Audit Inspector", expanded=True):
        st.write(f"**Audit Verdict:** {resp.audit_result.details}")
        if resp.audit_result.valid_citations:
            st.write(f"**Verified Citations:** `{resp.audit_result.valid_citations}`")
        if resp.audit_result.invalid_citations:
            st.error(f"**Invalid Citations Detected:** `{resp.audit_result.invalid_citations}`")
        if resp.audit_result.unsupported_claims:
            st.warning(f"**Low-Overlap Claims Flagged:** `{resp.audit_result.unsupported_claims}`")

    # Retrieved Evidence Items
    with st.expander(f"📚 Retrieved Evidence Chunks ({len(resp.retrieved_evidence)})", expanded=True):
        if not resp.retrieved_evidence:
            st.write("*(No chunks retrieved above relevance threshold)*")
        else:
            for item in resp.retrieved_evidence:
                st.markdown(
                    f"**Rank #{item.rank}** | Relevance Score: `{item.score:.3f}` | "
                    f"**Citation:** `{item.citation_label}`"
                )
                st.code(item.text_content, language="text")
                st.divider()
