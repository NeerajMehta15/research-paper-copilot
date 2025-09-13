import streamlit as st

# ---------- Page Config ----------
st.set_page_config(page_title="Research Paper Copilot", layout="wide")

# ---------- Custom CSS ----------
st.markdown("""
<style>
body {
    background-color: #fafafa;
}
.section-header {
    font-size: 1.2rem !important;
    margin-top: 1.5rem;
    border-bottom: 1px solid #ddd;
    padding-bottom: 0.3rem;
}
.paper-card {
    background: white;
    padding: 0.7rem 1rem;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    margin-bottom: 0.6rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.recent-chip button {
    border-radius: 16px !important;
    background-color: #f0f0f0 !important;
    border: none !important;
    color: #333 !important;
    padding: 0.3rem 0.8rem !important;
    margin: 0.2rem !important;
    font-size: 0.85rem !important;
}
.recent-chip button:hover {
    background-color: #e0e0e0 !important;
}
.mode-badge {
    display: inline-block;
    background: #e3edfa;
    color: #1a4a8d;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.85rem;
    margin-bottom: 0.5rem;
}
.empty-state {
    text-align: center;
    padding: 3rem;
    color: #555;
}
</style>
""", unsafe_allow_html=True)

# ---------- Session State ----------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "recent_questions" not in st.session_state:
    st.session_state.recent_questions = []
if "papers" not in st.session_state:
    st.session_state.papers = []  # store mock info like {"title":..., "abstract":..., "pages":...}

# ---------- Sidebar ----------
with st.sidebar:
    st.title("📚 Research Paper Copilot")
    st.caption("Upload papers or explore from our sample collection.")

    uploaded_pdfs = st.file_uploader(
        "Upload Research Papers",
        type=["pdf"],
        accept_multiple_files=True
    )

    # Mock adding them to library
    if uploaded_pdfs:
        for pdf in uploaded_pdfs:
            st.session_state.papers.append({
                "title": pdf.name.replace(".pdf",""),
                "pages": 12,
                "abstract": "Lorem ipsum abstract placeholder for this uploaded paper."
            })

    st.markdown("<div class='section-header'>Common Papers</div>", unsafe_allow_html=True)
    common_papers = [
        "Attention Is All You Need",
        "BERT: Pre-training of Deep Bidirectional Transformers",
        "Large Language Models are Zero-Shot Learners"
    ]
    selected_common = st.multiselect("Select demo papers", common_papers)
    for paper in selected_common:
        if paper not in [p["title"] for p in st.session_state.papers]:
            st.session_state.papers.append({
                "title": paper,
                "pages": 8,
                "abstract": "This is a sample abstract for the demo paper."
            })

    st.markdown("<div class='section-header'>Mode</div>", unsafe_allow_html=True)
    mode = st.radio("", ["Normal Q&A", "Compare Papers", "Simplify Explanation"])

# ---------- Main Layout ----------
left, right = st.columns([2, 1], gap="large")

# ---------- Chat Section ----------
with left:
    st.title("💬 Chat with Your Papers")

    # Mode badge
    st.markdown(f"<span class='mode-badge'>Mode: {mode}</span>", unsafe_allow_html=True)

    # Empty state if no papers
    if not st.session_state.papers:
        st.markdown("""
        <div class='empty-state'>
            <h3>📥 Get Started</h3>
            <p>Upload your research PDFs from the sidebar or select from our demo papers.</p>
            <p>Then, start asking questions like:</p>
            <ul>
                <li>What is the main contribution of this paper?</li>
                <li>Summarize section 3 in simple terms</li>
                <li>Compare paper A and paper B</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Display chat history
        for role, message, citations in st.session_state.chat_history:
            with st.chat_message("user" if role == "user" else "assistant"):
                st.markdown(message)
                if role == "assistant" and citations:
                    st.caption("📎 Sources: " + ", ".join([f"{c['title']} (p.{c['page']})" for c in citations]))

        # Dynamic placeholder based on mode
        placeholder = {
            "Normal Q&A": "Ask a question about your papers...",
            "Compare Papers": "Ask how two papers differ...",
            "Simplify Explanation": "Paste something to simplify..."
        }[mode]

        user_query = st.chat_input(placeholder)
        if user_query:
            # Append to history (mock citations)
            st.session_state.chat_history.append(("user", user_query, None))
            st.session_state.chat_history.append((
                "assistant",
                "_(Pending answer from model...)_",
                [{"title": "Attention Is All You Need", "page": 3}]
            ))
            st.session_state.recent_questions.append(user_query)
            st.rerun()

# ---------- Right Panel ----------
with right:
    # Paper Library
    st.markdown("### 📑 Paper Library")
    if st.session_state.papers:
        for paper in st.session_state.papers:
            with st.container():
                st.markdown(f"""
                <div class='paper-card'>
                    <strong>{paper['title']}</strong><br>
                    <small>{paper['pages']} pages</small>
                    <p style='font-size:0.85rem; color:#555;'>{paper['abstract']}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No papers loaded yet.")

    # Recent Questions
    st.markdown("### 🕒 Recent Questions")
    if st.session_state.recent_questions:
        cols = st.columns(2)
        for i, q in enumerate(reversed(st.session_state.recent_questions[-8:])):
            with cols[i % 2]:
                if st.button(q, key=f"recent_{i}", use_container_width=True):
                    # Instead of auto-submit, pre-fill as next user query
                    st.session_state.prefill = q
                    st.rerun()
    else:
        st.info("Ask something to see it appear here.")
