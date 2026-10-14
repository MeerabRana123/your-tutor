"""Streamlit Web Application for Your Tutor — Grounded Adaptive Tutoring MVP.

Demonstrates:
1. Multimodal PDF Ingestion with page-level provenance
2. Grounded Q&A with independent citation auditing
3. Adaptive Multiple-Choice Assessments with deterministic answer evaluation
4. Real-time Bayesian Knowledge Tracing (BKT) topic mastery tracking
5. Grounded revision recommendations for incorrect responses
6. Reproducible evaluation benchmark reporting
"""

import os
from pathlib import Path
import streamlit as st

from src.core.tutor_service import TutorService
from src.providers.mock_provider import MockDeterministicProvider
from src.providers.gemini_provider import GeminiProvider
from eval.benchmark import run_benchmark


st.set_page_config(
    page_title="Your Tutor — Adaptive Learning Companion",
    page_icon="🎓",
    layout="wide",
)

# Persistent session state initialization
if "tutor_service" not in st.session_state:
    st.session_state.tutor_service = TutorService()
    st.session_state.active_doc_name = None
    st.session_state.last_response = None
    st.session_state.current_question = None
    st.session_state.last_assessment_result = None
    st.session_state.student_id = "student_demo"

service: TutorService = st.session_state.tutor_service

st.title("🎓 Your Tutor — Adaptive Learning Companion")
st.caption("Multimodal AI Hackathon 2026 — Track D: Personalized Tutoring & Adaptive Learning")

# -----------------------------------------------------------------------------
# SIDEBAR: Ingestion, Configuration, and Student Profile
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration & Ingestion")

    # Student Profile
    student_id = st.text_input("Active Student ID:", value=st.session_state.student_id)
    st.session_state.student_id = student_id

    # Gemini API Key configuration
    st.subheader("🔑 Gemini API Key")
    current_key = os.getenv("GEMINI_API_KEY", "")
    gemini_key_input = st.text_input(
        "Enter GEMINI_API_KEY (Optional):",
        type="password",
        value=st.session_state.get("user_gemini_key", current_key),
        help="Optional: paste your Gemini API key to activate live generative Q&A and dynamic question creation. If blank, the app runs in 100% offline deterministic mode.",
    )
    if gemini_key_input:
        st.session_state.user_gemini_key = gemini_key_input.strip()
        os.environ["GEMINI_API_KEY"] = gemini_key_input.strip()

    # Model Provider Selection
    active_key = st.session_state.get("user_gemini_key") or os.getenv("GEMINI_API_KEY")
    gemini_provider_candidate = GeminiProvider(api_key=active_key)
    gemini_avail = gemini_provider_candidate.is_available()

    provider_choice = st.radio(
        "Model Provider:",
        options=["Offline Deterministic Engine", "Google Gemini (Live)"],
        index=1 if gemini_avail else 0,
        help="Offline mode uses template grounding and zero external API keys.",
    )

    if provider_choice == "Google Gemini (Live)":
        if gemini_avail:
            service.set_provider(gemini_provider_candidate)
            st.success("🟢 Live Gemini Provider Active")
        else:
            st.warning("⚠️ No valid GEMINI_API_KEY detected. Running in Offline Mode.")
            service.set_provider(MockDeterministicProvider())
    else:
        service.set_provider(MockDeterministicProvider())
        st.info("ℹ️ Offline Deterministic Engine Active")

    st.divider()

    # Document Ingestion
    st.subheader("📄 Course Ingestion")
    sample_pdf_path = Path("tests/fixtures/synthetic_ml_notes.pdf")
    uploaded_file = st.file_uploader("Upload Course Material (PDF):", type=["pdf"])

    use_sample = False
    if sample_pdf_path.exists():
        use_sample = st.checkbox("Use Synthetic ML Notes Fixture", value=True)

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
                with st.spinner(f"Extracting page-aware chunks from {target_path.name}..."):
                    doc = service.ingest_pdf(target_path)
                    st.session_state.active_doc_name = doc.filename
                    st.success(f"✅ Ingested '{doc.filename}' ({doc.total_pages} pages, {len(service.retriever.chunks)} chunks)")
            else:
                st.error("Please upload a PDF or select the synthetic fixture.")
        except Exception as e:
            st.error(f"Ingestion failed: {e}")

    # Active Corpus Stats
    if st.session_state.active_doc_name:
        st.divider()
        st.write(f"**Indexed Document:** `{st.session_state.active_doc_name}`")
        st.write(f"**Chunks in Index:** `{len(service.retriever.chunks)}`")

# -----------------------------------------------------------------------------
# MAIN APP TABS
# -----------------------------------------------------------------------------
tab_qa, tab_practice, tab_eval = st.tabs([
    "💬 Grounded Tutor Q&A",
    "🎯 Adaptive Practice & BKT Mastery",
    "📊 Evaluation Benchmark",
])

# =============================================================================
# TAB 1: Grounded Tutor Q&A
# =============================================================================
with tab_qa:
    st.subheader("💬 Ask Your Course Materials")
    st.write(
        "Questions are answered strictly from retrieved course excerpts with page-level citations. "
        "Out-of-domain questions are safely refused."
    )

    sample_queries = [
        "What is backpropagation and how does the chain rule apply?",
        "Explain the three variants of gradient descent.",
        "What is overfitting and how does L2 regularization combat it?",
        "What is the difference between a loss function and a cost function?",
        "What temperature is required to bake a sourdough loaf in a Dutch oven?",  # Refusal demo
    ]

    selected_sample = st.selectbox(
        "💡 Preset Evaluation Shortcuts (Select one to load, or leave blank to write your own):",
        [""] + sample_queries,
        help="These presets are quick shortcuts for evaluation. You can also type any custom question below!",
    )

    st.caption("💡 **Note:** The dropdown above contains quick evaluation presets. You can also type **any arbitrary question** in the input field below to test dynamic BM25 retrieval against any uploaded document!")

    user_query = st.text_input(
        "Enter your question (Arbitrary custom queries supported):",
        value=selected_sample if selected_sample else "",
        placeholder="e.g., How does learning rate alpha govern gradient descent updates?",
    )

    if st.button("Submit Question", type="primary"):
        if not user_query.strip():
            st.warning("Please enter a question.")
        elif len(service.retriever.chunks) == 0:
            st.error("No course materials indexed yet. Please ingest a PDF from the sidebar first.")
        else:
            with st.spinner("Retrieving evidence and verifying citations..."):
                resp = service.answer_question(user_query)
                st.session_state.last_response = resp

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

        st.markdown("### 📝 Grounded Response")
        if resp.is_refusal:
            st.warning(resp.answer)
        elif not resp.audit_passed:
            st.error(resp.answer)
        else:
            st.info(resp.answer)

        # Audit Inspector
        with st.expander("🔍 Citation Audit Details", expanded=True):
            st.write(f"**Audit Verdict:** {resp.audit_result.details}")
            if resp.audit_result.valid_citations:
                st.write(f"**Verified Citations:** `{resp.audit_result.valid_citations}`")
            if resp.audit_result.invalid_citations:
                st.error(f"**Unverified Citations:** `{resp.audit_result.invalid_citations}`")
            if resp.audit_result.unsupported_claims:
                st.warning(f"**Low-Overlap Claims:** `{resp.audit_result.unsupported_claims}`")

        # Evidence Chunks
        with st.expander(f"📚 Retrieved Course Evidence ({len(resp.retrieved_evidence)} chunks)", expanded=True):
            if not resp.retrieved_evidence:
                st.write("*(No chunks met relevance threshold — query safely refused)*")
            else:
                for item in resp.retrieved_evidence:
                    st.markdown(
                        f"**Rank #{item.rank}** | Relevance Score: `{item.score:.3f}` | "
                        f"**Citation:** `{item.citation_label}`"
                    )
                    st.code(item.text_content, language="text")
                    st.divider()

# =============================================================================
# TAB 2: Adaptive Practice & BKT Mastery
# =============================================================================
with tab_practice:
    st.subheader("🎯 Adaptive Practice & Knowledge Tracing (BKT)")
    st.write(
        "Practice Multiple-Choice Questions generated from indexed course text. "
        "Your mastery $P(L)$ updates in real-time using standard **Corbett & Anderson (1994) Bayesian Knowledge Tracing**."
    )

    # Topic Selection
    available_topics = [
        "Loss and Cost Functions",
        "Gradient Descent Optimization",
        "Backpropagation and the Chain Rule",
        "Overfitting and Regularization",
    ]

    practice_mode = st.radio(
        "Practice Topic Mode:",
        options=["Core Curriculum Presets", "Custom Topic / Document Search"],
        horizontal=True,
        help="Select a standard syllabus topic or enter any concept from your uploaded PDF.",
    )

    col_top1, col_top2 = st.columns([2, 1])
    with col_top1:
        if practice_mode == "Core Curriculum Presets":
            chosen_topic = st.selectbox("Select Curriculum Topic:", available_topics)
        else:
            chosen_topic = st.text_input(
                "Enter Concept or Search Term from Material:",
                value="",
                placeholder="e.g., Stochastic Gradient Descent, Dropout, Chain Rule...",
            )
    with col_top2:
        st.write("")
        st.write("")
        if st.button("🎲 Generate Practice Item", use_container_width=True):
            if len(service.retriever.chunks) == 0:
                st.error("Please ingest course materials from the sidebar first.")
            else:
                try:
                    topic_arg = chosen_topic.strip() if chosen_topic else None
                    q = service.generate_assessment(topic_hint=topic_arg)
                    st.session_state.current_question = q
                    st.session_state.last_assessment_result = None
                except Exception as e:
                    st.error(f"Could not generate question: {e}")

    # Active Assessment Item
    if st.session_state.current_question:
        q = st.session_state.current_question
        st.markdown(f"#### Question ({q.topic})")
        st.caption(f"**Source Origin:** `{q.citation_label}` | **Generator Mode:** `{q.generator_mode}`")
        st.markdown(f"**{q.question_stem}**")

        # Radio options with dynamic key so selection resets cleanly on new question
        option_labels = [f"{k}: {v}" for k, v in q.options.items()]
        selected_option = st.radio(
            "Choose your answer:",
            option_labels,
            key=f"practice_radio_{q.question_id}",
        )

        if st.button("Submit Answer", type="primary"):
            choice_key = selected_option.split(":")[0].strip()
            result = service.submit_assessment(
                student_id=st.session_state.student_id,
                question=q,
                student_choice=choice_key,
            )
            st.session_state.last_assessment_result = result

    # Display Assessment Feedback and Mastery Delta
    if st.session_state.last_assessment_result:
        res = st.session_state.last_assessment_result
        st.divider()

        if res.is_correct:
            st.success(f"🎉 **Correct!** (Answer: {res.correct_answer})")
        else:
            st.error(f"❌ **Incorrect.** (You selected {res.student_choice}; Correct answer is {res.correct_answer})")

        st.markdown(f"**Explanation:** {res.explanation}")
        st.caption(f"**Verified Citation:** `{res.citation_label}`")

        # BKT Mastery Update
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.metric("Prior Mastery P(L_t-1)", f"{res.prior_mastery:.2f}")
        with m_col2:
            st.metric("Posterior Mastery P(L_t)", f"{res.posterior_mastery:.2f}", delta=f"{res.mastery_delta:+.2f}")
        with m_col3:
            st.metric("Curriculum Status", "Proficient" if res.posterior_mastery >= 0.70 else "Needs Review")

        # Grounded Revision Recommendation
        if res.revision_recommendation:
            st.warning(f"📌 **{res.revision_recommendation}**")

    # Current Student Mastery Dashboard
    st.divider()
    st.subheader(f"📈 Learner Mastery Dashboard ({st.session_state.student_id})")
    masteries = service.get_student_masteries(st.session_state.student_id)

    if not masteries:
        st.info("No practice attempts recorded yet for this student. Submit an answer above to establish your BKT baseline!")
    else:
        for topic_name, p_val in masteries.items():
            t_col1, t_col2 = st.columns([3, 1])
            with t_col1:
                st.write(f"**{topic_name}**")
                st.progress(p_val)
            with t_col2:
                st.metric("BKT Mastery P(L)", f"{p_val:.1%}")

    with st.expander("ℹ️ About Bayesian Knowledge Tracing (BKT)"):
        st.markdown(
            "**Formula:** Corbett & Anderson (1994) standard closed-form posterior updating:\n"
            "- Correct response: $P(L_t \\mid obs=1) = \\frac{P(L_{t-1}) (1 - P(S))}{P(L_{t-1}) (1 - P(S)) + (1 - P(L_{t-1})) P(G)}$\n"
            "- Learning transition: $P(L_{t+1}) = P(L_t) + (1 - P(L_t)) P(T)$\n\n"
            "**Pedagogical Note:** Mastery values are probabilistic estimates of latent proficiency over practice items, "
            "not certified measurements of human competence."
        )

# =============================================================================
# TAB 3: Evaluation Benchmark
# =============================================================================
with tab_eval:
    st.subheader("📊 Reproducible Evaluation Benchmark")
    st.write(
        "Runs an 8-item ground truth test suite (4 in-domain technical questions and 4 out-of-domain queries). "
        "Calculates real, unmanipulated retrieval precision, citation audit rates, and refusal accuracy."
    )

    if st.button("▶️ Execute Benchmark Suite", type="primary"):
        with st.spinner("Running 8 benchmark evaluations..."):
            rep = run_benchmark()
            summary = rep["benchmark_summary"]

            b_col1, b_col2, b_col3, b_col4 = st.columns(4)
            with b_col1:
                st.metric("Retrieval Precision@1", f"{summary['in_domain_retrieval_precision_at_1'] * 100:.1f}%")
            with b_col2:
                st.metric("Citation Audit Rate", f"{summary['in_domain_citation_audit_pass_rate'] * 100:.1f}%")
            with b_col3:
                st.metric("Refusal Accuracy", f"{summary['out_of_domain_refusal_rate'] * 100:.1f}%")
            with b_col4:
                st.metric("Overall Accuracy", f"{summary['overall_accuracy'] * 100:.1f}%")

            st.markdown("### Itemized Evaluation Log")
            st.dataframe(rep["item_results"], use_container_width=True)
            st.success("✅ Benchmark execution complete. Bit-for-bit reproducible.")
