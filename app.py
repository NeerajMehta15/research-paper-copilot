# app.py - minimal version
import streamlit as st
from backend.ingest import _extract_pdf

st.title("PDF Text Extractor")
uploaded_file = st.file_uploader("Choose a PDF", type="pdf")

if uploaded_file:
    # Save temporarily and extract
    text = _extract_pdf(uploaded_file)
    st.write(text)