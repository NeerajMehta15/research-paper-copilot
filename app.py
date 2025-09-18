# app.py
import streamlit as st
import tempfile
import os
from pathlib import Path
from backend.ingest import process_file
from backend.embeddings import EmbeddingManager
from backend.rag_pipelines import answer_question_with_citations

# Page configuration
st.set_page_config(
    page_title="Research Paper Copilot",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Research Paper Copilot")
st.markdown("Upload research papers and ask questions with accurate citations!")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processed_files" not in st.session_state:
    st.session_state.processed_files = []
if "embedding_manager" not in st.session_state:
    st.session_state.embedding_manager = EmbeddingManager()

# Sidebar for file upload and settings
with st.sidebar:
    st.header("📤 Upload Papers")
    
    uploaded_files = st.file_uploader(
        "Choose PDF files", 
        type="pdf", 
        accept_multiple_files=True,
        help="Upload research papers, reports, or any PDF documents"
    )
    
    # Mode selector
    st.header("🔧 Settings")
    mode = st.selectbox(
        "Query Mode", 
        ["normal", "compare", "simplify"],
        help="Normal: Standard Q&A | Compare: Cross-paper analysis | Simplify: Plain language explanations"
    )
    
    # Display processed files
    st.header("📚 Processed Papers")
    if st.session_state.processed_files:
        for filename in st.session_state.processed_files:
            st.text(f"✅ {filename}")
    else:
        st.text("No papers uploaded yet")
    
    # Process uploaded files
    if uploaded_files:
        if st.button("🚀 Process Papers", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, uploaded_file in enumerate(uploaded_files):
                if uploaded_file.name not in st.session_state.processed_files:
                    try:
                        status_text.text(f"Processing {uploaded_file.name}...")
                        
                        # Save uploaded file temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_path = tmp_file.name
                        
                        # Process file through your pipeline
                        processed_doc = process_file(tmp_path)
                        doc_id = st.session_state.embedding_manager.add_document(processed_doc)
                        
                        if doc_id:
                            st.session_state.processed_files.append(uploaded_file.name)
                            st.success(f"✅ Processed: {uploaded_file.name}")
                        else:
                            st.error(f"❌ Failed to process: {uploaded_file.name}")
                        
                        # Cleanup
                        os.unlink(tmp_path)
                        
                    except Exception as e:
                        st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            status_text.text("Processing complete!")
            st.rerun()

# Main content area
col1, col2 = st.columns([3, 1])

with col1:
    st.header("💬 Chat with Your Papers")
    
    # Display chat messages
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Display citations for assistant messages
                if message["role"] == "assistant" and "citations" in message:
                    if message["citations"]:
                        st.markdown("**Sources:**")
                        for source, reference in message["citations"].items():
                            st.markdown(f"- **{source}**: {reference}")

with col2:
    st.header("📊 Query Info")
    if st.session_state.messages:
        last_message = st.session_state.messages[-1]
        if last_message["role"] == "assistant" and "metadata" in last_message:
            metadata = last_message["metadata"]
            st.metric("Sources Found", metadata.get("sources_count", 0))
            st.metric("Citations Used", len(metadata.get("citations_used", [])))
            
            confidence = metadata.get("confidence", "unknown")
            confidence_color = {
                "high": "🟢",
                "medium": "🟡", 
                "low": "🟠",
                "error": "🔴"
            }.get(confidence, "⚪")
            
            st.markdown(f"**Confidence:** {confidence_color} {confidence.title()}")

# Chat input
if st.session_state.processed_files:
    if prompt := st.chat_input("Ask about your papers..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Searching papers and generating answer..."):
                try:
                    result = answer_question_with_citations(prompt, mode=mode)
                    
                    # Display answer
                    st.markdown(result['answer'])
                    
                    # Display citations if available
                    if result['has_citations'] and result['citation_map']:
                        st.markdown("**Sources:**")
                        for source, reference in result['citation_map'].items():
                            st.markdown(f"- **{source}**: {reference}")
                    elif not result['has_citations']:
                        st.warning("⚠️ Answer generated without citations. Consider refining your query.")
                    
                    # Store assistant response
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": result['answer'],
                        "citations": result['citation_map'],
                        "metadata": {
                            "sources_count": result.get('sources_count', 0),
                            "citations_used": result.get('citations_used', []),
                            "confidence": result.get('confidence', 'unknown')
                        }
                    })
                    
                except Exception as e:
                    error_msg = f"Error generating answer: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": error_msg,
                        "citations": {},
                        "metadata": {"confidence": "error"}
                    })
        
        st.rerun()
else:
    st.info("👆 Please upload and process some PDF files first to start asking questions!")

# Footer
st.markdown("---")
st.markdown("**Research Paper Copilot** - AI-powered document analysis with accurate citations")